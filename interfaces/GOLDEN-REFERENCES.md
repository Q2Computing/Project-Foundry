# Golden references — research log

Authoritative, openly-licensed reference models this competition checks against.
Only permissively-licensed references are usable, because the competition and
its harness are public. Dated findings; this log grows as references are vetted.

## Vetted

### sky130 PDK functional Verilog — IN USE
- **Scope:** every `sky130_fd_sc_hd` standard-cell contract.
- **License:** Apache-2.0 (SkyWater / Google open PDK).
- **Status:** mounted in the reference flow; functions, ports, and sequential
  behavior for the 123 published cell contracts were extracted directly from the
  Liberty and blackbox Verilog. This is the reference for the equivalence check.

### Berkeley HardFloat — SELECTED for the IEEE 754 bucket
- **What:** parameterized Verilog for IEEE 754 binary floating-point (half,
  single, double, quad), by John R. Hauser. Conforms to IEEE 754 including all
  rounding modes, exception flags, subnormals, and special values.
- **License:** BSD (3-clause) — permissive; compatible with a public harness.
  Confirm the exact LICENSE text at vendor time.
- **Testing:** HardFloat's testbenches depend on **Berkeley TestFloat**
  (`testfloat_gen`), which depends on **Berkeley SoftFloat** — the de-facto
  gold-standard FP conformance vector generator.
- **Plan:** vendor HardFloat (pinned) as the FP golden reference and drive the
  `q2_if.fp32_*` contracts with TestFloat vectors (subnormals / signed-zero /
  inf / NaN). Until vendored, FP contracts validate against the IEEE 754-2019
  definition directly.
- Source: https://jhauser.us/arithmetic/HardFloat.html

## Candidates (not yet vetted)

- **RISC-V reference** (Spike / `riscv-isa-sim`, riscv-arch-test, RVFI) — golden
  ISA model for an eventual RV32I integer-datapath / core bucket. License and
  scope review pending.
- **FloPoCo** — generator for correctly-specified arithmetic operators; useful
  as a cross-check reference for non-754 FP approximations. License review
  pending.

## Rule

A reference is only adopted after its license is confirmed compatible with
public redistribution and its version is pinned. A contract names its golden
reference in `catalog.json`; see `VERIFICATION.md` for how it is applied.
