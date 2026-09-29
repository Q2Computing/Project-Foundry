#!/usr/bin/env python3
"""
differentiate.py: tell cells apart in a context.

The foundry ships the same buffer, buf_16, in five sky130 libraries. They are
built from different transistor flavors and sizes, so they trade speed,
switching energy, leakage, and silicon area differently. This bench measures
all five on one ruler and turns the numbers into a choice for a given net.

Per cell, at each load and process corner:
  delay        average of the rising and falling 50%-to-50% delays
  energy       supply energy the cell draws for one full cycle (rise + fall)
  input energy energy the upstream stage spends charging this cell's input
  leakage      static supply current, averaged over input low and input high
  area         the cell's laid-out footprint from its LEF (SIZE x BY y)

The netlists are the foundry's own, vendored in analysis/foundry_cells/ at
pinned commits (SOURCES.json records commit and sha256). Device models come
from the pinned sky130A PDK. Run in the ngspice container:
`python3 analysis/differentiate.py`. Writes results/differentiate.json,
results/differentiate.md, and results/differentiate_trace.json.
"""
import hashlib
import json
import os
import re
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CELLS_DIR = os.path.join(HERE, "foundry_cells")
PDK_ROOT = os.environ.get("PDK_ROOT", "/pdk")
PDK_VERSION = os.environ.get("PDK_VERSION", "0fe599b2afb6708d281543108caf8310912f54af")
MODELS = f"{PDK_ROOT}/libs.tech/ngspice/sky130.lib.spice"
VDD = 1.8
SLEW = "0.05n"
LIBS = ["hd", "hdll", "ls", "ms", "hs"]
LOADS = ["60f", "250f", "1000f"]
CORNERS = ["tt", "ss", "ff"]
REF = "hd"   # the high-density library, the usual default

SOURCES = json.load(open(os.path.join(CELLS_DIR, "SOURCES.json")))
_MEAS = re.compile(r"^\s*(tpdr|tpdf|qsup|qin|vmax|vmin)(\d+)\s*=\s*([-0-9.eE+]+)", re.M)


def _includes():
    return "\n".join(f'.include "{os.path.join(CELLS_DIR, SOURCES[l]["netlist"])}"' for l in LIBS)


def _ngspice(deck, name):
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, name)
        open(sp, "w").write(deck)
        p = subprocess.run(["ngspice", "-b", sp], capture_output=True, text=True, timeout=1200, cwd=d)
        extra = {}
        for f in os.listdir(d):
            if f.endswith(".dat"):
                extra[f] = open(os.path.join(d, f)).read()
    return p.stdout + p.stderr, extra


def transient(corner, load):
    """Every cell in one deck, each with its own supply and its own input source,
    so supply energy and input charge are separable per cell."""
    L = [f"* differentiate: buf_16 x{len(LIBS)} CL={load} corner={corner}",
         f'.lib "{MODELS}" {corner}', _includes(),
         f".param VDD={VDD}", f".param TS={SLEW}", "Vgnd VGND 0 0", "Vnb VNB 0 0", "Vpb VPB 0 {VDD}"]
    meas = []
    for k, l in enumerate(LIBS):
        L += [f"Vin{k} A{k} 0 PWL(0 0  2n 0  '2n+TS' {{VDD}}  12n {{VDD}}  '12n+TS' 0  22n 0)",
              f"Vpwr{k} VPWR{k} 0 {{VDD}}",
              f"X{k} A{k} VGND VNB VPB VPWR{k} O{k} {SOURCES[l]['cell']}",
              f"C{k} O{k} 0 {load}"]
        meas += [f".measure tran tpdr{k} TRIG v(A{k}) VAL='VDD/2' RISE=1 TARG v(O{k}) VAL='VDD/2' RISE=1",
                 f".measure tran tpdf{k} TRIG v(A{k}) VAL='VDD/2' FALL=1 TARG v(O{k}) VAL='VDD/2' FALL=1",
                 f".measure tran qsup{k} INTEG i(Vpwr{k}) FROM=2n TO=22n",
                 f".measure tran qin{k} INTEG i(Vin{k}) FROM=2n TO=12n",
                 f".measure tran vmax{k} MAX v(O{k}) FROM=8n TO=11n",
                 f".measure tran vmin{k} MIN v(O{k}) FROM=18n TO=21n"]
    txt, _ = _ngspice("\n".join(L + [".tran 2p 22n"] + meas + [".end"]) + "\n", "tran.sp")
    vals = {}
    for name, idx, v in _MEAS.findall(txt):
        vals.setdefault(int(idx), {})[name] = float(v)
    out = {}
    for k, l in enumerate(LIBS):
        v = vals.get(k, {})
        if not all(x in v for x in ("tpdr", "tpdf", "qsup", "qin", "vmax", "vmin")):
            raise RuntimeError(f"measurement missing for {l} {corner} {load}:\n{txt[-2000:]}")
        out[l] = {"delay_ps": round((v["tpdr"] + v["tpdf"]) / 2 * 1e12, 2),
                  "rise_ps": round(v["tpdr"] * 1e12, 2), "fall_ps": round(v["tpdf"] * 1e12, 2),
                  "energy_fj": round(abs(v["qsup"]) * VDD * 1e15, 2),
                  "input_energy_fj": round(abs(v["qin"]) * VDD * 1e15, 2),
                  "functional": v["vmax"] > 0.9 * VDD and v["vmin"] < 0.1 * VDD}
    return out


