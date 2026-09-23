#!/usr/bin/env bash
# Map GT3 BSIM-CMG (HSPICE level 72) model cards onto the OSDI bsimcmg_va module.
#   .model X nmos/pmos  ->  .model X bsimcmg_va
#   drop  +level=72
#   add   +TYPE=1  (nmos) / +TYPE=-1 (pmos)   [the OSDI model ignores GT3's DEVTYPE]
# usage: transform_gt3.sh <gt3 models/hspice dir> <output dir>
set -euo pipefail
SRC="$1"; OUT="$2"
for flav in rvt lvt; do
  sed -e "s/\.model nmos_${flav} nmos/.model nmos_${flav} bsimcmg_va\n+TYPE=1/" \
      -e "s/\.model pmos_${flav} pmos/.model pmos_${flav} bsimcmg_va\n+TYPE=-1/" \
      -e "/^+level=72/d" \
      "$SRC/gt3_${flav}.mod" > "$OUT/gt3_${flav}_osdi.mod"
done
echo "transformed rvt + lvt cards into $OUT"
