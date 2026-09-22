#!/usr/bin/env python3
"""
compare.py: score how different LLM models perform on the cell-design task.

Reads one or more manifests produced by propose.py (each tagged with the model
that generated it, via the `generator` field), re-measures every proposed design
against the shared baseline in the same ngspice bench, and tallies a per-model
scoreboard: how many designs were valid, how many were functional, how many
actually beat the part on EDP, and the best and median EDP gain.

The point mirrors the oracle: generation per model is separate and may be
nondeterministic, but this scorer is deterministic and reproducible, so a
model's standing is a public fact rather than a claim. A model only gets credit
for a win the ngspice measurement confirms.

Usage:
  compare.py candidates/model-*.json           # a glob of per-model manifests
  compare.py flash.json pro.json --out results
Produce the inputs with, e.g.:
  GEMINI_MODEL=gemini-2.5-flash ./run.sh propose --backend llm --out candidates/flash.json
  GEMINI_MODEL=gemini-2.5-pro   ./run.sh propose --backend llm --out candidates/pro.json
"""
import argparse
import glob
import json
import os
import statistics
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import candidate as C
from measure import measure, measure_many

EDP_MARGIN = 0.01


def load_manifests(patterns):
    files = []
    for p in patterns:
        files += glob.glob(p) or ([p] if os.path.exists(p) else [])
    mans = []
    for f in sorted(set(files)):
        with open(f) as fh:
            m = json.load(fh)
        m["_path"] = f
        mans.append(m)
    if not mans:
        sys.exit("no manifests matched: " + " ".join(patterns))
    return mans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+", help="per-model manifest json paths")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mans = load_manifests(a.manifests)

    # operating point + baseline come from the manifests; they must agree
    op = mans[0].get("operating_point", {})
    baseline = mans[0].get("baseline", "sky130_fd_sc_hd__buf_16")
    load = op.get("load", "250f")
    slew = op.get("slew", "0.05n")
    corner = op.get("corner", "tt")
    for m in mans[1:]:
        if m.get("baseline") != baseline or m.get("operating_point", {}) != op:
            print(f"warning: {m['_path']} has a different baseline/operating "
                  f"point; comparison assumes the first manifest's setup")

    base = measure(baseline, cl_farad=load, slew_s=slew, corner=corner)
    print(f"baseline {baseline} @ {load}: EDP={base['edp']:.2f} "
          f"tpd={base['tpd_ns']:.4f} E={base['energy_fj']:.1f}")

    # dedupe specs within each model; collect the global set to measure once
    all_specs, per_model = {}, {}
    for m in mans:
        model = m.get("generator", os.path.basename(m["_path"]))
        seen = set()
        for item in m.get("candidates", []):
            spec = item.get("spec")
            if not spec:
                continue
            h = C.design_hash(spec)
            if h in seen:
                continue
            seen.add(h)
            all_specs[h] = spec
            per_model.setdefault(model, []).append(h)

    # measure every unique proposed design once
    metrics = {}
    hashes = list(all_specs)
    with tempfile.TemporaryDirectory() as d:
        items = []
        for h in hashes:
            name = C.cell_name(all_specs[h])
            _, txt = C.emit_subckt(all_specs[h], name=name)
            p = os.path.join(d, name + ".spice")
            with open(p, "w") as fh:
                fh.write(txt)
            items.append({"cell": name, "lib_include": p, "_h": h})
        CHUNK = 16
        for i in range(0, len(items), CHUNK):
            chunk = items[i:i + CHUNK]
            res = measure_many(chunk, cl_farad=load, slew_s=slew, corner=corner)
            for it, mm in zip(chunk, res):
                metrics[it["_h"]] = mm
            print(f"  measured {min(i+CHUNK, len(items))}/{len(items)}")

    # score per model
    board = []
    for model, hs in per_model.items():
        ms = [metrics[h] for h in hs]
        functional = [x for x in ms if x["ok"]]
        gains = [(base["edp"] - x["edp"]) / base["edp"] * 100 for x in functional]
        winners = [g for g in gains if g >= EDP_MARGIN * 100]
        best = max(gains) if gains else None
        board.append({
            "model": model,
            "proposed": len(hs),
            "functional": len(functional),
            "winners": len(winners),
            "win_rate": round(len(winners) / len(hs), 3) if hs else 0,
            "best_gain_pct": round(best, 2) if best is not None else None,
            "median_gain_pct": round(statistics.median(gains), 2) if gains else None,
        })
    board.sort(key=lambda r: (r["best_gain_pct"] is None, -(r["best_gain_pct"] or 0)))

    report = {"baseline": baseline, "operating_point": op, "models": board}
    with open(os.path.join(a.out, "model_comparison.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    write_md(base, board, load, os.path.join(a.out, "model_comparison.md"))

    print("\nmodel scoreboard (best EDP gain vs the part):")
    for r in board:
        bg = f"{r['best_gain_pct']:+.1f}%" if r["best_gain_pct"] is not None else "n/a"
        print(f"  {r['model']:28s} proposed={r['proposed']:3d} "
              f"functional={r['functional']:3d} winners={r['winners']:3d} "
              f"best={bg}")


def write_md(base, board, load, path):
    b = base["cell"].replace("sky130_fd_sc_hd__", "")
    L = ["# LLM model comparison: designing a cell to beat `%s`" % b, "",
         "Each model proposed custom driver cells; every proposal was re-measured",
         "in the same ngspice bench against `%s` at a %s load. A win is a real"
         % (base["cell"], load),
         "EDP improvement the measurement confirms, so the ranking is reproducible.",
         "",
         "| model | proposed | functional | winners | best EDP gain | median gain |",
         "|---|---|---|---|---|---|"]
    for r in board:
        bg = "%+.1f%%" % r["best_gain_pct"] if r["best_gain_pct"] is not None else "n/a"
        mg = "%+.1f%%" % r["median_gain_pct"] if r["median_gain_pct"] is not None else "n/a"
        L.append("| %s | %d | %d | %d | %s | %s |"
                 % (r["model"], r["proposed"], r["functional"], r["winners"],
                    bg, mg))
    L += ["", "_Generation is per model and may be nondeterministic; this "
          "scoreboard is the deterministic scorer. A model is credited only for "
          "wins ngspice confirms._"]
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
