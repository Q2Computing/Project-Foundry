#!/usr/bin/env python3
"""
codesign.py: differentiable-physics gradient co-design of sizing AND dopant.

The Q2 thesis in one primitive. A driver cell is modeled as a differentiable
function of its design x = (m1, m2, g):

  * m1, m2 : input / output stage multiplicities (sizing)
  * g      : dopant/Vt knob spanning two REAL foundry endpoints, both fabricable
             today: g=0 = nfet_svt + pfet_hvt (highest Vt available, slow, low
             leak), g=1 = nfet_lvt + pfet_svt (lowest Vt fabricable, fast, leaky).
             sky130 ships nfet svt/lvt (no hvt) and pfet svt/hvt (no lvt), so
             those two combos bound what a mask set can build. g in (0,1) is a
             PREDICTED intermediate implant, fabricable only via distributed
             silicon: it is the hypothesis the commons exists to measure.

  The two speed knobs are physically ASYMMETRIC (measured, analysis/
  vt_calibration.json): nfet svt->lvt buys -9.7% on the fall edge for 3x leak
  (nearly free), while pfet hvt->svt buys -23% on the rise edge for 121x leak
  (expensive). A single g here interpolates the full-inverter average of both;
  the asymmetry is why context, not a fixed recipe, should pick the dopant.

Everything is calibrated to SPICE:
  delay   = tau0 * (1 - kv*g) * (m2/m1 + L/m2 + 2p)          [logical effort + Vt]
  E_dyn   = (C_L + kcell*(m1+m2)*Cu) * Vdd^2                  [switching energy]
  leak    = Ileak0 * (m1+m2) * ratio^g                       [subthreshold, calibrated]
  E_leak  = leak * Vdd * t_idle                              [static energy while idle]
  E_total = E_dyn + E_leak
  EDP     = delay * E_total

A context is (C_L, t_idle): the load and how long the cell idles per operation.
We descend the gradient of the context objective through this differentiable
model to the optimal (m1, m2, g). The point: the optimum -- including the dopant
-- MOVES with context. Active/hot-path contexts pull g up (low Vt, fast);
idle-heavy contexts pull g down (high Vt, low leak). No search, a gradient.

Calibration sources: analysis/le_params.json (tau0,p,Cu,kcell) + the hvt/svt
unit-inverter measurement (kv, ratio, Ileak0). SPICE confirms the sizing at a
fabricable endpoint; the continuous-g cell is emitted as a `predicted` commons
entry for distributed fab to promote to `measured`.
"""
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "le_params.json")) as fh:
    LP = json.load(fh)
TAU0, P, CU, VDD = LP["tau_ns"], LP["p"], LP["Cu_fF"], LP["vdd"]
KCELL = 1.273                 # cell-energy coeff (analysis/model.py calibration)
V2 = VDD * VDD

# dopant calibration from the measured unit-inverter Vt span (analysis/
# vt_calibration.json). Endpoints are real fabricable flavor combos:
#   g=0  nfet_svt + pfet_hvt : avg tpd 268.9 ps, avg leak 2.285 pA
#   g=1  nfet_lvt + pfet_svt : avg tpd 218.0 ps, avg leak 162.9 pA
# The earlier pfet-only read (KV=0.152, ratio=6465x) missed the nfet edge and
# encoded a false leakage cliff; the full-inverter span is 18.9% speed and 71x leak.
KV = 0.189                    # fractional speedup g=0->g=1 (268.9->218.0 ps avg tpd)
LEAK_RATIO = 162.9 / 2.285    # full-inverter leakage ratio, measured ~71x
ILEAK0 = 2.285e-12           # per-unit-inverter avg leakage at g=0, A


def model(x, CL_fF, t_idle_ns):
    m1, m2, g = x
    L = CL_fF / CU
    delay = TAU0 * (1 - KV * g) * (m2 / m1 + L / m2 + 2 * P)      # ns
    E_dyn = (CL_fF + KCELL * (m1 + m2) * CU) * V2                 # fJ
    leak = ILEAK0 * (m1 + m2) * (LEAK_RATIO ** g)                # A
    E_leak = leak * VDD * (t_idle_ns * 1e-9) * 1e15              # fJ
    E_tot = E_dyn + E_leak
    return {"delay_ns": delay, "E_dyn_fj": E_dyn, "E_leak_fj": E_leak,
            "E_fj": E_tot, "edp": delay * E_tot, "leak_A": leak}


def objective(x, CL_fF, t_idle_ns):
    return model(x, CL_fF, t_idle_ns)["edp"]


