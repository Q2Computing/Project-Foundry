# Research: the scientific record behind the proof economy

Every number in the [README](README.md) is reproduced here by a measurement or
a machine-checked theorem, with the method that produced it and the source it
came from. Nothing on this page is asserted; each claim names how to re-run it.

## Methods

**One ruler.** ngspice is the single measurement operator. A custom cell and
the foundry cell are simulated in the same testbench, at the same load, slew,
and corner, from the same open sky130 PDK devices. Delay is a 50 percent to 50
percent propagation measurement; energy is the integral of supply current over
a switching cycle.

**Proof engines, by level.**

| Level | Engine | What is checked | What is trusted |
| --- | --- | --- | --- |
| 1. Exhaustive | ngspice DC and transient sweeps | A cell's output for every digital input, threshold at half VDD; capture, hold, and edge exclusivity for flops | The PDK transistor models |
| 2. Equivalence | Yosys SAT miter, temporal induction for sequential logic | Netlist equals RTL over the whole input space, symbolically | The SAT solver's verdict, parsed with counterexample detection |
| 3. Techmap | Yosys techmap plus structural equivalence | The netlist maps only onto level-1 cells and equals its RTL; a leaf over 64 cells is refused | The proven-cell whitelist |
| 4. Composition | Census plus composition equivalence | The assembly instantiates only proven children and proven glue, and equals the composition of its declared children | Each child's own certificate |

**Evidence that is not proof.** Simulation with test vectors (Icarus,
Verilator) is recorded as conformance evidence and never advances a certificate
by itself. Physical signoff (DRC, LVS, static timing) is a manufacturability
verdict, taken only from a run at the declared target clock.

## The MXFP4 record

Q2's MXFP4 (OCP Microscaling FP4, E2M1) GEMM accelerator is the worked example.
It was certified purely by reference to proven parts. Every block's certificate
carries the content hash of its real proof of record.

| Block | Tier | Proof level |
| --- | --- | --- |
| sky130 inv_1, nand2_1, dfxtp_1 | PDK cell | 1, exhaustive SPICE |
| E2M1 decoder, 32-bit register | component | 3, techmap onto proven cells |
| FP32 normalize, 32-way adder tree, FP32 accumulator | component | 2, equivalence |
| MXFP4 lane multiplier | component | 4, composition |
| MXFP4 dot product | sub-assembly | 4, composition |
| MXFP4 accumulating PE | assembly | 4, composition, plus DRC, LVS, and timing signoff |
| 16 by 16 GEMM tile | assembly | 4, composition |
| MXFP4 GEMM accelerator | system | 4, composition |

**What it cost to produce**, from the portal's analysis records.

| Measure | Value | Source |
| --- | --- | --- |
| Completed proof runs | 23 | portal analysis table |
| Proving compute | 3.724 hours (OpenLane 3.714, Icarus 0.007, Yosys 0.003) | completed minus started, summed |
| Creation span, first request to last completion | 101.72 hours | portal analysis table |
| Machine power | 80 watts | specified |
| Electricity, Vermont residential, September 2026 | 24.44 cents per kWh | see Sources |
| Energy cost, proving-compute basis | 72,811 micro-dollars, about 7.3 cents | theorem energy_compute_uUSD |
| Energy cost, creation-span basis | 1,988,829 micro-dollars, about $1.99 | theorem energy_span_uUSD |

## The Lean proof package

`Q2Market.lean` is a Lean 4 project with 58 theorems over a model that mirrors
the contract's arithmetic exactly. Core kernel only: no mathlib, no
native_decide, no sorry. The axiom audit shows every theorem depends on at most
propext and Quot.sound, and every numeric theorem on no axioms at all. All money
is integer wei or micro-dollars, so no rounding is hidden.