def leakage(corner):
    """Static supply current with the input held low and held high."""
    L = [f"* differentiate leakage corner={corner}", f'.lib "{MODELS}" {corner}', _includes(),
         f".param VDD={VDD}", "Vlo lo 0 0", "Vhi hi 0 {VDD}", "Vgnd VGND 0 0", "Vnb VNB 0 0", "Vpb VPB 0 {VDD}"]
    for k, l in enumerate(LIBS):
        for st in ("lo", "hi"):
            L += [f"V{k}{st} VPWR{k}{st} 0 {{VDD}}", f"X{k}{st} {st} VGND VNB VPB VPWR{k}{st} o{k}{st} {SOURCES[l]['cell']}"]
    L += [".control", "op"] + [f"print v{k}{st}#branch" for k in range(len(LIBS)) for st in ("lo", "hi")] + [".endc", ".end"]
    txt, _ = _ngspice("\n".join(L) + "\n", "leak.sp")
    vals = {m[0]: abs(float(m[1])) for m in re.findall(r"v(\d+(?:lo|hi))#branch\s*=\s*([-0-9.eE+]+)", txt)}
    out = {}
    for k, l in enumerate(LIBS):
        if f"{k}lo" not in vals or f"{k}hi" not in vals:
            raise RuntimeError(f"leakage missing for {l} {corner}:\n{txt[-2000:]}")
        out[l] = {"leak_na": round((vals[f"{k}lo"] + vals[f"{k}hi"]) / 2 * 1e9, 4),
                  "leak_lo_na": round(vals[f"{k}lo"] * 1e9, 4), "leak_hi_na": round(vals[f"{k}hi"] * 1e9, 4)}
    return out


def trace(load="250f", corner="tt"):
    """Rising-edge transient of every cell at one operating point, for the page."""
    L = [f"* differentiate trace CL={load} corner={corner}", f'.lib "{MODELS}" {corner}', _includes(),
         f".param VDD={VDD}", f".param TS={SLEW}", "Vgnd VGND 0 0", "Vnb VNB 0 0", "Vpb VPB 0 {VDD}",
         "Vin A 0 PWL(0 0  2n 0  '2n+TS' {VDD}  12n {VDD}  '12n+TS' 0  22n 0)"]
    for k, l in enumerate(LIBS):
        L += [f"Vpwr{k} VPWR{k} 0 {{VDD}}", f"X{k} A VGND VNB VPB VPWR{k} O{k} {SOURCES[l]['cell']}", f"C{k} O{k} 0 {load}"]
    L += [".control", "tran 2p 3n", "wrdata trace.dat v(A) " + " ".join(f"v(O{k})" for k in range(len(LIBS))), ".endc", ".end"]
    _, files = _ngspice("\n".join(L) + "\n", "trace.sp")
    rows = [list(map(float, r.split())) for r in files["trace.dat"].strip().splitlines()]
    t0, t1 = 1.9e-9, 2.9e-9
    rows = [r for r in rows if t0 <= r[0] <= t1]
    # wrdata writes (t, v) pairs per vector: t, vA, t, vO0, t, vO1, ...
    tr = {"t_ps": [round(r[0] * 1e12, 2) for r in rows], "vin": [round(r[1], 4) for r in rows]}
    for k, l in enumerate(LIBS):
        tr[l] = [round(r[3 + 2 * k], 4) for r in rows]
    return {"load": load, "corner": corner, "slew": SLEW, "vdd": VDD, "window_ps": [t0 * 1e12, t1 * 1e12], "trace": tr}


def devices(lib):
    """Transistor flavors, widths, and counts from the vendored netlist."""
    txt = open(os.path.join(CELLS_DIR, SOURCES[lib]["netlist"])).read()
    agg = {}
    for model, w, l in re.findall(r"(sky130_fd_pr__\w+)\s+w=([0-9.eE+]+)u\s+l=([0-9.eE+]+)u", txt):
        key = (model, round(float(w) * 1e-6, 3), round(float(l) * 1e-6, 3))
        agg[key] = agg.get(key, 0) + 1
    return [{"model": m, "w_um": w, "l_um": l, "count": n} for (m, w, l), n in sorted(agg.items())]


