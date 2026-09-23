#!/usr/bin/env python3
"""sky130 smallest buffers with the low-Vt swap, plus hypothetical sub-unit points.

Real, measured: buf_1 = [1,1] and buf_2 = [1,2] at the foundry recipe (nfet_svt +
pfet_hvt) and the low-Vt swap (nfet_lvt + pfet_svt), at 250 fF.

Hypothetical: buf_1/4 (drive 0.25) and buf_1/32 (drive ~0.031) are BELOW the
minimum fabricable finger (sky130's smallest device is the drive-1 unit), so they
cannot be built or SPICE-measured. They are extrapolated from the measured
low-Vt points by the logical-effort scaling delay ~ 1/drive at a fixed load, with
energy floored at the load's own CV^2. Marked hypothetical everywhere.
"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import measure as M  # noqa
NUNIT, PUNIT, LCH = "650000u", "1e+06u", "150000u"
NF = {"svt": "sky130_fd_pr__nfet_01v8", "lvt": "sky130_fd_pr__nfet_01v8_lvt"}
PF = {"hvt": "sky130_fd_pr__pfet_01v8_hvt", "svt": "sky130_fd_pr__pfet_01v8"}
LOAD = "250f"

def buf(name, m1, m2, nvt, pvt):
    L = [f".subckt {name} A VGND VNB VPB VPWR X"]
    for i, (gin, gout, m) in enumerate([("A","n1",m1),("n1","X",m2)]):
        for j in range(m):
            L.append(f"XN{i}_{j} VGND {gin} {gout} VNB {NF[nvt]} w={NUNIT} l={LCH}")
            L.append(f"XP{i}_{j} VPWR {gin} {gout} VPB {PF[pvt]} w={PUNIT} l={LCH}")
    L.append(".ends"); return "\n".join(L) + "\n"

CELLS = [  # label, m1, m2, nvt, pvt
    ("buf_1 foundry [1,1] svt/hvt", 1, 1, "svt", "hvt"),
    ("buf_1 low-Vt  [1,1] lvt/svt", 1, 1, "lvt", "svt"),
    ("buf_2 foundry [1,2] svt/hvt", 1, 2, "svt", "hvt"),
    ("buf_2 low-Vt  [1,2] lvt/svt", 1, 2, "lvt", "svt"),
]

def main():
    lib, items = [], []
    for i, (lab, m1, m2, nvt, pvt) in enumerate(CELLS):
        nm = f"sb{i}"; lib.append(buf(nm, m1, m2, nvt, pvt))
        items.append({"cell": nm, "_lab": lab})
    tmp = tempfile.NamedTemporaryFile("w", suffix=".spice", delete=False)
    tmp.write("\n".join(lib) + "\n"); tmp.close()
    for it in items: it["lib_include"] = tmp.name
    res = M.measure_many([{"cell": it["cell"], "lib_include": it["lib_include"]} for it in items], cl_farad=LOAD)
    os.unlink(tmp.name)
    out = []
    for r, it in zip(res, items):
        out.append({"label": it["_lab"], "ok": r["ok"], "tpd_ns": r["tpd_ns"],
                    "E_fj": r["energy_fj"], "edp": r["edp"]})
    # hypothetical sub-unit low-Vt points: extrapolate from buf_1 low-Vt.
    base = next(o for o in out if o["label"].startswith("buf_1 low-Vt"))
    hyp = []
    for frac, name in [(0.25, "buf_1/4"), (1/32, "buf_1/32")]:
        # drive scales the pull strength: delay ~ base_delay / frac (fixed 250fF load)
        tpd = base["tpd_ns"] / frac
        E = base["E_fj"]  # energy is load-dominated at 250fF, ~unchanged
        hyp.append({"label": f"{name} low-Vt (hypothetical, sub-unit)",
                    "drive": round(frac, 4), "tpd_ns": round(tpd, 4),
                    "E_fj": round(E, 1), "edp": round(tpd * E, 1)})
    data = {"load": LOAD, "measured": out, "hypothetical": hyp}
    json.dump(data, open(os.path.join(HERE, "smallbuf.json"), "w"), indent=2)
    print(f"sky130 smallest buffers at {LOAD}:")
    for o in out:
        print(f"  {o['label']:32s} tpd={o['tpd_ns']:.4f}ns E={o['E_fj']:.0f}fJ EDP={o['edp']:.1f}")
    print("hypothetical sub-unit low-Vt (extrapolated, NOT fabricable):")
    for h in hyp:
        print(f"  {h['label']:40s} drive={h['drive']:.4f} tpd={h['tpd_ns']:.3f}ns EDP={h['edp']:.0f}")
    print("wrote analysis/smallbuf.json")

if __name__ == "__main__":
    main()
