#!/usr/bin/env python3
"""
propose.py -- the generation step (isolated from the oracle).

Produces candidate driver designs that try to beat a foundry part. Two backends:

  * grid  -- a deterministic device-layer sweep: stage count, taper ratio,
             output width, Vt flavor. Reproducible; needs no API. This is what
             seeds the search and what CI could regenerate.
  * llm   -- SEAM (not wired here): an external agent ("hey Gemini, beat this
             part") proposes specs as JSON. Hundreds of shots, nondeterministic,
             run offline where an API key is fine. It must emit the SAME spec
             schema; the oracle judges it identically. Kept out of CI on purpose
             -- the judge stays independent of the generator.

With --measure, candidates are pre-filtered locally in ngspice and only
functional, unique survivors are written to the manifest, so the committed set
that CI re-verifies is small and every row is real. Generation may fan out over
hundreds; only survivors are committed.
"""
import argparse
import itertools
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import candidate as C


def grid_specs():
    """Device-layer sweep of non-inverting driver chains (unit-multiplicity).

    Built from the SAME two devices the sky130 HD cells use -- nfet_01v8 (svt)
    and pfet_01v8_hvt -- so a win is "same transistors, arranged better", not a
    faster-device trick. The levers the fixed 2-stage ladder lacks: stage count,
    free taper, and drive strength PAST the ladder's drive-16 ceiling.
    (Vt-mixing is a phase-2 lever; the lvt device wrapper is not loaded by the
    ngspice tt corner here.)
    """
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=("grid", "llm"), default="grid")
    ap.add_argument("--measure", action="store_true",
                    help="pre-filter locally; keep functional+unique survivors")
    ap.add_argument("--baseline", default="sky130_fd_sc_hd__buf_16")
    ap.add_argument("--load", default="120f")
    ap.add_argument("--slew", default="0.05n")
    ap.add_argument("--corner", default="tt")
    ap.add_argument("--keep", type=int, default=24, help="max survivors to keep")
    ap.add_argument("--out", default="candidates/manifest.json")
    a = ap.parse_args()

    if a.backend == "llm":
        print("llm backend is a documented seam; provide specs via JSON on "
              "stdin matching candidate.py schema, then judge with assess.py.")
        sys.exit(2)

    specs = grid_specs()
    # dedupe by design hash
    uniq, seen = [], set()
    for s in specs:
        h = C.design_hash(s["spec"])
        if h not in seen:
            seen.add(h)
            uniq.append(s)
    print(f"generated {len(uniq)} unique candidate designs")

    if a.measure:
        from measure import measure, measure_many
        base = measure(a.baseline, cl_farad=a.load, slew_s=a.slew,
                       corner=a.corner)
        print(f"baseline {a.baseline}: EDP={base['edp']:.2f} "
              f"tpd={base['tpd_ns']:.4f} E={base['energy_fj']:.1f} "
              f"area={base['area_um']:.1f}")
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
                    dom = (m["ok"]
                           and all(m[k] <= base[k] * 1.0000001 for k in obj)
                           and any(m[k] < base[k] * 0.9999999 for k in obj))
                    if dom:
                        s2 = dict(s)
                        s2["_edp"] = m["edp"]
                        survivors.append(s2)
                print(f"  measured {min(i+CHUNK, len(uniq))}/{len(uniq)} "
                      f"survivors={len(survivors)}")
        survivors.sort(key=lambda s: s["_edp"])
        survivors = survivors[:a.keep]
        for s in survivors:
            s.pop("_edp", None)
        out = survivors
        print(f"kept {len(out)} dominating survivors")
    else:
        out = uniq

    manifest = {
        "operating_point": {"load": a.load, "slew": a.slew,
                            "corner": a.corner},
        "baseline": a.baseline,
        "candidates": out,
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote {a.out} ({len(out)} designs, baseline={a.baseline} @ {a.load})")


if __name__ == "__main__":
    main()
