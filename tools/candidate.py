#!/usr/bin/env python3
"""
candidate.py -- build a custom driver cell from a device-layer spec.

Faithful to how sky130 actually builds drive strength: the fd_pr models are
binned only to ~1um, so a foundry buffer is many UNIT inverters in parallel
(buf_16 == ~22 parallel unit inverters, every device the same nfet 0.65um /
pfet_hvt 1.0um as buf_1). We build candidates the same way. A stage is a
multiplicity `m` of unit inverters; drive strength is m, exactly like the
ladder. The custom edge the fixed 2-stage ladder cannot reach: arbitrary stage
counts, arbitrary per-stage multiplicities (taper), and per-stage Vt mixes.

An even number of stages => non-inverting (matches a foundry buffer's function).

spec = [{"m": int, "nvt": "", "pvt": "_hvt"}, ...]   (even length)
emit_subckt() writes `.subckt <name> A VGND VNB VPB VPWR X` as literal parallel
unit devices -- identical modeling to the foundry cells, so both sides are
measured on the same ruler. The canonical form is hashed for dedup/provenance.
"""
import hashlib
import json

L_UM = 0.15         # channel length, same as sc_hd
NUNIT_UM = 0.65     # unit nfet width (== inv_1 / buf_16 unit)
PUNIT_UM = 1.00     # unit pfet width (== inv_1 / buf_16 unit); 1.0/0.65 ratio
NFET = {"": "sky130_fd_pr__nfet_01v8", "_lvt": "sky130_fd_pr__nfet_01v8_lvt"}
PFET = {"": "sky130_fd_pr__pfet_01v8", "_hvt": "sky130_fd_pr__pfet_01v8_hvt",
        "_lvt": "sky130_fd_pr__pfet_01v8_lvt", "_mvt": "sky130_fd_pr__pfet_01v8_mvt"}


def _u(um):
    return f"{int(round(um * 1e6))}u"   # foundry style: 0.65um -> 650000u


def canonical(spec):
    norm = [{"m": int(s["m"]), "nvt": s.get("nvt", ""),
             "pvt": s.get("pvt", "_hvt")} for s in spec]
    return json.dumps(norm, sort_keys=True, separators=(",", ":"))


def design_hash(spec):
    return hashlib.sha256(canonical(spec).encode()).hexdigest()


def cell_name(spec):
    return "q2drv_" + design_hash(spec)[:12]


def emit_subckt(spec, name=None):
    n = len(spec)
    assert n % 2 == 0 and n >= 2, "need an even number of stages (non-inverting)"
    name = name or cell_name(spec)
    nodes = ["A"] + [f"n{i}" for i in range(1, n)] + ["X"]
    lines = [f".subckt {name} A VGND VNB VPB VPWR X"]
    for i, s in enumerate(spec):
        gin, gout = nodes[i], nodes[i + 1]
        nvt, pvt = s.get("nvt", ""), s.get("pvt", "_hvt")
        for j in range(int(s["m"])):
            lines.append(f"XN{i}_{j} VGND {gin} {gout} VNB {NFET[nvt]} "
                         f"w={_u(NUNIT_UM)} l={_u(L_UM)}")
            lines.append(f"XP{i}_{j} VPWR {gin} {gout} VPB {PFET[pvt]} "
                         f"w={_u(PUNIT_UM)} l={_u(L_UM)}")
    lines.append(".ends")
    return name, "\n".join(lines) + "\n"


def area_um(spec):
    return sum(int(s["m"]) * (NUNIT_UM + PUNIT_UM) for s in spec)


if __name__ == "__main__":
    spec = [
        {"m": 1, "nvt": "", "pvt": "_hvt"},
        {"m": 4, "nvt": "", "pvt": "_hvt"},
        {"m": 10, "nvt": "", "pvt": "_hvt"},
        {"m": 24, "nvt": "_lvt", "pvt": "_lvt"},
    ]
    name, txt = emit_subckt(spec)
    print(txt)
    print(f"* name={name} area_um={area_um(spec):.2f} hash={design_hash(spec)}")
