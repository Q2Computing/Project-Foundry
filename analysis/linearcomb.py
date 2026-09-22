#!/usr/bin/env python3
"""
linearcomb.py: the disciplined test. Back to the drawing board.

The foundry high-density buffer ladder (buf_1 .. buf_16) is, in every cell,
nfet_01v8 (svt) + pfet_01v8_hvt (hvt): the library trades pfet rise-edge speed
for low leakage and density. Its cells span an energy-per-cycle band; a real
32/64-bit datapath lives INSIDE that band, it does not pay for over-driven cells
outside it.

So the only honest question: at the fixed unit finger width, inside the buf_1..16
energy band, does there exist a LINEAR COMBINATION of the PDK's real dopant masks
and gate areas that beats the ladder? A linear combination here is literal and
FABRICABLE today: a stage of m fingers with k of them on one Vt mask and m-k on
another, in parallel. No intermediate implant, no hypothesis: two masks that both
already exist, mixed by count. The dopant palette that loads in tt:
  nfet: svt, lvt        pfet: hvt, svt
The foundry uses (svt, hvt). The reachable swaps are pfet hvt->svt (the big
rise-edge knob) and nfet svt->lvt (the small, nearly-free fall-edge knob).

If no combination inside the band beats the ladder, the single-cell provenance
claim is empty and we go back to the drawing board. Run in the ngspice container:
`python analysis/linearcomb.py`.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import measure as M            # noqa: E402

LOAD = "250f"
NUNIT, PUNIT, LCH = "650000u", "1e+06u", "150000u"
NF = {"svt": "sky130_fd_pr__nfet_01v8", "lvt": "sky130_fd_pr__nfet_01v8_lvt"}
PF = {"hvt": "sky130_fd_pr__pfet_01v8_hvt", "svt": "sky130_fd_pr__pfet_01v8"}
LADDER = [1, 2, 4, 6, 8, 12, 16]


def blended_buffer(name, m1, m2, fn, fp):
    """2-stage non-inverting buffer, unit fingers, dopant BLEND by finger count.
    fn = fraction of nfet fingers on lvt; fp = fraction of pfet fingers on svt.
    The remaining fingers are the foundry masks (nfet svt, pfet hvt)."""
    lines = [f".subckt {name} A VGND VNB VPB VPWR X"]
    for i, (gin, gout, m) in enumerate([("A", "n1", m1), ("n1", "X", m2)]):
        knl = round(fn * m)          # lvt nfet fingers
        kps = round(fp * m)          # svt pfet fingers
        for j in range(m):
            nmodel = NF["lvt"] if j < knl else NF["svt"]
            pmodel = PF["svt"] if j < kps else PF["hvt"]
            lines.append(f"XN{i}_{j} VGND {gin} {gout} VNB {nmodel} w={NUNIT} l={LCH}")
            lines.append(f"XP{i}_{j} VPWR {gin} {gout} VPB {pmodel} w={PUNIT} l={LCH}")
    lines.append(".ends")
    return "\n".join(lines) + "\n"


# gate areas spanning the region (output-stage fingers), input tapered ~2.7:1
AREAS = [6, 8, 11, 13, 16, 20]
# dopant recipes: (label, fn, fp)
RECIPES = [
    ("foundry recipe  svt/hvt", 0.0, 0.0),   # control: reconstruct the ladder's masks
    ("pfet swap       svt/svt", 0.0, 1.0),   # pfet hvt->svt only
    ("nfet swap       lvt/hvt", 1.0, 0.0),   # nfet svt->lvt only
    ("both low-Vt     lvt/svt", 1.0, 1.0),   # both swaps
    ("blend 50/50     mix",     0.5, 0.5),   # fabricable linear combination of masks
]


def main():
    # foundry ladder
    items = [{"cell": f"sky130_fd_sc_hd__buf_{n}", "lib_include": None} for n in LADDER]

    combos, libtxt = [], []
    for m2 in AREAS:
        m1 = max(1, round(m2 / 2.7))
        for label, fn, fp in RECIPES:
            nm = f"lc_{m2}_{label.split()[0]}_{int(fn*100)}_{int(fp*100)}"
            libtxt.append(blended_buffer(nm, m1, m2, fn, fp))
            combos.append({"cell": nm, "m1": m1, "m2": m2, "label": label})
    tmp = tempfile.NamedTemporaryFile("w", suffix=".spice", delete=False)
    tmp.write("\n".join(libtxt) + "\n"); tmp.close()
    for c in combos:
        c["lib_include"] = tmp.name

    res = M.measure_many(
        [{"cell": it["cell"], "lib_include": it.get("lib_include")}
         for it in items + combos], cl_farad=LOAD)
    os.unlink(tmp.name)

    fo, cu = [], []
    for r, it in zip(res, items + combos):
        if not r["ok"]:
            continue
        p = {"tpd": r["tpd_ns"], "E": r["energy_fj"], "edp": r["edp"]}
        if r["cell"].startswith("sky130_fd_sc_hd__buf_"):
            p["label"] = "buf_" + r["cell"].split("_")[-1]
            fo.append(p)
        else:
            p.update({k: it[k] for k in ("m1", "m2", "label")})
            cu.append(p)

    Emin = min(f["E"] for f in fo); Emax = max(f["E"] for f in fo)
    fo_sorted = sorted(fo, key=lambda f: f["E"])

    def beats_ladder(p):
        """Inside the energy band and strictly below the ladder: lower delay than
        every foundry buffer at equal-or-lower energy."""
        if p["E"] > Emax + 1e-9:
            return False, "outside band (too much energy)"
        # foundry buffers with energy <= this point's energy
        lower = [f for f in fo if f["E"] <= p["E"] + 1e-9]
        ref = min(lower, key=lambda f: f["tpd"]) if lower else min(fo, key=lambda f: f["E"])
        if p["tpd"] < ref["tpd"] - 1e-6:
            return True, f"faster than {ref['label']} at <= its energy"
        return False, f"not below {ref['label']}"

    for p in cu:
        p["win"], p["why"] = beats_ladder(p)

    out = {"load": LOAD, "band_fJ": [round(Emin, 1), round(Emax, 1)],
           "foundry": fo, "combos": cu}
    with open(os.path.join(HERE, "linearcomb.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"load {LOAD}   foundry energy band = [{Emin:.0f}, {Emax:.0f}] fJ "
          f"(all nfet_svt + pfet_hvt)\n")
    print("foundry ladder:")
    for f in sorted(fo, key=lambda x: x["tpd"]):
        print(f"  {f['label']:8s} tpd={f['tpd']:.4f}ns  E={f['E']:.0f}fJ  EDP={f['edp']:.1f}")
    print("\nlinear combinations (gate area x dopant masks), at 250 fF:")
    print(f"  {'area':>6} {'recipe':22} {'tpd(ns)':>9} {'E(fJ)':>7} {'EDP':>7}  verdict")
    wins = 0
    for p in sorted(cu, key=lambda x: (x["m2"], x["label"])):
        mark = "WIN " if p["win"] else "    "
        wins += p["win"]
        inband = "in-band" if p["E"] <= Emax + 1e-9 else "OUT"
        print(f"  [{p['m1']},{p['m2']}]".ljust(8)
              + f"{p['label']:22} {p['tpd']:9.4f} {p['E']:7.0f} {p['edp']:7.1f}  "
              + f"{mark}{inband}  {p['why']}")
    print(f"\n{wins} of {len(cu)} combinations beat the ladder inside its own energy band.")
    best = min((p for p in cu if p["win"]), key=lambda x: x["edp"], default=None)
    if best:
        b16 = min(fo, key=lambda f: f["tpd"])
        print(f"best in-band win: [{best['m1']},{best['m2']}] {best['label']} "
              f"tpd={best['tpd']:.4f}ns E={best['E']:.0f}fJ EDP={best['edp']:.1f}  "
              f"vs buf_16 tpd={b16['tpd']:.4f}ns E={b16['E']:.0f}fJ EDP={b16['edp']:.1f}")
    else:
        print("NO in-band linear combination beats the ladder. Back to the drawing board.")
    print("\nwrote analysis/linearcomb.json")


if __name__ == "__main__":
    main()
