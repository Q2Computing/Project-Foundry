FROM ubuntu:24.04
# Self-contained environment for the EDP loop.
# ngspice is the measurement operator (used by the oracle and the local
# pre-filter). google-genai is the OPTIONAL Gemini generator backend, used only
# by `propose.py --backend llm` for local generation, never by CI. The sky130
# PDK is mounted at /pdk (local: host ~/.ciel; CI does not use this image).
RUN apt-get update && apt-get install -y --no-install-recommends \
      ngspice python3 python3-numpy python3-pip ca-certificates \
    && pip3 install --no-cache-dir --break-system-packages google-genai \
    && rm -rf /var/lib/apt/lists/*
ENV PDK_ROOT=/pdk
WORKDIR /work
