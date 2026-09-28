#!/usr/bin/env python3
"""
Deterministic antenna + latchup check.

This runs the foundry's *published* deterministic rules against a submitted
object and reports whether it signs off. It is the public, re-checkable half of
Project Foundry's measurement loop.

The object it checks is a MEASUREMENT ABSTRACTION (see objects/current.json): it
carries only the areas and distances the rule needs, never the routed geometry,
the design method, or the dopant recipe that produced them. That is the whole
trick — a public CI run can verify the boundary INSIGHT ("this antenna ratio is
clean for sky130") while the private IP that achieved it never leaves its owner.
The lower bound is a property of the process; the way you reach it can stay
yours.

The arithmetic below is exactly what a DRC antenna/latchup deck computes on
extracted areas. It is deliberately structured so it can be swapped for a real
KLayout antenna runset (KLAYOUT_ANTENNA_RUNSET) or a Magic latchup check on a
GDS with no change to the object contract or the on-chain mapping.
"""
import argparse, hashlib, json, os, sys

# The foundry's published deterministic limits, per process. Representative
# values; the exact per-layer antenna ratios live in each PDK's DRC deck. They
# are per-PDK BY DESIGN: the clean lower bound is unique to the environment.
PDK_RULES = {
    "sky130": {"label": "SkyWater sky130 (130 nm)", "antenna_ratio": 400.0, "tap_max_um": 15.0, "context": 130},
    "gt3":    {"label": "GT3 GAAFET (3 nm, illustrative)", "antenna_ratio": 180.0, "tap_max_um": 7.0, "context": 3},
}


def content_hash(measurement: dict) -> str:
    """Canonical, non-invertible commitment to the measurement (matches the
    viewer and the on-chain anchor's artifact_hash)."""
    canon = json.dumps(measurement, sort_keys=True, separators=(",", ":"))
    return "0x" + hashlib.sha256(canon.encode()).hexdigest()


def check(obj: dict) -> dict:
    pdk = obj.get("pdk", "sky130")
    if pdk not in PDK_RULES:
        raise SystemExit(f"unknown pdk: {pdk!r} (known: {', '.join(PDK_RULES)})")
    rule = PDK_RULES[pdk]
    m = obj["measurement"]

    # metal area: given directly, or derived from the arm abstraction.
    if "metal_area_um2" in m:
        metal_area = float(m["metal_area_um2"])
    else:
        w = float(m["metal_width_um"])
        metal_area = sum(float(a) for a in m["arms_um"]) * w + float(m.get("trunk_area_um2", 2.5))
    gate_area = float(m["gate_area_um2"])
    tap = float(m["tap_distance_um"])

    ratio = metal_area / gate_area
    antenna_violation = ratio > rule["antenna_ratio"]
    latchup_violation = tap > rule["tap_max_um"]
    signoff = not (antenna_violation or latchup_violation)

    measurement = {
        "pdk": pdk,
        "structure": obj.get("structure", "unknown"),
        "metal_area_um2": round(metal_area, 3),
        "gate_area_um2": round(gate_area, 3),
        "antenna_ratio": round(ratio, 2),
        "antenna_rule": rule["antenna_ratio"],
        "tap_distance_um": tap,
        "tap_rule": rule["tap_max_um"],
        "antenna_violation": antenna_violation,
        "latchup_violation": latchup_violation,
        "signoff": "PASS" if signoff else "FAIL",
    }
    # label: coarse outcome code (0 clean, 1 antenna, 2 latchup, 3 both) — the
    # opaque label the public anchor records alongside the content hash.
    label = (1 if antenna_violation else 0) | (2 if latchup_violation else 0)
    return {
        "rule_label": rule["label"],
        "measurement": measurement,
        "content_hash": content_hash(measurement),
        "label": label,
        "context": rule["context"],
        "signoff": signoff,
    }


def emit(res: dict) -> None:
    m = res["measurement"]
    print(f"== Project Foundry deterministic check :: {res['rule_label']} ==")
    print(f"  structure           {m['structure']}")
    print(f"  metal_area          {m['metal_area_um2']} um^2")
    print(f"  gate_area           {m['gate_area_um2']} um^2")
    print(f"  antenna_ratio       {m['antenna_ratio']} : 1   (rule {m['antenna_rule']})")
    print(f"  tap_distance        {m['tap_distance_um']} um   (rule {m['tap_rule']})")
    print(f"  route__antenna_violation__count      {1 if m['antenna_violation'] else 0}")
    print(f"  latchup__tap_distance_violation      {1 if m['latchup_violation'] else 0}")
    print(f"  signoff             {m['signoff']}")
    print(f"  content_hash        {res['content_hash']}")
    print(f"  anchor call         record({res['content_hash']}, {res['label']}, {res['context']})")

    # GitHub annotations — surfaced near-real-time in the run UI.
    if m["antenna_violation"]:
        print(f"::error title=Antenna violation::antenna_ratio {m['antenna_ratio']} exceeds "
              f"the {res['rule_label']} rule of {m['antenna_rule']}. Back the metal off to find the clean edge.")
    if m["latchup_violation"]:
        print(f"::error title=Latchup violation::tap_distance {m['tap_distance_um']} um exceeds "
              f"the {res['rule_label']} maximum of {m['tap_rule']} um. Move a tap closer.")

    # Job summary (markdown) for the run page.
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### Deterministic check — {res['rule_label']}\n\n")
            f.write("| metric | value | rule | verdict |\n|---|---|---|---|\n")
            f.write(f"| antenna ratio | {m['antenna_ratio']} : 1 | {m['antenna_rule']} | "
                    f"{'❌ VIOLATION' if m['antenna_violation'] else '✅ clean'} |\n")
            f.write(f"| tap distance | {m['tap_distance_um']} µm | {m['tap_rule']} µm | "
                    f"{'❌ VIOLATION' if m['latchup_violation'] else '✅ clean'} |\n")
            f.write(f"\n**Signoff: {m['signoff']}**\n\n")
            f.write(f"`content_hash` `{res['content_hash']}`  \n")
            f.write(f"`record({res['content_hash']}, {res['label']}, {res['context']})`\n")

    # Step outputs for downstream jobs (e.g. an on-chain anchor step).
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"signoff={'pass' if res['signoff'] else 'fail'}\n")
            f.write(f"content_hash={res['content_hash']}\n")
            f.write(f"label={res['label']}\n")
            f.write(f"context={res['context']}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic antenna/latchup check")
    ap.add_argument("object", nargs="?", default="objects/current.json", help="path to the object spec")
    ap.add_argument("--out", default="results.json", help="where to write the machine result")
    ap.add_argument("--fail-on-violation", action="store_true",
                    help="exit non-zero on any violation (the error-reporting protocol)")
    args = ap.parse_args()

    with open(args.object, encoding="utf-8") as f:
        obj = json.load(f)
    res = check(obj)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    emit(res)

    if args.fail_on_violation and not res["signoff"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
