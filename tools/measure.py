#!/usr/bin/env python3
"""
measure.py: the single SPICE measurement operator.

Every candidate and every foundry baseline cell is measured HERE, in the same
ngspice testbench, so the numbers sit on one ruler. Given a cell (a foundry
sc_hd cell, or a custom candidate subckt) it returns, at one operating point
(input slew + load): propagation delay, supply energy per switching cycle, a
transistor-area proxy, and a pass/fail on whether the output still swings
rail-to-rail (function check).

Runs INSIDE the ngspice container. The sky130 PDK is at $PDK_ROOT (/pdk locally,
the ciel-installed sky130A in CI). Nothing here is Q2-specific; a stranger with
the open PDK reproduces every number.
"""
import os
import re
import subprocess
import tempfile

PDK_ROOT = os.environ.get("PDK_ROOT", "/pdk")
CELL_LIB = f"{PDK_ROOT}/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
MODELS = f"{PDK_ROOT}/libs.tech/ngspice/sky130.lib.spice"
VDD = 1.8

# canonical port roles for an sc_hd combinational buffer/inverter footprint
RAILS = {"VGND", "VNB", "VPB", "VPWR"}
IN_PIN = "A"
OUT_PINS = ("X", "Y")  # buffers expose X, inverters Y


def find_subckt_ports(lib_path, cell):
    """Return the ordered port list of `.subckt <cell> ...` from lib_path."""
    pat = re.compile(rf"^\.subckt\s+{re.escape(cell)}\s+(.*)$", re.I)
    with open(lib_path, "r", errors="ignore") as fh:
        for line in fh:
            m = pat.match(line.strip())
            if m:
                return m.group(1).split()
    raise ValueError(f"subckt {cell} not found in {lib_path}")


def device_widths(lib_path, cell):
    """Sum of device widths (um) inside a subckt, a transistor-area proxy.

    Not a layout area. It is the honest netlist-level cost that a device-layer
    designer trades against speed; real cell area comes later from the layout
    flow. Widths in the sc_hd spice are written like w=650000u == 0.65 (um).
    """
    total = 0.0
    inside = False
    start = re.compile(rf"^\.subckt\s+{re.escape(cell)}\s", re.I)
    with open(lib_path, "r", errors="ignore") as fh:
        for line in fh:
            s = line.strip()
            if start.match(s):
                inside = True
                continue
            if inside:
                if s.lower().startswith(".ends"):
                    break
                m = re.search(r"\bw=([0-9.eE+]+)u\b", s)
                if m:
                    total += float(m.group(1)) * 1e-6  # ...u -> value
    return total  # in um


def _deck(cell, lib_include, cl_farad, slew_s, corner):
    ports = find_subckt_ports(lib_include, cell)
    out = next((p for p in ports if p in OUT_PINS), None)
    if out is None:
        raise ValueError(f"no output port (X/Y) in {cell}: {ports}")
    # wire the instance in declared port order
    wiring = {"A": "A", "VGND": "VGND", "VNB": "VNB", "VPB": "VPB",
              "VPWR": "VPWR", out: "OUT"}
    nodes = " ".join(wiring[p] for p in ports)
    extra = f'.include "{lib_include}"\n' if lib_include != CELL_LIB else ""
    return f"""* q2-edp measurement: {cell} CL={cl_farad} slew={slew_s} corner={corner}
.lib "{MODELS}" {corner}
.include "{CELL_LIB}"
{extra}.param VDD={VDD}
.param CL={cl_farad}
.param TS={slew_s}
Vpwr VPWR 0 {{VDD}}
Vgnd VGND 0 0
Vnb  VNB  0 0
Vpb  VPB  0 {{VDD}}
Vin  A 0 PWL(0 0  2n 0  '2n+TS' {{VDD}}  12n {{VDD}}  '12n+TS' 0  22n 0)
Xdut {nodes} {cell}
CLo  OUT 0 {{CL}}
.tran 2p 22n
.measure tran tpdr TRIG v(A) VAL='VDD/2' RISE=1 TARG v(OUT) VAL='VDD/2' RISE=1
.measure tran tpdf TRIG v(A) VAL='VDD/2' FALL=1 TARG v(OUT) VAL='VDD/2' FALL=1
.measure tran qsup INTEG i(Vpwr) FROM=2n TO=22n
.measure tran vmax MAX v(OUT) FROM=8n TO=11n
.measure tran vmin MIN v(OUT) FROM=18n TO=21n
.end
"""