def grad(f, x, *a, h=1e-4):
    g = []
    for i in range(len(x)):
        xp = list(x); xm = list(x)
        step = h * max(1.0, abs(x[i]))
        xp[i] += step; xm[i] -= step
        g.append((f(xp, *a) - f(xm, *a)) / (2 * step))
    return g


def clamp(x):
    m1, m2, g = x
    return [max(1.0, m1), max(1.0, m2), min(1.0, max(0.0, g))]


def descend(CL_fF, t_idle_ns, x0=(4.0, 12.0, 0.5), iters=6000):
    """Adam gradient descent through the differentiable model (auto-scales the
    very different magnitudes of m1, m2 and g)."""
    x = list(x0)
    m = [0.0, 0.0, 0.0]; v = [0.0, 0.0, 0.0]
    b1, b2, eps = 0.9, 0.999, 1e-9
    step = [0.4, 0.4, 0.01]        # per-variable Adam step (parameter-space scale)
    for t in range(1, iters + 1):
        gr = grad(objective, x, CL_fF, t_idle_ns)
        for i in range(3):
            m[i] = b1 * m[i] + (1 - b1) * gr[i]
            v[i] = b2 * v[i] + (1 - b2) * gr[i] * gr[i]
            mh = m[i] / (1 - b1 ** t); vh = v[i] / (1 - b2 ** t)
            x[i] -= step[i] * mh / (math.sqrt(vh) + eps)
        x = clamp(x)
    return x


CONTEXTS = [
    ("small load, hot path",     12.0, 1.0),
    ("small load, idle-heavy",   12.0, 100000.0),
    ("large load, hot path",    200.0, 1.0),
    ("large load, moderate",    200.0, 3000.0),
    ("large load, idle-heavy",  200.0, 100000.0),
]


def commons_entry(name, CL, t_idle, x, m):
    m1, m2, g = x
    fabricable = g < 0.02 or g > 0.98
    spec = {"m1": round(m1, 2), "m2": round(m2, 2), "g_dopant": round(g, 4)}
    payload = {"schema": "q2.codesign.v1", "context": {"C_L_fF": CL, "t_idle_ns": t_idle},
               "design": spec, "predicted": {k: round(m[k], 4) for k in
               ("delay_ns", "E_fj", "E_leak_fj", "edp", "leak_A")}}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = "0x" + hashlib.sha256(blob.encode()).hexdigest()
    return {"context": name, "design": spec,
            "status": "measured-endpoint" if fabricable else "predicted",
            "note": ("fabricable foundry flavor (g~0 nfet_svt+pfet_hvt / g~1 nfet_lvt+pfet_svt)"
                     if fabricable
                     else "intermediate Vt implant: PREDICTED, awaiting distributed silicon"),
            "artifact_hash": h,
            "stylus_call": f"record({h}, {min(65535, round(g*1000))}, {round(CL)})"}


def main():
    print(f"calibration: tau0={TAU0*1e3:.2f}ps p={P:.3f} Cu={CU:.3f}fF kcell={KCELL} "
          f"| Vt: speedup(g=1)={KV*100:.1f}% leak_ratio={LEAK_RATIO:.0f}x")
    print("\ngradient co-design of (m1, m2, dopant g) per context:\n")
    entries = []
    for name, CL, t_idle in CONTEXTS:
        x = descend(CL, t_idle)
        m = model(x, CL, t_idle)
        m1, m2, g = x
        vt = "hvt(slow,low-leak)" if g < 0.35 else ("svt(fast,leaky)" if g > 0.65 else "mid-Vt")
        print(f"  {name:24s} C_L={CL:5.0f}fF t_idle={t_idle:>8.0f}ns  ->  "
              f"[m1={m1:4.1f}, m2={m2:4.1f}, g={g:.2f} {vt}]")
        print(f"      delay={m['delay_ns']:.4f}ns  E_dyn={m['E_dyn_fj']:.1f}fJ  "
              f"E_leak={m['E_leak_fj']:.1f}fJ  EDP={m['edp']:.2f}")
        entries.append(commons_entry(name, CL, t_idle, x, m))
    with open("analysis/codesign.json", "w") as fh:
        json.dump({"calibration": {"tau0_ns": TAU0, "p": P, "Cu_fF": CU,
                   "kcell": KCELL, "kv": KV, "leak_ratio": LEAK_RATIO,
                   "Ileak0_A": ILEAK0}, "entries": entries}, fh, indent=2)
    print("\ncommons entries (Stylus, predicted vs fabricable):")
    for e in entries:
        print(f"  {e['context']:24s} {e['status']:16s} g={e['design']['g_dopant']}  {e['stylus_call'][:38]}...")
    print("\nwrote analysis/codesign.json")


if __name__ == "__main__":
    main()
