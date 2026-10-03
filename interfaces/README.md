# Interface contracts

These are the interface contracts for the open sky130 competition. For each
circuit, a contract gives the I/O interface and an efficiency metric drawn from
a public standard, so anyone can implement it and post a result on the
[witness board](../WITNESS.md). Register a result hash-only: a hash stakes the
claim, so a design stays with its author until they choose to reveal it.

## The standards

Every contract is grounded in a published standard:

- **sky130 PDK standard cells.** The full SkyWater `sky130_fd_sc_hd` logic
  library (open-source, Apache-2.0): 123 contracts (93 combinational gates and
  30 flip-flops/latches), with functions, ports, and sequential behavior taken
  directly from the PDK Liberty and blackbox Verilog.
- **IEEE 754 binary32 (FP32) devices,** per IEEE 754-2019.
- **OCP Microscaling (MX),** per the OCP MX Specification v1.0 (E2M1 elements,
  K=32 blocks, shared E8M0 scale).
- **Generic integer datapath:** textbook, width-parameterized adders, shifters,
  encoders, decoders, multipliers, registers.

See `catalog.json` for the machine-readable list and the per-bucket pages:
[`pdk-standard-cells.md`](pdk-standard-cells.md),
[`ieee754-fp32.md`](ieee754-fp32.md),
[`ocp-mx-microscaling.md`](ocp-mx-microscaling.md),
[`integer-datapath.md`](integer-datapath.md).

How a submission is checked and who signs off is in
[`VERIFICATION.md`](VERIFICATION.md); the authoritative reference models and
their licenses are logged in [`GOLDEN-REFERENCES.md`](GOLDEN-REFERENCES.md).

## Scope

The catalog covers general-purpose, standards-defined compute and logic. It
lists the published interface of each block, not an implementation: no netlists,
GDS, RTL, or testbenches (the witness rail commits a hash instead). Q2 custom
cells, which are not part of the open PDK, and mission-specific physical devices
such as sensors and emitters, are out of scope. The PDK bucket also omits
physical, analog, clock-tree, isolation and fill cells, which are not
implement-a-better-one targets.

## The metric

Submissions are ranked by information-entropy-normalized efficiency against the
primary physical resources (time, space, energy), with information as the
normalizer. Each contract declares its useful output width `n_bits`; a
submission reports `area_um2`, `delay_ns`, `energy_j`. See
[`../WITNESS.md`](../WITNESS.md) for the formula and the honesty ladder
(witnessed, verified, settled).

## How to compete

1. Pick an interface id from `catalog.json` (for example
   `sky130_fd_sc_hd__nand2_1`, `q2_if.fp32_mul`, `q2_if.mxfp4_dot32`,
   `q2_if.rca`).
2. Build an implementation that meets the contract and measure it against the
   open sky130 PDK.
3. Register it hash-only with `tools/attest.mjs` and open a pull request adding
   your `submissions/*.json`. Reveal later to move from witnessed to verified.

A contract is a fixed public target. The board shows a Pareto frontier per
interface, so a catalog certifies a frontier, not a single winner.
