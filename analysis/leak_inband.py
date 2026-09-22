#!/usr/bin/env python3
"""Static leakage of buf_16 vs the same-area [6,16] dopant swaps, both input
states, tt corner. The dynamic-energy table hides the cost the foundry bought
with its high-Vt pfet; this measures it."""
import os, re, subprocess, sys, tempfile

PDK = os.environ.get("PDK_ROOT", "/pdk")
MODELS = f"{PDK}/libs.tech/ngspice/sky130.lib.spice"
CELL_LIB = f"{PDK}/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
VDD = 1.8
NUNIT, PUNIT, LCH = "650000u", "1e+06u", "150000u"
NF = {"svt": "sky130_fd_pr__nfet_01v8", "lvt": "sky130_fd_pr__nfet_01v8_lvt"}
PF = {"hvt": "sky130_fd_pr__pfet_01v8_hvt", "svt": "sky130_fd_pr__pfet_01v8"}


def buf(name, m1, m2, fn, fp):
    L = [f".subckt {name} A VGND VNB VPB VPWR X"]
    for i, (gin, gout, m) in enumerate([("A", "n1", m1), ("n1", "X", m2)]):
        knl, kps = round(fn * m), round(fp * m)
        for j in range(m):
            nm = NF["lvt"] if j < knl else NF["svt"]
            pm = PF["svt"] if j < kps else PF["hvt"]
            L.append(f"XN{i}_{j} VGND {gin} {gout} VNB {nm} w={NUNIT} l={LCH}")
            L.append(f"XP{i}_{j} VPWR {gin} {gout} VPB {pm} w={PUNIT} l={LCH}")
    L.append(".ends")
    return "\n".join(L) + "\n"


RECIPES = [("foundry svt/hvt", 0.0, 0.0), ("pfet swap svt/svt", 0.0, 1.0),
           ("blend 50/50", 0.5, 0.5), ("both low-Vt lvt/svt", 1.0, 1.0)]
defs = "".join(buf(f"lc{i}", 6, 16, fn, fp) for i, (_, fn, fp) in enumerate(RECIPES))

# one deck: buf_16 + 4 variants, each twice (input lo / hi), static op
lines = [".title inband leakage", f'.lib "{MODELS}" tt', f'.include "{CELL_LIB}"',
         defs, f".param VDD={VDD}", "Vlo lo 0 0", "Vhi hi 0 {VDD}",
         "Vgnd VGND 0 0", "Vnb VNB 0 0", "Vpb VPB 0 {VDD}"]
cells = ["sky130_fd_sc_hd__buf_16"] + [f"lc{i}" for i in range(len(RECIPES))]
for k, c in enumerate(cells):
    for st, node in (("lo", "lo"), ("hi", "hi")):
        lines.append(f"V{k}{st} VPWR{k}{st} 0 {{VDD}}")
        lines.append(f"X{k}{st} {node} VGND VNB VPB VPWR{k}{st} o{k}{st} {c}")
lines.append(".control\nop")
for k, c in enumerate(cells):
    for st in ("lo", "hi"):
        lines.append(f"print v{k}{st}#branch")
lines.append(".endc\n.end")
deck = "\n".join(lines) + "\n"

with tempfile.TemporaryDirectory() as d:
    sp = os.path.join(d, "leak.sp")
    open(sp, "w").write(deck)
    p = subprocess.run(["ngspice", "-b", sp], capture_output=True, text=True, timeout=600)
txt = p.stdout + p.stderr
vals = {m[0]: float(m[1]) for m in re.findall(r"v(\d+(?:lo|hi))#branch\s*=\s*([-0-9.eE+]+)", txt)}

print(f"{'cell':22} {'leak_lo(nA)':>12} {'leak_hi(nA)':>12} {'avg(nA)':>10}  vs buf_16")
labels = ["buf_16 (foundry svt/hvt)"] + [r[0] for r in RECIPES]
base = None
for k, lab in enumerate(labels):
    lo = abs(vals.get(f"{k}lo", 0.0)) * 1e9
    hi = abs(vals.get(f"{k}hi", 0.0)) * 1e9
    avg = (lo + hi) / 2
    if k == 0:
        base = avg
    ratio = f"{avg/base:6.1f}x" if base else ""
    print(f"{lab:22} {lo:12.4f} {hi:12.4f} {avg:10.4f}  {ratio}")