| Section | What is proved | Key result |
| --- | --- | --- |
| 1. Cap invariant | royalty_due = min(price, target minus recovered), zero once recovered; by induction, recovered never exceeds target | Collection is capped at the declared listing gas |
| 2. Rent bound | rent = collected minus cost | rent is at most CAP minus cost, always |
| 3. Free-entry equilibrium | Any price above cost is undercut; the only stable price is cost | Equilibrium rent is zero |
| 4. Production cost | 80 W, 24.44 cents per kWh, measured hours | 7.3 cents and $1.99; both far below the 0.005 ETH cap |
| 5. Manufacturing, make versus buy | A competent buyer pays at most replication cost across all masks | $800 Charter price at $4,000 replication; $6,000 at $30,000 |
| 6. The floor | $100 per mask, SoC down | 66 bps of a shuttle, 0 bps of a mask set; entrants need 40 (team) or 300 (incumbent) masks to break even |
| 7. Capstone | Production versus floor | $98.01 on the first mask, $100 on every later one; replication is 2,011 times production |
| 8. The descent | Physical cost per mask falls with volume; deterrence tightens as the floor falls | 1.2 cents per mask at 1,200 masks, 1.0 cent at a million; the safe-descent ladder |

**The descent ladder**, each row a theorem.

| Floor per mask | Masks per year for $120,000 | Entrant break-even at $4,000 replication |
| --- | --- | --- |
| $100 | 1,201 | 40 |
| $10 | 12,100 | 400 |
| $1 | 122,000 | 4,000 |
| 10 cents | 1,340,000 | 40,000 |

## Invariants the contract enforces

| Invariant | Mechanism |
| --- | --- |
| A listing target can never be raised | No setter exists for recovery_target |
| No listing may declare more than 0.005 ETH | MAX_RECOVERY_TARGET, checked on register and certify |
| The royalty sum cannot wrap | Checked addition; overflow reverts |
| A sold license cannot be repriced, redirected, or stranded | Unit price, foundry, and package commitment are snapshotted into the license at purchase |
| No unit is manufactured from an unreceived design | consume requires a recorded disclosure matching the designer's committed package |
| A competing implementation cannot be listed silently | Same interface requires naming a baseline and settling its remaining recovery |
| A beat is measured, never declared | claim_beat requires a reference to a recorded improvement |
| Value is conserved | Every wei is credited to an owner or refunded; payout is pull-based with the balance zeroed before transfer |

## The bets

Proved: everything in the tables above. Assumed, and where each is tested:

- Elasticity, that volume rises about tenfold as the floor falls tenfold. Tested per rung: the floor drops only when measured volume clears the next rung.
- Interfaces. Beat-or-fork binds whoever claims the exact interface hash; renaming evades it. Canonical interfaces (RISC-V F and D, OCP MX) make renaming costly.
- Certificates are claims. Registration is unverified by design; trust comes from the proof being checkable off chain, re-run by the verifier, or attested.
- Parameters: 24.44 cents per kWh, $3,000 per ETH, replication $4,000 (team) and $30,000 (incumbent), settlement gas 1 cent per mask, a 20 percent Charter fraction, a $120,000 per year target. Change any and the numbers move; the theorems do not.

## Reproduce

```
cd contracts/q2-composition/demo && npm install && node run.mjs   # both economies over the real MXFP4 tree
cd contracts/q2-composition/proofs && lake build && lake env lean Audit.lean   # 58 theorems and the axiom audit
cd contracts/q2-composition && cargo build --release --target wasm32-unknown-unknown   # the contract, on Linux
cargo stylus check --endpoint https://sepolia-rollup.arbitrum.io/rpc
```

## Sources

- [chipIgnite shuttle pricing, $14,950 per project](https://chipfoundry.io/faqs)
- [130 nm wafer and MPW cost, mask set $1 to 2 million](https://anysilicon.com/130nm-wafer-mpw-cost/)
- [First-silicon success at 14 percent, 2024 Wilson Research study](https://semiengineering.com/first-time-silicon-success-plummets/)
- [First-silicon success at 5 percent, 2026 study](https://blogs.sw.siemens.com/verificationhorizons/2025/09/03/why-first-silicon-success-is-getting-harder-for-system-companies/)
- [Vermont residential electricity, 24.44 cents per kWh, September 2026](https://www.electricchoice.com/electricity-prices-by-state/vermont/)
- [Power laws in citation distributions, Scopus](https://link.springer.com/article/10.1007/s11192-014-1524-z)
