#!/usr/bin/env python3
"""1-bit full adder: foundry fa_1 vs the same-topology dopant swap.

One rung up the VLSI tree from the standard cell. The foundry sky130_fd_sc_hd__fa_1
is the classic 28-transistor mirror adder (14 nfet_svt + 14 pfet_hvt). The swap
keeps the IDENTICAL topology and only changes the Vt masks (nfet -> lvt, pfet_hvt
-> svt), so the truth table is unchanged BY CONSTRUCTION -- the strongest possible
functional-equivalence argument. Measures the carry path Cin->Cout (the adder's
critical path), dynamic energy, and static leakage. Run in the ngspice container.
"""
import json, os, re, subprocess, tempfile
PDK = os.environ.get("PDK_ROOT", "/pdk")
LIB = f"{PDK}/libs.tech/ngspice/sky130.lib.spice"
SCH = f"{PDK}/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
VDD, CL = 1.8, "4f"


def extract(name):
    out, f = [], False
    for ln in open(SCH):
        if ln.startswith(f".subckt {name} "):
            f = True
        if f:
            out.append(ln)
        if f and ln.startswith(".ends"):
            break
    return "".join(out)


def run(deck, keys):
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "r.sp")
        open(sp, "w").write(deck)
        p = subprocess.run(["ngspice", "-b", sp], capture_output=True, text=True, timeout=300)
    txt = p.stdout + p.stderr
    vals = {}
    for k in keys:
        m = re.search(re.escape(k) + r"\s*=\s*([-0-9.eE+]+)", txt, re.IGNORECASE)
        vals[k] = float(m.group(1)) if m else None
    return vals


def main():
    foundry = extract("sky130_fd_sc_hd__fa_1")
    perf = (foundry.replace("sky130_fd_sc_hd__fa_1", "q2_fa1_perf")
            .replace("sky130_fd_pr__pfet_01v8_hvt", "sky130_fd_pr__pfet_01v8")
            .replace("sky130_fd_pr__nfet_01v8", "sky130_fd_pr__nfet_01v8_lvt"))
    defs = foundry + "\n" + perf + "\n"

    # carry path: A=1, B=0 => Cout = Cin
    delay = f'''* fa carry-path delay + energy
.lib "{LIB}" tt
{defs}
.param VDD={VDD} CL={CL}
Vpb VPB 0 {{VDD}}
Vgnd VGND 0 0
Vnb VNB 0 0
Va A 0 {{VDD}}
Vb B 0 0
Vcin cin 0 pulse(0 {{VDD}} 2n 100p 100p 8n 20n)
VpwrF VPWRF 0 {{VDD}}
Xf A B cin VGND VNB VPB VPWRF coutF sumF sky130_fd_sc_hd__fa_1
CcF coutF 0 {{CL}}
CsF sumF 0 {{CL}}
VpwrP VPWRP 0 {{VDD}}
Xp A B cin VGND VNB VPB VPWRP coutP sumP q2_fa1_perf
CcP coutP 0 {{CL}}
CsP sumP 0 {{CL}}
.control
tran 2p 22n
meas tran tclh_F trig v(cin) val=0.9 rise=1 targ v(coutF) val=0.9 rise=1
meas tran tchl_F trig v(cin) val=0.9 fall=1 targ v(coutF) val=0.9 fall=1
meas tran tclh_P trig v(cin) val=0.9 rise=1 targ v(coutP) val=0.9 rise=1
meas tran tchl_P trig v(cin) val=0.9 fall=1 targ v(coutP) val=0.9 fall=1
meas tran qF integ i(VpwrF) from=2n to=22n
meas tran qP integ i(VpwrP) from=2n to=22n
.endc
.end
'''
    d = run(delay, ["tclh_F", "tchl_F", "tclh_P", "tchl_P", "qF", "qP"])

    leak = f'''* fa static leakage, states 000 and 111
.lib "{LIB}" tt
{defs}
.param VDD={VDD}
Vlo lo 0 0
Vhi hi 0 {{VDD}}
Vgnd VGND 0 0
Vnb VNB 0 0
Vpb VPB 0 {{VDD}}
Vsa PWA 0 {{VDD}}
Xfa lo lo lo VGND VNB VPB PWA cfa sfa sky130_fd_sc_hd__fa_1
Vsb PWB 0 {{VDD}}
Xfb hi hi hi VGND VNB VPB PWB cfb sfb sky130_fd_sc_hd__fa_1
Vsc PWC 0 {{VDD}}
Xpa lo lo lo VGND VNB VPB PWC cpa spa q2_fa1_perf
Vsd PWD 0 {{VDD}}
Xpb hi hi hi VGND VNB VPB PWD cpb spb q2_fa1_perf
.control
op
print i(Vsa) i(Vsb) i(Vsc) i(Vsd)
.endc
.end
'''
    lk = run(leak, ["i(vsa)", "i(vsb)", "i(vsc)", "i(vsd)"])

    def tpd(a, b):
        return (a + b) / 2 * 1e12  # ps
    fo_d = tpd(d["tclh_F"], d["tchl_F"])
    pf_d = tpd(d["tclh_P"], d["tchl_P"])
    fo_e = abs(d["qF"]) * VDD * 1e15   # fJ
    pf_e = abs(d["qP"]) * VDD * 1e15
    fo_lk = (abs(lk["i(vsa)"]) + abs(lk["i(vsb)"])) / 2 * 1e12  # pA
    pf_lk = (abs(lk["i(vsc)"]) + abs(lk["i(vsd)"])) / 2 * 1e12
    res = {
        "cell": "sky130_fd_sc_hd__fa_1", "topology": "28T mirror adder (14 nfet + 14 pfet)",
        "swap": "nfet_01v8->_lvt, pfet_01v8_hvt->pfet_01v8 (svt); identical topology",
        "path": "carry Cin->Cout, A=1 B=0", "load": CL,
        "foundry": {"delay_ps": round(fo_d, 1), "energy_fJ": round(fo_e, 1),
                    "edp": round(fo_d * fo_e, 0), "leak_pA": round(fo_lk, 2)},
        "swap_perf": {"delay_ps": round(pf_d, 1), "energy_fJ": round(pf_e, 1),
                      "edp": round(pf_d * pf_e, 0), "leak_pA": round(pf_lk, 2)},
        "delta": {"delay_pct": round((pf_d/fo_d-1)*100, 1), "energy_pct": round((pf_e/fo_e-1)*100, 1),
                  "edp_pct": round((pf_d*pf_e)/(fo_d*fo_e-1e-9)*100-100, 1), "leak_x": round(pf_lk/fo_lk, 1)},
    }
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fa_result.json"), "w"), indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
