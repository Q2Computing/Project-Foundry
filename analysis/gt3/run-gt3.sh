#!/usr/bin/env bash
# GT3 3nm calibration. Fetches deps on the host (needs git + curl), then computes
# in the q2edp ngspice+OSDI container. From repo root: analysis/gt3/run-gt3.sh
# Override the image with Q2EDP=<image>; the container is built by ../../run.sh.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
B="$HERE/build"; mkdir -p "$B"
Q2EDP="${Q2EDP:-q2edp}"

# OpenVAF: Verilog-A -> OSDI compiler (prebuilt linux amd64)
if [ ! -f "$B/openvaf" ]; then
  curl -fsSL -o "$B/openvaf.tar.gz" \
    https://openva.fra1.cdn.digitaloceanspaces.com/openvaf_devel_linux_amd64.tar.gz
  tar xzf "$B/openvaf.tar.gz" -C "$B" && chmod +x "$B/openvaf"
fi
# BSIM-CMG Verilog-A (latest vacode supports GEOMOD=5 / GAA nanosheet)
[ -d "$B/VA-Models" ] || git clone --depth 1 https://github.com/dwarning/VA-Models.git "$B/VA-Models"
# GT3 3nm GAAFET PDK
[ -d "$B/GT3" ] || git clone --depth 1 https://github.com/azadnaeemi/GT3.git "$B/GT3"

# compute in the ngspice+OSDI container
docker run --rm -v "$HERE":/work -w /work "$Q2EDP" bash calibrate.sh