_MEAS = re.compile(r"^\s*(tpdr|tpdf|qsup|vmax|vmin)\s*=\s*([-0-9.eE+]+)", re.M)


def measure(cell, lib_include=None, cl_farad="60f", slew_s="0.05n", corner="tt"):
    """Measure one cell at one operating point. Returns a metrics dict.

    lib_include: path to a custom candidate .spice (defines `cell`); None for a
    foundry sc_hd cell.
    """
    lib_include = lib_include or CELL_LIB
    deck = _deck(cell, lib_include, cl_farad, slew_s, corner)
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "run.sp")
        with open(sp, "w") as fh:
            fh.write(deck)
        p = subprocess.run(["ngspice", "-b", sp], capture_output=True,
                           text=True, timeout=300)
    vals = {k: float(v) for k, v in _MEAS.findall(p.stdout + p.stderr)}
    tpdr, tpdf = vals.get("tpdr"), vals.get("tpdf")
    qsup = vals.get("qsup")
    vmax, vmin = vals.get("vmax"), vals.get("vmin")
    ok = all(x is not None for x in (tpdr, tpdf, qsup, vmax, vmin))
    # function check: output must swing rail-to-rail (>90% high, <10% low)
    functional = ok and vmax > 0.9 * VDD and vmin < 0.1 * VDD
    # symmetry: a usable driver must not be wildly skew; both edges finite/pos
    edges_ok = ok and tpdr is not None and tpdf is not None and \
        tpdr > 0 and tpdf > 0
    tpd = (tpdr + tpdf) / 2 if edges_ok else None
    energy = abs(qsup) * VDD if qsup is not None else None  # J per cycle
    area = device_widths(lib_include, cell)  # um (width proxy, L fixed 0.15u)
    return {
        "cell": cell,
        "corner": corner,
        "cl": cl_farad,
        "slew": slew_s,
        "tpd_ns": tpd * 1e9 if tpd else None,
        "tpdr_ns": tpdr * 1e9 if tpdr else None,
        "tpdf_ns": tpdf * 1e9 if tpdf else None,
        "energy_fj": energy * 1e15 if energy else None,
        "edp": (energy * tpd * 1e24) if (energy and tpd) else None,  # fJ*ns
        "area_um": area,
        "functional": bool(functional),
        "ok": bool(edges_ok and functional),
    }


