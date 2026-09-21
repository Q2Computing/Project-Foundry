#!/usr/bin/env python3
"""
anchor.py: disclosure-safe provenance for verified improvements.

Turns the oracle's winners into records for the q2-anchor Stylus contract:
    record(bytes32 artifact_hash, uint16 label, uint16 context)

For each unique candidate that BEAT the foundry part, we commit a hash over a
canonical bundle (the design's canonical netlist form + the measured metrics +
the operating point + the PDK version). The hash is the on-chain artifact; the
netlist itself need never be published. A holder of the netlist can recompute
the hash and verify; without it the record is an opaque commitment. That is the
whole point, anchor the *fact* of a unique, measured improvement without
exposing the IP that produced it.

label  (uint16): basis points of EDP improvement vs the part, capped at 65535.
context(uint16): the foundry part's drive strength (e.g. buf_16 -> 16).

This does NOT transact. It emits the call arguments; submitting on-chain uses
the user's funded key, an explicit and irreversible step.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import candidate as C

PDK_VER = os.environ.get("SKY130_VERSION", "0fe599b2afb6708d281543108caf8310912f54af")


def context_from_baseline(cell):
    m = re.search(r"__\w+?_(\d+)$", cell)
    return int(m.group(1)) if m else 0


def bundle_hash(cand, spec, op, baseline):
    """sha256 over the canonical, reproducible provenance bundle -> bytes32."""
    payload = {
        "schema": "q2.edp.provenance.v1",
        "pdk": "sky130A",
        "pdk_version": PDK_VER,
        "baseline": baseline["cell"],
        "operating_point": op,
        "design_canonical": C.canonical(spec),   # private input to the commitment
        "measured": {
            "tpd_ns": round(cand["tpd_ns"], 6),
            "energy_fj": round(cand["energy_fj"], 4),
            "area_um": round(cand["area_um"], 4),
            "edp": round(cand["edp"], 6),
        },
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "0x" + hashlib.sha256(blob.encode()).hexdigest(), payload


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else "results/leaderboard.json"
    specs_path = sys.argv[2] if len(sys.argv) > 2 else "candidates/manifest.json"
    outdir = "provenance"
    os.makedirs(outdir, exist_ok=True)

    with open(board) as fh:
        rep = json.load(fh)
    with open(specs_path) as fh:
        manifest = json.load(fh)
    cand_list = manifest["candidates"] if isinstance(manifest, dict) else manifest
    spec_by_hash = {C.design_hash(m["spec"]): m["spec"] for m in cand_list}

    base = rep["baseline"]
    op = rep["operating_point"]
    ctx = context_from_baseline(base["cell"])
    records = []
    for c in rep["candidates"]:
        if not c.get("beats_baseline"):
            continue
        spec = spec_by_hash.get(c["hash"])
        if spec is None:
            continue
        gain_pct = (base["edp"] - c["edp"]) / base["edp"] * 100.0
        label = max(0, min(65535, round(gain_pct * 100)))  # basis points
        ahash, payload = bundle_hash(c, spec, op, base)
        rec = {
            "artifact_hash": ahash,
            "label": label,
            "context": ctx,
            "note": f"custom driver beats {base['cell']} @ {op['load']}: "
                    f"EDP {gain_pct:+.1f}% (disclosure-safe: hash commits the "
                    f"design; netlist not published)",
            "call": f"record({ahash}, {label}, {ctx})",
        }
        with open(os.path.join(outdir, f"anchor-{ahash[2:10]}.json"), "w") as fh:
            json.dump({"record": rec, "bundle": payload}, fh, indent=2)
        records.append(rec)

    with open(os.path.join(outdir, "manifest.json"), "w") as fh:
        json.dump({"contract": "q2-anchor",
                   "abi": "record(bytes32,uint16,uint16)",
                   "records": records}, fh, indent=2)
    print(f"prepared {len(records)} disclosure-safe anchor record(s) in {outdir}/")
    for r in records:
        print("  " + r["call"])
    if not records:
        print("  (no verified improvements to anchor)")


if __name__ == "__main__":
    main()
