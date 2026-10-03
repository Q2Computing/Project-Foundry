# Verification, validation, and QA/QC

How a submission to an interface contract is checked, and who signs off. The
competition is only meaningful if the oracle is objective and independent of the
thing it judges, so the function check and the cost measurement are separated,
and the final human sign-off is separated from the automation.

## 1. Golden reference model (per bucket)

A contract names a **golden reference** — the authoritative behavior a
submission must match. It is never a Q2 design.

| Bucket | Golden reference |
|---|---|
| sky130 PDK standard cells | the cell's own PDK functional Verilog / `.lib` (Apache-2.0), mounted in the flow |
| IEEE 754 binary32 | Berkeley HardFloat RTL + Berkeley TestFloat / SoftFloat vectors (see `GOLDEN-REFERENCES.md`) |
| OCP Microscaling (MX) | the OCP MX v1.0 numeric definition (E2M1 decode, K=32 block, shared E8M0) |
| integer datapath | a width-parameterized reference model of the stated function |

## 2. Validation pipeline (the oracle)

1. **Functional equivalence.** The submission is proven to implement the
   contract function, not merely to pass a few vectors:
   - combinational cells and datapath: a SAT **miter / logic-equivalence check**
     (Yosys `equiv`) against the golden reference;
   - sequential cells: sequential equivalence (state-matched) against the
     reference flip-flop / latch behavior;
   - FP: equivalence or exhaustive-vector co-simulation against HardFloat driven
     by TestFloat, including subnormals, signed zero, infinities, and NaN.
2. **Physical signoff on sky130.** Synthesis -> place-and-route -> **DRC, LVS,
   and static timing** against the open sky130 PDK (Yosys, OpenROAD, Magic,
   Netgen, OpenLane/LibreLane). This produces the measured `area_um2`,
   `delay_ns`, and `energy_j`.
3. **Metric.** Those measurements feed the information-entropy-normalized
   efficiency score in [`../WITNESS.md`](../WITNESS.md).

Steps 1 and 2 are the two axes: a result is both *correct* (equivalent to the
golden reference) and *costed* (measured at signoff). One without the other does
not rank.

## 3. QA/QC sign-off (who decides)

Automation proposes; humans dispose. No agent approves its own work.

1. **Agent conformance** — the automated pipeline above runs and must pass.
2. **Independent re-run** — the equivalence check and signoff are reproduced by
   an oracle independent of the producer (different harness, same result).
3. **Human sign-off** — a human reviewer confirms the evidence before an entry
   is published as more than a claim.
4. **Final authorization** — settling an entry on-chain is authorized by the
   principal from their own wallet, once activation returns.

## 4. Honesty ladder (what a published entry means)

- **witnessed** — a wallet signed the hash of a design + result. A signed claim;
  the design stays private. Owners can run steps 1–2 locally and commit hash-only.
- **verified** — the owner reveals the design and steps 1–2 are reproduced
  against the open PDK / golden reference by the independent oracle.
- **settled** — recorded on-chain after human sign-off, when Stylus activation
  returns.

The leaderboard currently shows **witnessed** claims only. A contract is a fixed
public target; nothing here asserts that Q2 holds any frontier.