def measure_many(items, cl_farad="120f", slew_s="0.05n", corner="tt"):
    """Measure many cells in ONE ngspice run (models load once).

    items: list of {"cell": name, "lib_include": path_or_None}. Each DUT gets its
    own VPWR source so its supply energy is separable; VGND/VNB/VPB and the input
    stimulus are shared. Returns list of metrics dicts aligned to `items`.
    """
    # concatenate candidate includes once (dedup by path)
    includes, seen = [], set()
    for it in items:
        li = it.get("lib_include")
        if li and li != CELL_LIB and li not in seen:
            seen.add(li)
            with open(li) as fh:
                includes.append(fh.read())
    hdr = [f'* q2-edp batch: {len(items)} DUTs CL={cl_farad} slew={slew_s} '
           f'corner={corner}',
           f'.lib "{MODELS}" {corner}',
           f'.include "{CELL_LIB}"']
    body = ["".join(includes),
            f".param VDD={VDD}", f".param CL={cl_farad}", f".param TS={slew_s}",
            "Vgnd VGND 0 0", "Vnb VNB 0 0", "Vpb VPB 0 {VDD}",
            "Vin A 0 PWL(0 0  2n 0  '2n+TS' {VDD}  12n {VDD}  '12n+TS' 0  22n 0)"]
    meas = []
    for k, it in enumerate(items):
        cell = it["cell"]
        li = it.get("lib_include") or CELL_LIB
        ports = find_subckt_ports(li, cell)
        out = next((p for p in ports if p in OUT_PINS), None)
        wiring = {"A": "A", "VGND": "VGND", "VNB": "VNB", "VPB": "VPB",
                  "VPWR": f"VPWR{k}", out: f"O{k}"}
        nodes = " ".join(wiring[p] for p in ports)
        body.append(f"Vpwr{k} VPWR{k} 0 {{VDD}}")
        body.append(f"X{k} {nodes} {cell}")
        body.append(f"CL{k} O{k} 0 {{CL}}")
        meas += [
            f".measure tran tpdr{k} TRIG v(A) VAL='VDD/2' RISE=1 TARG v(O{k}) VAL='VDD/2' RISE=1",
            f".measure tran tpdf{k} TRIG v(A) VAL='VDD/2' FALL=1 TARG v(O{k}) VAL='VDD/2' FALL=1",
            f".measure tran qsup{k} INTEG i(Vpwr{k}) FROM=2n TO=22n",
            f".measure tran vmax{k} MAX v(O{k}) FROM=8n TO=11n",
            f".measure tran vmin{k} MIN v(O{k}) FROM=18n TO=21n"]
    deck = "\n".join(hdr + body + [".tran 2p 22n"] + meas + [".end"]) + "\n"

    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "batch.sp")
        with open(sp, "w") as fh:
            fh.write(deck)
        p = subprocess.run(["ngspice", "-b", sp], capture_output=True,
                           text=True, timeout=1200)
    txt = p.stdout + p.stderr
    pat = re.compile(r"^\s*(tpdr|tpdf|qsup|vmax|vmin)(\d+)\s*=\s*([-0-9.eE+]+)", re.M)
    vals = {}
    for name, idx, v in pat.findall(txt):
        vals.setdefault(int(idx), {})[name] = float(v)
    out = []
    for k, it in enumerate(items):
        v = vals.get(k, {})
        tpdr, tpdf = v.get("tpdr"), v.get("tpdf")
        qsup, vmax, vmin = v.get("qsup"), v.get("vmax"), v.get("vmin")
        ok = all(x is not None for x in (tpdr, tpdf, qsup, vmax, vmin))
        functional = ok and vmax > 0.9 * VDD and vmin < 0.1 * VDD
        edges_ok = ok and tpdr > 0 and tpdf > 0
        tpd = (tpdr + tpdf) / 2 if edges_ok else None
        energy = abs(qsup) * VDD if qsup is not None else None
        area = device_widths(it.get("lib_include") or CELL_LIB, it["cell"])
        out.append({
            "cell": it["cell"], "corner": corner, "cl": cl_farad, "slew": slew_s,
            "tpd_ns": tpd * 1e9 if tpd else None,
            "tpdr_ns": tpdr * 1e9 if tpdr else None,
            "tpdf_ns": tpdf * 1e9 if tpdf else None,
            "energy_fj": energy * 1e15 if energy else None,
            "edp": (energy * tpd * 1e24) if (energy and tpd) else None,
            "area_um": area,
            "functional": bool(functional),
            "ok": bool(edges_ok and functional)})
    return out


if __name__ == "__main__":
    import json
    import sys
    cell = sys.argv[1] if len(sys.argv) > 1 else "sky130_fd_sc_hd__buf_1"
    cl = sys.argv[2] if len(sys.argv) > 2 else "60f"
    print(json.dumps(measure(cell, cl_farad=cl), indent=2))
