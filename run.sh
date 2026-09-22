#!/usr/bin/env bash
# Local driver for the EDP system. Runs the same ngspice measurement the CI
# oracle runs, in a container, against the local sky130 PDK.
#
#   ./run.sh assess          # re-measure committed candidates vs the part (gate)
#   ./run.sh propose         # search the design grid, write survivors to manifest
#   ./run.sh anchor          # prepare disclosure-safe provenance records
#
# Override the PDK location with PDK=/path/to/sky130A ./run.sh ...
set -euo pipefail
CMD="${1:-assess}"; shift || true
DEF="$HOME/.ciel/ciel/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A"
PDK="${PDK:-$DEF}"
test -f "$PDK/libs.tech/ngspice/sky130.lib.spice" || {
  echo "sky130A not found at PDK=$PDK (set PDK=/path/to/sky130A)"; exit 1; }

docker build -q -t q2edp . >/dev/null
# GEMINI_API_KEY / GEMINI_MODEL are forwarded for `propose --backend llm`
# (a free key from https://aistudio.google.com works). They are ignored by the
# grid backend and by assess/anchor.
run() { docker run --rm -e GEMINI_API_KEY -e GEMINI_MODEL \
          -v "$PDK:/pdk:ro" -v "$PWD:/work" -w /work q2edp "$@"; }

case "$CMD" in
  assess)   run python3 tools/assess.py --gate "$@" ;;
  propose)  run python3 tools/propose.py --measure "$@" ;;  # measured survivors
  generate) run python3 tools/propose.py "$@" ;;            # raw proposals (for compare)
  compare)  run python3 tools/compare.py "$@" ;;
  proof)    run python3 tools/proof.py "$@" ;;        # raw head-to-head ngspice proof
  anchor)   run python3 tools/anchor.py "$@" ;;
  *) echo "usage: run.sh {assess|propose|generate|compare|proof|anchor} [args]"; exit 2 ;;
esac
