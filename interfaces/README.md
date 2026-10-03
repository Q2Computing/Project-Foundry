# Interface contracts — compete against these

This catalog publishes **interface contracts**: the public, standards-grounded
I/O contract and metric for a circuit, so anyone can build an implementation and
post a result on the [witness board](../WITNESS.md). A contract is the *challenge
spec*, not a design. Nothing here is a Q2 implementation, a netlist, or a
testbench — those stay private and are committed hash-only through the witness
rail.

## What is published here

Only generic building blocks whose interface is defined by a public standard or
textbook function:

- **sky130 PDK standard cells** — the full SkyWater `sky130_fd_sc_hd` logic
  library (open-source, Apache-2.0): 123 contracts (93 combinational gates + 30
  flip-flops/latches), with functions, ports, and sequential behavior extracted
  directly from the PDK Liberty and blackbox Verilog.
- **IEEE 754 binary32 (FP32) devices** — per IEEE 754-2019.
- **OCP Microscaling (MX)** — per the OCP MX Specification v1.0 (E2M1, K=32
  blocks, shared E8M0 scale).
- **Generic integer datapath** — textbook, width-parameterized adders,
  shifters, encoders, decoders, multipliers, registers.

How a submission is checked and who signs off is in
[`VERIFICATION.md`](VERIFICATION.md); the authoritative reference models and
their licenses are logged in [`GOLDEN-REFERENCES.md`](GOLDEN-REFERENCES.md).
Physical, analog, clock-tree, isolation and fill cells are deliberately omitted
from the PDK bucket — they are not implement-a-better-one targets.

See `catalog.json` for the machine-readable list and the per-bucket pages:
[`pdk-standard-cells.md`](pdk-standard-cells.md),
[`ieee754-fp32.md`](ieee754-fp32.md),
[`ocp-mx-microscaling.md`](ocp-mx-microscaling.md),
[`integer-datapath.md`](integer-datapath.md).

## What is never published here

- **Mission-specific physical devices** — any sensor or emitter (for example a
  LIDAR sensor or a UV laser emitting diode), and any integrated circuit built
  for a particular mission. The catalog is limited to general-purpose,
  standards-defined compute and logic.
- **Q2 implementations** — no netlists, GDS, RTL, or testbenches. The witness
  rail commits only a hash, so a design is proven without being disclosed.
- **Q2 custom cells** — cells authored by Q2 (not part of the open PDK) are IP
  and are not listed as public contracts.

## The metric

Submissions are ranked by information-entropy-normalized efficiency against the
primary physical resources — time, space, energy — with information as the
normalizer. Each contract declares its useful output width `n_bits`; a
submission reports `area_um2`, `delay_ns`, `energy_j`. See [`../WITNESS.md`](../WITNESS.md)
for the exact formula and the honesty ladder (witnessed -> verified -> settled).

## How to compete

1. Pick an interface id from `catalog.json` (e.g. `sky130_fd_sc_hd__nand2_1`,
   `q2_if.fp32_mul`, `q2_if.mxfp4_dot32`, `q2_if.rca`).
2. Build an implementation that meets the contract and measure it against the
   open sky130 PDK.
3. Register it hash-only with `tools/attest.mjs` and open a PR adding your
   `submissions/*.json`. Your design never leaves your machine; reveal later to
   move from *witnessed* to *verified*.

A contract is a fixed target, not a claim about who holds the frontier. The
board shows a Pareto frontier per interface, so a catalog certifies a frontier,
not a single winner.
