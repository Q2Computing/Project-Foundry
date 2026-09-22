#!/usr/bin/env python3
"""
characterize.py: extract the logical-effort constants for the sky130 unit inverter.

The analytical model needs three numbers, measured (not assumed) from the real
devices in ngspice:

  tau  : the delay per unit of electrical effort (ns), the slope of delay vs fanout
  p    : the inverter parasitic delay (in units of tau), the intercept
  Cu   : the unit-inverter input capacitance (fF), so a real load in fF becomes a
         fanout L = C_L / Cu

Method:
  * fanout sweep: a unit inverter drives k copies of itself (k = 1..8); its
    propagation delay is D(k) = tau*(k + p). A straight-line fit gives tau and p.
  * input cap: slowly ramp an isolated unit-inverter gate and integrate the gate
    current; Cu = Q / VDD.

Writes analysis/le_params.json.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

PDK = os.environ.get("PDK_ROOT", "/pdk")
MODELS = f"{PDK}/libs.tech/ngspice/sky130.lib.spice"
VDD = 1.8
NFET, PFET = "sky130_fd_pr__nfet_01v8", "sky130_fd_pr__pfet_01v8_hvt"
UNIT = f""".subckt q2_unit A VGND VNB VPB VPWR X
XN VGND A X VNB {NFET} w=650000u l=150000u
XP VPWR A X VPB {PFET} w=1000000u l=150000u
.ends
"""
KS = [1, 2, 3, 4, 6, 8]


def ngspice(deck):
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "c.sp")
        open(sp, "w").write(deck)
        r = subprocess.run(["ngspice", "-b", sp], capture_output=True, text=True,
                           timeout=600)
        return r.stdout + r.stderr


def fanout_sweep():
    """delay of a unit inverter driving k unit-inverter loads, for each k."""
    parts = [f'* fanout sweep', f'.lib "{MODELS}" tt', UNIT,
             f'.param VDD={VDD}', 'Vgnd VGND 0 0', 'Vnb VNB 0 0',
             'Vpb VPB 0 {VDD}',
             "Vin A 0 PWL(0 0 2n 0 '2n+0.05n' {VDD} 12n {VDD} '12n+0.05n' 0 22n 0)"]
    meas = []
    for i, k in enumerate(KS):
        # DUT driven by A, output OUT{i} loads k unit inverters (inputs tied)
        parts.append(f'Vp{i} VP{i} 0 {{VDD}}')
        parts.append(f'Xd{i} A VGND VNB VPB VP{i} O{i} q2_unit')
        for j in range(k):
            parts.append(f'Xl{i}_{j} O{i} VGND VNB VPB VP{i} T{i}_{j} q2_unit')
        meas += [
            f".measure tran r{i} TRIG v(A) VAL='VDD/2' FALL=1 TARG v(O{i}) VAL='VDD/2' RISE=1",
            f".measure tran f{i} TRIG v(A) VAL='VDD/2' RISE=1 TARG v(O{i}) VAL='VDD/2' FALL=1"]
    deck = "\n".join(parts + [".tran 1p 22n"] + meas + [".end"]) + "\n"
    out = ngspice(deck)
    vals = {k: float(v) for k, v in
            re.findall(r"^\s*([rf]\d+)\s*=\s*([-0-9.eE+]+)", out, re.M)}
    D = []
    for i, k in enumerate(KS):
        r, f = vals.get(f"r{i}"), vals.get(f"f{i}")
        if r and f:
            D.append((k, (r + f) / 2 * 1e9))  # ns
    return D


def input_cap():
    """Cu = integral of gate current while slowly ramping the input, over VDD."""
    deck = f"""* unit inverter input cap
.lib "{MODELS}" tt
{UNIT}
.param VDD={VDD}
Vgnd VGND 0 0
Vnb VNB 0 0
Vpb VPB 0 {{VDD}}
Vramp A 0 PWL(0 0 20n {{VDD}})
Xu A VGND VNB VPB VPWR O q2_unit
Vpwr VPWR 0 {{VDD}}
CL O 0 3.2f
.tran 2p 20n
.measure tran q INTEG i(Vramp) FROM=0 TO=20n
.end
"""
    out = ngspice(deck)
    m = re.search(r"^\s*q\s*=\s*([-0-9.eE+]+)", out, re.M)
    if not m:
        return None
    return abs(float(m.group(1))) / VDD * 1e15  # fF


def fit_line(D):
    """least-squares D = tau*k + b; return tau, p=b/tau."""
    n = len(D)
    sx = sum(k for k, _ in D); sy = sum(d for _, d in D)
    sxx = sum(k * k for k, _ in D); sxy = sum(k * d for k, d in D)
    tau = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - tau * sx) / n
    return tau, b / tau


def main():
    D = fanout_sweep()
    print("fanout sweep (k, delay ns):")
    for k, d in D:
        print(f"  k={k}  D={d:.4f}")
    tau, p = fit_line(D)
    Cu = input_cap()
    print(f"\ntau = {tau:.5f} ns / fanout")
    print(f"p   = {p:.3f} (parasitic, in tau)")
    print(f"Cu  = {Cu:.3f} fF (unit-inverter input cap)")
    os.makedirs("analysis", exist_ok=True)
    with open("analysis/le_params.json", "w") as fh:
        json.dump({"tau_ns": tau, "p": p, "Cu_fF": Cu,
                   "fanout_delay_ns": D, "vdd": VDD}, fh, indent=2)
    print("\nwrote analysis/le_params.json")


if __name__ == "__main__":
    main()
