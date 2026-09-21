#!/usr/bin/env python3
"""
propose.py: the generation step (isolated from the oracle).

Produces candidate driver designs that try to beat a foundry part. Two backends:

  * grid: a deterministic device-layer sweep (stage count, taper, drive). No API,
    fully reproducible. Seeds the search and is what CI could regenerate.
  * llm:  an agent ("hey Gemini, beat this part") proposes designs via the Google
    Gemini API. Nondeterministic, run offline where an API key is fine. It emits
    the SAME spec schema; the oracle in assess.py judges it identically. Kept out
    of CI on purpose, so the judge stays independent of the generator.

The split is the whole point: generation can be as fancy or as cheap as you like
(free-tier flash here; point GEMINI_MODEL at a stronger model to raise the game),
while the public GitHub Actions oracle re-measures every proposal from scratch.

With --measure, candidates are pre-filtered locally in ngspice and only
functional, unique survivors are written to the manifest, so the committed set
that CI re-verifies is small and every row is real.
"""
import argparse
import itertools
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import candidate as C

# Devices actually loadable by the ngspice tt corner (see candidate.py). Gemini
# is constrained to these; anything else is sanitized to them so every proposal
# is measurable.
OK_NVT = {""}
OK_PVT = {"_hvt"}
M_MAX = 64


def grid_specs():
    """Device-layer sweep of non-inverting driver chains (unit-multiplicity)."""
    specs = []
    stage_counts = (2, 4)
    out_m = (8, 12, 16, 20, 24, 28, 32)   # output multiplicity; extends past 16
    tapers = (2.5, 3.0, 3.5, 4.0, 5.0)    # multiplicity ratio between stages
    for N, om, f in itertools.product(stage_counts, out_m, tapers):
        ms = [max(1, round(om / (f ** (N - 1 - k)))) for k in range(N)]
        if len(set(ms)) == 1 and N > 2:
            continue  # skip chains with no real taper
        stages = [{"m": m, "nvt": "", "pvt": "_hvt"} for m in ms]
        label = f"N{N}_out{om}_f{f:g}_" + "-".join(map(str, ms))
        specs.append({"spec": stages, "label": label})
    return specs


# ---------------------------------------------------------------- Gemini backend

def _prompt(baseline, load, n):
    part = baseline.replace("sky130_fd_sc_hd__", "")
    return f"""You are a custom digital standard-cell designer competing against a
semiconductor foundry. Design custom driver cells that beat the foundry part
`{part}` when driving a {load} load, on energy-delay product (EDP = energy x delay).

The cell is a chain of CMOS inverter stages. An EVEN number of stages makes it
non-inverting, matching a buffer. Each stage is `m` identical unit inverters in
parallel; `m` is the stage's drive strength. The unit inverter is one
nfet_01v8 (0.65um) + one pfet_01v8_hvt (1.0um): these are the ONLY two devices
available, the same ones the foundry buffers are built from.

Context: `{part}` is the largest buffer the sky130 HD library ships. It is a
fixed 2-stage design at drive strength 16. The foundry ladder stops at 16, but a
{load} load wants more drive, so there is room to win by using higher output
multiplicity and different stage counts / tapers than the ladder offers. More
speed costs area and energy, so balance them for EDP.

Return ONLY a JSON array of exactly {n} distinct designs, each:
  {{"label": "<short-name>", "spec": [{{"m": <int 1-{M_MAX}>, "nvt": "", "pvt": "_hvt"}}, ...]}}
Rules: spec has an EVEN number of stages (2, 4, or 6); m is an integer in
[1, {M_MAX}]; nvt is always "" and pvt is always "_hvt". Vary stage count,
output drive (~8 to 48), and taper. Aim the output stage well above 16.
No prose, no markdown fences, just the JSON array."""