def break_even(ref, other):
    """Switching rate (full cycles per second) above which `other` uses less total
    energy than `ref`. Total power of a net = cycles/s x energy per cycle + leakage
    x VDD. None when `other` never uses less (it spends more per cycle and more at rest)."""
    de = (ref["energy_fj"] + ref["input_energy_fj"]) - (other["energy_fj"] + other["input_energy_fj"])
    dp = (other["leak_na"] - ref["leak_na"]) * 1e-9 * VDD
    if de <= 0:
        return None
    return dp / (de * 1e-15) if dp > 0 else 0.0


def main():
    meas = {c: {ld: transient(c, ld) for ld in LOADS} for c in CORNERS}
    leak = {c: leakage(c) for c in CORNERS}
    cells = {}
    for l in LIBS:
        cells[l] = {"cell": SOURCES[l]["cell"], "area_um2": SOURCES[l]["area_um2"],
                    "lef_size_um": SOURCES[l]["lef_size_um"], "devices": devices(l),
                    "netlist_sha256": SOURCES[l]["sha256"], "source": SOURCES[l]["source"],
                    "commit": SOURCES[l]["commit"]}
    rows = []
    for c in CORNERS:
        for ld in LOADS:
            for l in LIBS:
                m = dict(meas[c][ld][l]); m.update(leak[c][l])
                m["edp"] = round(m["energy_fj"] * m["delay_ps"] / 1000, 3)   # fJ x ns
                rows.append({"lib": l, "corner": c, "load": ld, **m})
    idx = {(r["lib"], r["corner"], r["load"]): r for r in rows}
    for r in rows:
        ref = idx[(REF, r["corner"], r["load"])]
        r["vs_hd"] = {"delay_pct": round(100 * (r["delay_ps"] / ref["delay_ps"] - 1), 1),
                      "energy_pct": round(100 * (r["energy_fj"] / ref["energy_fj"] - 1), 1),
                      "input_energy_pct": round(100 * (r["input_energy_fj"] / ref["input_energy_fj"] - 1), 1),
                      "edp_pct": round(100 * (r["edp"] / ref["edp"] - 1), 1),
                      "leak_x": round(r["leak_na"] / ref["leak_na"], 1),
                      "area_pct": round(100 * (cells[r["lib"]]["area_um2"] / cells[REF]["area_um2"] - 1), 1)}
        be = break_even(ref, r) if r["lib"] != REF else None
        r["break_even_cycles_per_s"] = None if be is None else float(f"{be:.3g}")

    bench = open(os.path.abspath(__file__), "rb").read()
    bundle = {"schema": "q2.differentiate.v1", "pdk": "sky130A", "pdk_version": PDK_VERSION,
              "bench_sha256": hashlib.sha256(bench).hexdigest(), "vdd": VDD, "slew": SLEW,
              "loads": LOADS, "corners": CORNERS, "reference": REF, "cells": cells, "rows": rows}
    blob = json.dumps(bundle, sort_keys=True, separators=(",", ":"))
    h = "0x" + hashlib.sha256(blob.encode()).hexdigest()
    record = {"artifact_hash": h, "label": 1, "context": 16,
              "meaning": "label 1 = measurement record, no improvement claim; context 16 = drive strength of the cells compared",
              "call": f"record({h}, 1, 16)"}
    out = {"record": record, "bundle": bundle}
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "results", "differentiate.json"), "w"), indent=1)
    json.dump(trace(), open(os.path.join(ROOT, "results", "differentiate_trace.json"), "w"))

    md = ["# buf_16 across the five sky130 libraries", "",
          f"PDK sky130A {PDK_VERSION}, VDD {VDD} V, input slew {SLEW}. Reference: sky130_fd_sc_{REF}__buf_16.",
          f"Record: `{record['call']}`", ""]
    for c in CORNERS:
        for ld in LOADS:
            md += [f"## {c}, load {ld}", "",
                   "| library | delay ps | energy fJ | input energy fJ | leakage nA | area um2 | delay vs hd | energy vs hd | leakage vs hd | break-even cycles/s |",
                   "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
            for l in LIBS:
                r = idx[(l, c, ld)]; v = r["vs_hd"]; be = r["break_even_cycles_per_s"]
                md.append(f"| {l} | {r['delay_ps']} | {r['energy_fj']} | {r['input_energy_fj']} | {r['leak_na']} | "
                          f"{cells[l]['area_um2']} | {v['delay_pct']:+}% | {v['energy_pct']:+}% | {v['leak_x']}x | "
                          f"{'' if l == REF else ('never' if be is None else f'{be:.3g}')} |")
            md.append("")
    open(os.path.join(ROOT, "results", "differentiate.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
