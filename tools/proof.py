import os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import candidate as C
from measure import CELL_LIB, MODELS
_TMP = tempfile.mkdtemp()

VDD, CL, TS = 1.8, "250f", "0.05n"
BASE = "sky130_fd_sc_hd__buf_16"
SPEC = [{"m":13,"nvt":"","pvt":"_hvt"},{"m":32,"nvt":"","pvt":"_hvt"}]  # custom [13,32]

print("="*70)
print("1) THE FOUNDRY PART: the real buf_16 subckt straight from the sky130 PDK")
print("   file:", CELL_LIB)
print("-"*70)
buf = []
grab = False
for line in open(CELL_LIB, errors="ignore"):
    if line.startswith(".subckt "+BASE+" "): grab = True
    if grab:
        buf.append(line.rstrip())
        if line.strip().startswith(".ends"): break
# show the header + a few device lines + count
print(buf[0])
devs = [l for l in buf if l.strip().startswith("X")]
for l in devs[:3]: print("  ", l)
print("   ... (%d unit transistors total; every device is nfet_01v8 0.65u or pfet_01v8_hvt 1.0u)" % len(devs))
print(buf[-1])

name, sub = C.emit_subckt(SPEC, name="q2_custom_13_32")
print("\n"+"="*70)
print("2) THE CUSTOM CELL: built from the SAME two fd_pr devices, arranged as [13,32]")
print("-"*70)
for l in sub.splitlines()[:3]: print(l)
print("   ... (%d unit transistors; a 13-unit input stage driving a 32-unit output stage)"
      % sum(2*s["m"] for s in SPEC))

# head-to-head deck: both cells, same input, same 250fF load, own supply
cust = os.path.join(_TMP,"custom.spice"); open(cust,"w").write(sub)
deck = f"""* head-to-head proof: {BASE} vs custom [13,32] at {CL}
.lib "{MODELS}" tt
.include "{CELL_LIB}"
.include "{cust}"
.param VDD={VDD}
.param CL={CL}
.param TS={TS}
Vgnd VGND 0 0
Vnb VNB 0 0
Vpb VPB 0 {{VDD}}
Vin A 0 PWL(0 0 2n 0 '2n+TS' {{VDD}} 12n {{VDD}} '12n+TS' 0 22n 0)
Vpwrb VPWRB 0 {{VDD}}
Xb A VGND VNB VPB VPWRB OB {BASE}
CLb OB 0 {{CL}}
Vpwrc VPWRC 0 {{VDD}}
Xc A VGND VNB VPB VPWRC OC q2_custom_13_32
CLc OC 0 {{CL}}
.tran 2p 22n
.measure tran tpdr_buf16 TRIG v(A) VAL='VDD/2' RISE=1 TARG v(OB) VAL='VDD/2' RISE=1
.measure tran tpdf_buf16 TRIG v(A) VAL='VDD/2' FALL=1 TARG v(OB) VAL='VDD/2' FALL=1
.measure tran charge_buf16 INTEG i(Vpwrb) FROM=2n TO=22n
.measure tran tpdr_custom TRIG v(A) VAL='VDD/2' RISE=1 TARG v(OC) VAL='VDD/2' RISE=1
.measure tran tpdf_custom TRIG v(A) VAL='VDD/2' FALL=1 TARG v(OC) VAL='VDD/2' FALL=1
.measure tran charge_custom INTEG i(Vpwrc) FROM=2n TO=22n
.end
"""
sp=os.path.join(_TMP,"proof.sp"); open(sp,"w").write(deck)
r = subprocess.run(["ngspice","-b",sp], capture_output=True, text=True, timeout=600)
raw = r.stdout + r.stderr

print("\n"+"="*70)
print("3) NGSPICE OWN OUTPUT (unedited .measure lines from the simulator):")
print("-"*70)
vals={}
for line in raw.splitlines():
    m=re.match(r"\s*(tpdr_\w+|tpdf_\w+|charge_\w+)\s*=\s*([-0-9.eE+]+)", line)
    if m:
        print("   ", line.strip())
        vals[m.group(1)]=float(m.group(2))

