#!/usr/bin/env bash
# Runs INSIDE the q2edp (ngspice + OSDI) container, cwd = this dir mounted at /work.
# Compiles the GAA BSIM-CMG to OSDI, transforms the GT3 cards, runs the decks.
# Dependencies must already be fetched under ./build by run-gt3.sh.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
B="$HERE/build"
# 1. compile the GAA-capable BSIM-CMG Verilog-A to OSDI (build in its own dir; it
#    `include`s sibling files, so cd in first)
chmod +x "$B/openvaf"
( cd "$B/VA-Models/code/bsimcmg/vacode" && "$B/openvaf" bsimcmg.va && cp bsimcmg.osdi "$B/bsimcmg_gaa.osdi" )
# 2. map the GT3 HSPICE cards onto the OSDI module
bash "$HERE/transform_gt3.sh" "$B/GT3/models/hspice" "$B"
# 3. run the calibration decks
cp "$HERE"/gt3_delay.sp "$HERE"/gt3_leak.sp "$HERE"/gt3_energy.sp "$B"/
cd "$B"
for d in gt3_delay gt3_leak gt3_energy; do
  echo "=== $d ==="
  ngspice -b "$d.sp" 2>&1 | grep -iE "tphl|tplh|i\(vp|q_rv|q_lv"
done
echo "done. Derived constants and the sky130 comparison are in gt3_calibration.json"
