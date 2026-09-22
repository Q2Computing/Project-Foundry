#!/usr/bin/env python3
"""
threetier.py: build the honest energy-delay picture in three tiers.

  1. FOUNDRY SYSTEM   real sky130 buffer ladder (buf_1..16), measured. White.
  2. DIFFERENTIATED   custom cells built from real, characterized foundry
                      devices (svt/lvt/hvt flavors). Fabricable today. Coloured
                      green or red by how their EDP compares to their CLOSEST
                      foundry prefab (nearest point in the log tpd / log E plane),
                      not to a single reference part.
  3. HYPOTHESES       intermediate-Vt implants a mask set cannot build today.
                      Placed by the SPICE-calibrated model interpolating between
                      two MEASURED fabricable endpoints (g=0 svt/hvt, g=1 lvt/svt).
                      White question marks: predicted, awaiting distributed silicon.

All three tiers share one ngspice ruler (the same load, corner, bench). The
hypothesis tier is the only non-measured one and is marked as such everywhere.
Run inside the ngspice container: `python analysis/threetier.py`.
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import candidate as C           # noqa: E402
import measure as M            # noqa: E402

LOAD = "250f"

# --- tier 1: foundry buffer ladder ------------------------------------------
LADDER = [1, 2, 4, 6, 8, 12, 16]

# --- tier 2: differentiated fabricable cells (real flavors) -----------------
# g0 = nfet_svt + pfet_hvt (buf-unit style); g1 = nfet_lvt + pfet_svt (low-Vt).
# strong drivers (beat the top of the ladder) plus a couple of deliberately
# under-driven cells that land beside a mid-ladder prefab and should lose to it.
SIZINGS = [(8, 24), (11, 32), (13, 32), (16, 48), (4, 10)]
def spec_g0(m1, m2):
    return [{"m": m1, "nvt": "", "pvt": "_hvt"}, {"m": m2, "nvt": "", "pvt": "_hvt"}]
def spec_g1(m1, m2):
    return [{"m": m1, "nvt": "_lvt", "pvt": ""}, {"m": m2, "nvt": "_lvt", "pvt": ""}]

# Vt-differentiated fabricable parts get the low-Vt endpoint too.
VT_SIZINGS = [(13, 32), (16, 48)]

# --- model constants (kept in sync with codesign.py) ------------------------
KV = 0.189            # full-span speedup g0 -> g1
LEAK_RATIO = 162.9 / 2.285


def measure_cells():
    items = [{"cell": f"sky130_fd_sc_hd__buf_{n}", "lib_include": None} for n in LADDER]
    customs = []                # (label, spec, tier-kind)
    for m1, m2 in SIZINGS:
        customs.append((f"[{m1},{m2}]", spec_g0(m1, m2), "size"))
    for m1, m2 in VT_SIZINGS:
        customs.append((f"[{m1},{m2}] low-Vt", spec_g1(m1, m2), "vt"))

    lib_parts, specs = [], []
    for label, spec, kind in customs:
        name, txt = C.emit_subckt(spec)
        lib_parts.append(txt)
        specs.append((label, name, spec, kind))
    tmp = tempfile.NamedTemporaryFile("w", suffix=".spice", delete=False,
                                      dir=os.path.join(ROOT, "candidates")
                                      if os.path.isdir(os.path.join(ROOT, "candidates"))
                                      else None)
    tmp.write("\n".join(lib_parts) + "\n"); tmp.close()
    for label, name, spec, kind in specs:
        items.append({"cell": name, "lib_include": tmp.name, "_label": label,
                      "_kind": kind, "_spec": spec})

    res = M.measure_many([{k: v for k, v in it.items() if not k.startswith("_")}
                          for it in items], cl_farad=LOAD)
    os.unlink(tmp.name)
    for r, it in zip(res, items):
        r["_label"] = it.get("_label")
        r["_kind"] = it.get("_kind")
    return res


def main():
    res = measure_cells()
    foundry, customs = [], []
    for r in res:
        if not r["ok"]:
            continue
        pt = {"tpd": r["tpd_ns"], "E": r["energy_fj"], "edp": r["edp"]}
        if r["cell"].startswith("sky130_fd_sc_hd__buf_"):
            pt["label"] = "buf_" + r["cell"].split("_")[-1]
            foundry.append(pt)
        else:
            pt["label"] = r["_label"]
            pt["kind"] = r["_kind"]
            customs.append(pt)

    # nearest foundry prefab in normalised log plane -> colour by EDP vs it
    def nearest(pt):
        lt, le = math.log(pt["tpd"]), math.log(pt["E"])
        best, bd = None, 1e9
        for f in foundry:
            d = (math.log(f["tpd"]) - lt) ** 2 + (math.log(f["E"]) - le) ** 2
            if d < bd:
                bd, best = d, f
        return best
    for pt in customs:
        nf = nearest(pt)
        pt["nearest"] = nf["label"]
        pt["beats"] = pt["edp"] < nf["edp"]

    # hypothesis tier: interpolate g=0.5 between the two measured endpoints of a
    # sizing (g0 and its low-Vt g1). delay ~ (1 - KV*g); energy from the model.
    hyps = []
    by_label = {c["label"]: c for c in customs}
    for m1, m2 in VT_SIZINGS:
        a = by_label.get(f"[{m1},{m2}]")           # g0 measured
        b = by_label.get(f"[{m1},{m2}] low-Vt")    # g1 measured
        if not (a and b):
            continue
        g = 0.5
        # delay: g0 delay scaled by the model's (1 - KV*g) relative to full span
        tpd = a["tpd"] * (1 - KV * g)
        # dynamic energy barely moves with Vt; leak adds a little. Interpolate E.
        E = a["E"] + (b["E"] - a["E"]) * g
        hyps.append({"tpd": tpd, "E": E, "edp": tpd * E,
                     "label": f"[{m1},{m2}] g=0.5", "nearest": a["nearest"]})

    out = {"load": LOAD, "foundry": foundry, "custom": customs, "hypothesis": hyps}
    with open(os.path.join(HERE, "threetier.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"load {LOAD}\n\nTIER 1  foundry ladder (white):")
    for f in sorted(foundry, key=lambda p: p["tpd"]):
        print(f"  {f['label']:8s} tpd={f['tpd']:.4f}ns  E={f['E']:.0f}fJ  EDP={f['edp']:.1f}")
    print("\nTIER 2  differentiated fabricable (green beats nearest prefab, red loses):")
    for c in sorted(customs, key=lambda p: p["tpd"]):
        tag = "GREEN" if c["beats"] else "red"
        print(f"  {c['label']:16s} tpd={c['tpd']:.4f}ns E={c['E']:.0f}fJ EDP={c['edp']:.1f}"
              f"  vs {c['nearest']:6s} -> {tag}")
    print("\nTIER 3  hypotheses (white '?', predicted intermediate Vt):")
    for h in hyps:
        print(f"  {h['label']:16s} tpd={h['tpd']:.4f}ns E={h['E']:.0f}fJ EDP={h['edp']:.1f}")
    print("\nwrote analysis/threetier.json")


if __name__ == "__main__":
    main()