def _coerce_json(text):
    """Pull a JSON array out of a model response (tolerate fences/prose)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def validate_specs(raw):
    """Sanitize model output into valid, measurable {label, spec} designs.

    Drops designs that can't be made non-inverting; clamps m; forces the only
    loadable devices. Forgiving on purpose, the oracle is the real gate.
    """
    if isinstance(raw, dict):
        raw = raw.get("candidates") or raw.get("designs") or []
    out = []
    for i, item in enumerate(raw or []):
        spec_in = item.get("spec") if isinstance(item, dict) else None
        if not isinstance(spec_in, list) or not spec_in:
            continue
        stages = []
        for s in spec_in:
            try:
                m = int(s.get("m"))
            except (TypeError, ValueError, AttributeError):
                m = 0
            if m < 1:
                continue
            stages.append({"m": min(m, M_MAX), "nvt": "", "pvt": "_hvt"})
        if len(stages) < 2 or len(stages) % 2 != 0:
            continue  # must be an even chain to be non-inverting
        label = "gemini_" + (str(item.get("label", "")).strip().replace(" ", "_")
                             [:24] or f"cand{i}")
        out.append({"spec": stages, "label": label})
    return out


def llm_specs(baseline, load, n):
    """Ask Gemini for n candidate designs. Needs GEMINI_API_KEY (free tier ok)."""
    try:
        from google import genai
    except ImportError:
        sys.exit("google-genai not installed. `pip install google-genai` and set "
                 "GEMINI_API_KEY (a free key from https://aistudio.google.com).")
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit("set GEMINI_API_KEY (free key from https://aistudio.google.com).")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=key)
    print(f"asking {model} for {n} designs to beat {baseline} @ {load} ...")
    resp = client.models.generate_content(
        model=model, contents=_prompt(baseline, load, n),
        config={"response_mime_type": "application/json", "temperature": 1.0})
    specs = validate_specs(_coerce_json(resp.text))
    print(f"{model} returned {len(specs)} valid designs")
    return specs


# ------------------------------------------------------------------------- main

def dedupe(specs):
    uniq, seen = [], set()
    for s in specs:
        h = C.design_hash(s["spec"])
        if h not in seen:
            seen.add(h)
            uniq.append(s)
    return uniq


def prefilter(uniq, a):
    from measure import measure, measure_many
    base = measure(a.baseline, cl_farad=a.load, slew_s=a.slew, corner=a.corner)
    print(f"baseline {a.baseline}: EDP={base['edp']:.2f} tpd={base['tpd_ns']:.4f} "
          f"E={base['energy_fj']:.1f} area={base['area_um']:.1f}")
    obj = ("area_um", "tpd_ns", "energy_fj")
    survivors = []
    CHUNK = 16
    with tempfile.TemporaryDirectory() as d:
        for i in range(0, len(uniq), CHUNK):
            batch = uniq[i:i + CHUNK]
            items = []
            for s in batch:
                name = C.cell_name(s["spec"])
                _, txt = C.emit_subckt(s["spec"], name=name)
                p = os.path.join(d, name + ".spice")
                with open(p, "w") as fh:
                    fh.write(txt)
                items.append({"cell": name, "lib_include": p})
            res = measure_many(items, cl_farad=a.load, slew_s=a.slew,
                               corner=a.corner)
            for s, m in zip(batch, res):
                win = m["ok"] and m["edp"] < base["edp"] * 0.99  # EDP win, >=1%
                dom = (m["ok"]
                       and all(m[k] <= base[k] * 1.0000001 for k in obj)
                       and any(m[k] < base[k] * 0.9999999 for k in obj))
                if win or dom:
                    s2 = dict(s)
                    s2["_edp"] = m["edp"]
                    survivors.append(s2)
            print(f"  measured {min(i+CHUNK, len(uniq))}/{len(uniq)} "
                  f"survivors={len(survivors)}")
    survivors.sort(key=lambda s: s["_edp"])
    survivors = survivors[:a.keep]
    for s in survivors:
        s.pop("_edp", None)
    print(f"kept {len(survivors)} candidate(s) that beat the part on EDP")
    return survivors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=("grid", "llm"), default="grid")
    ap.add_argument("--measure", action="store_true",
                    help="pre-filter locally; keep only candidates that win on EDP")
    ap.add_argument("--baseline", default="sky130_fd_sc_hd__buf_16")
    ap.add_argument("--load", default="250f")
    ap.add_argument("--slew", default="0.05n")
    ap.add_argument("--corner", default="tt")
    ap.add_argument("--n", type=int, default=30, help="llm: designs to request")
    ap.add_argument("--keep", type=int, default=24, help="max survivors to keep")
    ap.add_argument("--out", default="candidates/manifest.json")
    a = ap.parse_args()

    if a.backend == "llm":
        specs = llm_specs(a.baseline, a.load, a.n)
        gen = "gemini:" + os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    else:
        specs = grid_specs()
        gen = "grid"
    uniq = dedupe(specs)
    print(f"{len(uniq)} unique candidate designs")

    out = prefilter(uniq, a) if a.measure else uniq
    manifest = {
        "operating_point": {"load": a.load, "slew": a.slew, "corner": a.corner},
        "baseline": a.baseline,
        "generator": gen,   # e.g. "grid" or "gemini:gemini-2.5-flash" (for model comparison)
        "candidates": out,
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote {a.out} ({len(out)} designs, baseline={a.baseline} @ {a.load})")


if __name__ == "__main__":
    main()
