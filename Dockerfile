FROM ubuntu:24.04
# Self-contained SPICE measurement environment for the EDP assessment.
# ngspice is the single measurement operator; python drives the sweep and
# builds the report. The sky130 PDK is mounted at /pdk (local: host ~/.ciel;
# CI: fetched from the open SkyWater PDK via ciel).
RUN apt-get update && apt-get install -y --no-install-recommends \
      ngspice python3 python3-numpy ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ENV PDK_ROOT=/pdk
WORKDIR /work