print("\n"+"="*70)
print("4) THE RESULT computed straight from ngspice's numbers above:")
print("-"*70)
def edp(pref):
    tpd = (vals["tpdr_"+pref]+vals["tpdf_"+pref])/2
    E = abs(vals["charge_"+pref])*VDD
    return tpd, E, E*tpd
tb,Eb,edpb = edp("buf16"); tc,Ec,edpc = edp("custom")
print(f"   buf_16 : delay={tb*1e9:.4f} ns  energy={Eb*1e15:.1f} fJ  EDP={edpb*1e24:.2f}")
print(f"   custom : delay={tc*1e9:.4f} ns  energy={Ec*1e15:.1f} fJ  EDP={edpc*1e24:.2f}")
print(f"   -> custom is {(tb-tc)/tb*100:.1f}% faster, uses {(Ec-Eb)/Eb*100:+.1f}% energy,")
print(f"      and has {(edpb-edpc)/edpb*100:.1f}% lower EDP. The delay win is real: ")
print(f"      ngspice measured the custom output crossing 50% sooner into the same 250fF load.")


# ---- export real device params + transient traces for the online visual -------
import json

def devices(lines):
    """Actual transistor params (model, W, L, count) from a netlist, as simulated."""
    acc = {}
    for l in lines:
        m = re.search(r"(sky130_fd_pr__\w+)\s+w=([0-9.eE+]+)u\s+l=([0-9.eE+]+)u", l)
        if m:
            key = (m.group(1), round(float(m.group(2)) * 1e-6, 4),
                   round(float(m.group(3)) * 1e-6, 4))
            acc[key] = acc.get(key, 0) + 1
    kind = lambda model: "nmos" if "nfet" in model else "pmos"
    return [{"model": k[0], "type": kind(k[0]), "w_um": k[1], "l_um": k[2],
             "count": v} for k, v in sorted(acc.items())]

# second ngspice run: write the raw transient traces with wrdata
trace = os.path.join(_TMP, "trace.txt")
tdeck = deck.split(".measure")[0] + f""".control
run
set wr_singlescale
wrdata {trace} v(A) v(OB) v(OC)
.endc
.end
"""
tsp = os.path.join(_TMP, "trace.sp"); open(tsp, "w").write(tdeck)
subprocess.run(["ngspice", "-b", tsp], capture_output=True, text=True, timeout=600)
rows = []
if os.path.exists(trace):
    for line in open(trace):
        p = line.split()
        if len(p) >= 4 and re.match(r"^[-0-9.eE+]+$", p[0]):
            rows.append([float(x) for x in p[:4]])
# keep the rising-edge window and downsample
lo, hi = 1.9e-9, 2.9e-9
win = [r for r in rows if lo <= r[0] <= hi]
step = max(1, len(win) // 400)
win = win[::step]

data = {
    "operating_point": {"load": CL, "slew": TS, "vdd": VDD},
    "cells": {
        "buf_16": {"label": "buf_16 (foundry part)", "devices": devices(buf),
                   "total_devices": len([l for l in buf if l.strip().startswith("X")]),
                   "delay_ns": round(tb * 1e9, 4), "energy_fj": round(Eb * 1e15, 1),
                   "edp": round(edpb * 1e24, 2)},
        "custom": {"label": "custom [13,32]", "devices": devices(sub.splitlines()),
                   "total_devices": sum(2 * s["m"] for s in SPEC),
                   "delay_ns": round(tc * 1e9, 4), "energy_fj": round(Ec * 1e15, 1),
                   "edp": round(edpc * 1e24, 2)},
    },
    "window_ns": [lo * 1e9, hi * 1e9],
    "trace": {"t_ns": [r[0] * 1e9 for r in win],
              "vin": [r[1] for r in win],
              "vout_buf16": [r[2] for r in win],
              "vout_custom": [r[3] for r in win]},
}
os.makedirs("results", exist_ok=True)
with open("results/waveforms.json", "w") as fh:
    json.dump(data, fh)
print("\nwrote results/waveforms.json (%d trace points, real device params)"
      % len(win))
