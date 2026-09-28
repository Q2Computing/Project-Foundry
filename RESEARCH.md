# Research: the scientific record behind the proof economy

Written to be read from the beginning. No prior familiarity with the literature
is assumed. Every number in the [README](README.md) is reproduced here by a
measurement or a machine-checked theorem, with the method that produced it and
the source it came from.

## 1. Introduction

This page is written for a reader who has not seen the literature. It builds the argument in order. Section 2 states the economic instrument. Sections 3 and 4 supply the two pieces of background the instrument rests on: how digital silicon is designed and verified, and why floating-point arithmetic is the worked example. Section 5 gives the data, every number with its source. Section 6 analyzes the data with machine-checked theorems. Section 7 draws the conclusion. Nothing here is asserted without a way to re-run it.

**The problem.** A chip is a hierarchy of blocks. Before a design is sent to a foundry, each block and the whole assembly must be shown correct, because a mask set at a modern node costs one to two million dollars and a failed first spin is a second mask set. Industry surveys put first-silicon success at 14 percent in 2024 and 5 percent in 2026. Verification is the largest cost in the flow, and today it is repeated: every company that uses an adder, a floating-point unit, or a register file re-verifies its own copy, in private, and the work is thrown away when the project ends.

**The observation.** A proof of a block, once produced, does not depend on who uses the block. If the proof is public and content-addressed, a second team can inherit it instead of repeating it, and a larger system can be proved by reference to the proofs of its parts without ever opening the parts. Verification becomes a shared asset rather than a private expense.

**The claim.** Q2 Computing has built the first instrument that makes this inheritance a market: a proof is a certificate, certificates license into larger proofs at cost and into manufactured silicon at a fixed floor, and both licenses settle on a public chain. The rest of this page shows what was built, measures what it cost, proves what the instrument guarantees, and states what follows for anyone who tries to compete with it.

## 2. The proof economy

A **certificate** is an on-chain record naming a block by the content hash of its design, the content hash of its interface, the level at which it was proved, and the content hash of the proof of record. A certificate for a composed block additionally names the certificates of its children and a binding hash over their interfaces. Anyone can check that the proof of record exists and matches; nobody needs the design to do so.

Every certificate carries two licenses. The protocol takes nothing from either.

| License | What it grants | Price rule | Who pays |
| --- | --- | --- | --- |
| Reference | The right to name this certificate as a child of a larger proof | Recovers only the gas the lister spent to list, capped at a lister-declared target of at most 0.005 ETH, then free forever. Foundry PDK primitives are free from the start. | The abstraction one level up, for its direct children only. The recursion beneath is never charged. |
| Manufacturing | The right to include the design in a fabricated system on chip | A floor of $100 per mask set, covering every certified block in that mask, walked down as adoption grows | The manufacturer. The design is disclosed only to a designer-named foundry, which must prove receipt of the committed package before any unit is consumed. The licensee never downloads the file. |

**Beat or fork.** Anyone may list a competing implementation of an existing interface, but must name the block it beats and settle whatever remains of that block's listing cost. The prior lister is made whole. The improvement must be a recorded measurement, never a declaration.

The public site carries that rule run end to end on one sky130 standard cell, the foundry's buf_16 driver. An agent proposes fabricable candidate cells (gate areas and threshold-voltage mask mixes inside the foundry's energy band), an oracle in GitHub Actions re-measures the baseline and every candidate in one ngspice bench on the open PDK, and each verified, unique win is hashed for the anchor contract to record with its improvement label. The best in-band candidate lowered energy-delay by 22 percent against buf_16 at the same finger count with no extra transistors, and 22 of 30 fabricable mask combinations beat the foundry ladder inside its own energy-per-cycle band. Those measurements are evidence for the label; the cell's correctness is a separate level-1 proof.

**Three contracts** on Arbitrum Stylus carry the economy. The verifier re-runs a bounded proof on chain. The anchor records a content-addressed commitment of an off-chain proof. The composition contract certifies a system by reference to child certificates and settles both licenses. Their invariants are listed in Section 6.

## 3. VLSI and digital design

Very large scale integration is the discipline of building a circuit of billions of transistors so that it does exactly what it is specified to do. The design is a hierarchy, and the proof economy prices each tier of that hierarchy separately.

| Tier | What it is | How it is proved |
| --- | --- | --- |
| Device | A transistor, described by the foundry's process design kit (PDK) as a SPICE model | Characterized by measurement; the model is trusted |
| Cell | A handful of transistors wired into a gate: an inverter, a NAND, a flip-flop | Level 1, exhaustive: simulate every input in SPICE and compare against the truth table |
| Component | Tens to hundreds of cells forming an adder, a decoder, a register | Level 2 or 3: SAT equivalence of netlist to RTL, or techmap onto proven cells |
| Assembly | Components wired into a multiplier, a dot product, a processing element | Level 4, composition: every part is certified, and the glue is proved equal to the declared composition |
| System | Assemblies wired into an accelerator or a processor | Level 4 again; the ladder is closed under composition |

**Why verification cost explodes.** An exhaustive check of a block with n input bits takes 2 to the power n cases. An 8-bit adder has 131,072 cases and is checked in seconds. A 32-bit multiplier has 2 to the power 64 cases and cannot be enumerated in the lifetime of the universe. Symbolic equivalence (level 2) avoids enumeration but still fails on large arithmetic, where SAT solvers time out. The only method that scales without bound is composition: prove the parts, prove the glue, and never look inside a part again. This is why the proof ladder ends in composition, and why a primitive cap of 64 cells per leaf is enforced. The cap forces anything larger to decompose, so every proof in the system is either small enough to check exhaustively or built from proofs that were.

**The flow from design to silicon.** A designer writes register-transfer level (RTL) code. Synthesis maps the RTL onto the PDK's cells to produce a netlist. Place and route turns the netlist into geometry. Physical signoff (design rule check, layout versus schematic, static timing) confirms the geometry is manufacturable at the target clock. The geometry is sent to the foundry as a mask set, or shares a mask with other projects on a multi-project shuttle. The manufacturing license in Section 2 is priced per mask set because that is the unit at which a design becomes silicon.

**One ruler.** Every measurement in this record uses ngspice as the single operator. A custom cell and the foundry cell are simulated in the same testbench, at the same load, slew, and corner, from the same open sky130 PDK devices. Delay is a 50 percent to 50 percent propagation measurement; energy is the integral of supply current over a switching cycle. Simulation with test vectors is evidence, recorded and never counted as proof.

## 4. IEEE 754 and the microscaling formats

Floating-point arithmetic is the worked example for two reasons. It is the arithmetic every processor and every accelerator must implement, so a proven floating-point block has the widest possible market. And it has a public specification, IEEE 754, so a proof can eventually be checked against a standard rather than against the designer's own description.

**IEEE 754** defines a floating-point number as a sign, an exponent, and a mantissa, and defines correct rounding: the result of an operation is the representable number nearest the exact mathematical result. A block that is proved equal to its RTL is proved to do what the designer wrote. A block that is proved to satisfy IEEE 754 is proved to do what every other conforming implementation does. The second is stronger, and it is the next rung above the ladder on the front page: refinement to specification.

**Microscaling (MX)** is the Open Compute Project's family of low-precision formats for machine learning. MXFP4 packs elements as E2M1 (a sign bit, a two-bit exponent, a one-bit mantissa) and shares one scale factor across a block of 32 elements. An MXFP4 general matrix multiply (GEMM) accelerator decodes E2M1 elements, multiplies pairs, sums 32 products in an adder tree, and accumulates the result in IEEE 754 single precision (FP32). It is small enough to prove completely and large enough that flat verification of the whole is intractable, which makes it the right test of the ladder.

**Canonical interfaces.** IEEE 754, the OCP MX specification, and the RISC-V F and D floating-point extensions fix the interface of a block independently of its implementer. The beat-or-fork rule binds whoever claims an interface hash, so a canonical interface is one that cannot be quietly renamed to escape the rule. This is where the proof economy will be contested first, and it is the ground Q2 has chosen.

## 5. Data

**The MXFP4 record.** Q2's MXFP4 GEMM accelerator was certified purely by reference to proven parts. Every block's certificate carries the content hash of its real proof of record from the portal's analysis table. The full set of blocks with a passing proof of record, with their hashes, is the [catalog](./catalog.html), exported from the same table.

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

**What it cost to produce.**

| Measure | Value | Source |
| --- | --- | --- |
| Completed proof runs | 23 | portal analysis table |
| Proving compute | 3.724 hours (OpenLane 3.714, Icarus 0.007, Yosys 0.003) | completed minus started, summed |
| Creation span, first request to last completion | 101.72 hours | portal analysis table |
| Machine power | 80 watts | specified |
| Electricity, Vermont residential, September 2026 | 24.44 cents per kWh | see Sources |
| Energy cost, proving-compute basis | 72,811 micro-dollars, about 7.3 cents | theorem energy_compute_uUSD |
| Energy cost, creation-span basis | 1,988,829 micro-dollars, about $1.99 | theorem energy_span_uUSD |

**The market it enters.**

| Measure | Value | Source |
| --- | --- | --- |
| Multi-project shuttle slot, sky130 | $14,950 | chipIgnite |
| Full mask set, 130 nm | $1 to 2 million | AnySilicon |
| Mask set at an advanced node | $10 million or more | SemiAnalysis |
| First-silicon success, 2024 | 14 percent | Wilson Research |
| First-silicon success, 2026 | 5 percent | Siemens Verification Horizons |
| Replication cost of the MXFP4 proof, small team | $4,000 | parameter, about four engineer-days |
| Replication cost, incumbent | $30,000 | parameter, within the $16,000 to $50,000 loaded range |

**The driver loop**, the beat-or-fork example on the public site.

| Measure | Value | Source |
| --- | --- | --- |
| Baseline cell | sky130 buf_16, foundry library | public site, the loop |
| Best in-band candidate, energy-delay against buf_16 | 22 percent lower, same finger count, slightly less energy | oracle measurement, ngspice, sky130 tt corner, 1.8 V, 250 fF load |
| Extra transistors in the winning cell | 0; a threshold-voltage mask change | public site, the loop |
| Fabricable mask combinations that beat the foundry ladder in band | 22 of 30 | oracle measurement |
| Anchor record for the best win | label 2200 basis points, context 16 (drive strength) | q2-anchor record() call, prepared, not submitted |

**Proof engines, by level**, and what each trusts.

| Level | Engine | What is checked | What is trusted |
| --- | --- | --- | --- |
| 1. Exhaustive | ngspice DC and transient sweeps | A cell's output for every digital input, threshold at half VDD; capture, hold, and edge exclusivity for flops | The PDK transistor models |
| 2. Equivalence | Yosys SAT miter, temporal induction | Netlist equals RTL over the whole input space, symbolically | The solver's verdict, parsed with counterexample detection |
| 3. Techmap | Yosys techmap plus structural equivalence | The netlist maps only onto level-1 cells and equals its RTL; a leaf over 64 cells is refused | The proven-cell whitelist |
| 4. Composition | Census plus composition equivalence | The assembly instantiates only proven children and proven glue, and equals the composition of its declared children | Each child's own certificate |

## 6. Analysis

The analysis is a Lean 4 project, Q2Market.lean, with 58 theorems over a model that mirrors the contract's arithmetic exactly. Core kernel only: no mathlib, no native_decide, no sorry. The axiom audit shows every theorem depends on at most propext and Quot.sound, and every numeric theorem on no axioms at all. All money is integer wei or micro-dollars, so no rounding is hidden. The sections below walk from the instrument's guarantee to its consequence.

| Section | What is proved | Key result |
| --- | --- | --- |
| 1. Cap invariant | royalty_due = min(price, target minus recovered), zero once recovered; by induction, recovered never exceeds target | Collection is capped at the declared listing gas |
| 2. Rent bound | rent = collected minus cost | rent is at most CAP minus cost, always |
| 3. Free-entry equilibrium | Any price above cost is undercut; the only stable price is cost | Equilibrium rent is zero |
| 4. Production cost | 80 W, 24.44 cents per kWh, measured hours | 7.3 cents and $1.99; both far below the 0.005 ETH cap |
| 5. Make versus buy | A competent buyer pays at most replication cost across all masks | $800 Charter price at $4,000 replication; $6,000 at $30,000 |
| 6. The floor | $100 per mask, SoC down | 66 bps of a shuttle, 0 bps of a mask set; entrants need 40 (team) or 300 (incumbent) masks to break even |
| 7. Capstone | Production versus floor | $98.01 on the first mask, $100 on every later one; replication is 2,011 times production |
| 8. The descent | Physical cost per mask falls with volume; deterrence tightens as the floor falls | 1.2 cents per mask at 1,200 masks, 1.0 cent at a million; the safe-descent ladder |

**Reading the analysis.** Sections 1 through 3 establish that the reference license cannot extract rent: collection is capped at a declared, unraisable target, and under free entry the only stable price is cost. Section 4 measures that cost for a real system and finds it under two dollars. Section 5 turns to the manufacturing license and shows that a rational buyer never pays more than it would cost to replicate the proof. Section 6 places the $100 floor far below that replication cost and computes how many masks a competitor would need to sell to recover its own replication spend. Section 7 combines them: the first mask returns $98.01 over production cost, and every later mask returns $100, while a competitor is 2,011 times more expensive per unit than the incumbent proof. Section 8 shows the floor can descend by a factor of ten at each rung while the deterrence ratio tightens, because the physical cost per mask falls with volume.

**At the $100 floor**, each row a theorem.

| Measure | Kernel-checked value |
| --- | --- |
| Share of a $14,950 shuttle slot | 66 bps (0.66 percent) |
| Share of a $1.5 million mask set | 0 bps |
| Margin on the first mask | $98.01 |
| Margin on every later mask | $100 |
| Entrant break-even, small team ($4,000) | 40 masks |
| Entrant break-even, incumbent ($30,000) | 300 masks |
| Library break-even, IEEE 754 (about $100,000 to produce) | 1,000 masks |
| $120,000 per year | 1,201 masks per year |

**The descent ladder**, each row a theorem.

| Floor per mask | Masks per year for $120,000 | Entrant break-even at $4,000 replication |
| --- | --- | --- |
| $100 | 1,201 | 40 |
| $10 | 12,100 | 400 |
| $1 | 122,000 | 4,000 |
| 10 cents | 1,340,000 | 40,000 |

**Soundness of composition, proved.** The rule behind level 4, that proven parts plus proven glue yield a proven whole, is now a machine-checked theorem rather than an assumption. The project [proofs/composition-soundness](https://github.com/Q2Computing/Project-Foundry/tree/main/proofs/composition-soundness) models a combinational block as a pair of functions, its implementation and its specification, and proves for sequential, parallel, and general glue composition that if every child's implementation equals its specification and the assembly's implementation equals the wiring of the children's implementations, then the assembly's implementation equals the wiring of the children's specifications. Eighteen theorems in Lean 4.33.1, core kernel only; the sequential and parallel forms depend on no axioms, and the general glue and list forms depend only on Quot.sound through function extensionality. What remains assumed is the fidelity of the checker to the model: that the portal's census instantiates the hypothesis on the children and its Yosys equivalence check instantiates the hypothesis on the glue. Blocks with registers are the next step, scheduled on the roadmap.

**Invariants the contract enforces.** The theorems describe the model; these are the properties of the deployed code that make the model faithful.

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

**What is assumed.** Elasticity, that volume rises about tenfold as the floor falls tenfold; tested per rung, since the floor drops only when measured volume clears the next rung. Interfaces, that canonical standards make renaming costly. Certificates are claims; registration is unverified by design, and trust comes from the proof being checkable off chain, re-run by the verifier, or attested. Parameters: 24.44 cents per kWh, $3,000 per ETH, replication $4,000 and $30,000, settlement gas 1 cent per mask, a 20 percent Charter fraction, a $120,000 per year target. Change any and the numbers move; the theorems do not.

## 7. Conclusion

**Q2 Computing is first to market.** As of this record, a real system has been certified purely by composition of proven parts, its certificates carry the hashes of real proofs of record, two licenses settle it on a public chain, and 58 machine-checked theorems bound what the instrument can charge and what it guarantees. No other party has published a certificate at any level of the ladder, a composition contract, or a proof of the economics. The ground chosen for the first contest, IEEE 754 arithmetic and the OCP MX formats on open PDKs, is the ground with the widest market and the most canonical interfaces.

**Competition is structurally foreclosed, and the analysis shows why.** Consider each position a competitor could take.

1. **Charge rent on references.** Section 3 of the analysis proves that under free entry the only stable reference price is cost, and the cap invariant prevents any lister from collecting more than its declared listing gas. A competitor who charges more is undercut by a competitor who charges cost, and the first competitor to charge cost is Q2's own protocol.
2. **Re-prove the same blocks privately.** Section 7 shows replication costs 2,011 times what the existing proof costs per mask. A buyer who can inherit a proof for $100 per mask, or for free by reference, will not spend $4,000 to $30,000 to repeat it. Private re-verification, today's default, becomes the expensive option.
3. **Undercut the manufacturing floor.** Section 6 shows an entrant needs 40 to 300 masks to break even at $100, and Section 8 shows that every rung down the ladder multiplies that number by ten while the incumbent's physical cost per mask keeps falling. The floor is set by Q2 and descends on Q2's schedule, toward physical cost. There is no price below physical cost at which an entrant recovers replication.
4. **Beat the blocks.** This is permitted and invited. Beat-or-fork requires the challenger to make the prior lister whole and to prove the improvement by measurement. The result is a better block inside the same economy, listed under the same cap, licensed under the same floor. Improvement strengthens the catalog; it does not create a rival to it.
5. **Build a rival economy.** A rival must offer a cheaper reference (impossible below cost), a lower manufacturing floor (impossible below physical cost, which Q2 is already descending toward), or a stronger proof (which lists into this economy under beat-or-fork). Any block a rival proves is, by construction, a candidate certificate here.

The instrument does not win by out-competing rivals on price. It removes the positions from which price competition is possible. Reference pricing is pinned to cost by theorem. Manufacturing pricing is pinned to a floor that only its author can lower and that converges on the physical cost of producing and settling a proof. Improvement is captured rather than opposed. What remains is a single, growing, publicly proven catalog, first listed by Q2 Computing, whose every entry makes the next entry cheaper to prove.

The bets in Section 6 remain bets. Elasticity is tested one rung at a time and the floor never drops ahead of measured volume. The conclusion holds under the stated parameters; the theorems hold under any.

## Reproduce

1. `cd contracts/q2-composition/demo && npm install && node run.mjs`: both economies over the real MXFP4 tree.
2. `cd contracts/q2-composition/proofs && lake build && lake env lean Audit.lean`: 58 theorems and the axiom audit.
3. `cd contracts/q2-composition && cargo build --release --target wasm32-unknown-unknown`, then `cargo stylus check` against Arbitrum Sepolia: the contract, on Linux.

## Sources

1. [chipIgnite shuttle pricing, $14,950 per project](https://chipfoundry.io/faqs)
2. [130 nm wafer and MPW cost, mask set $1 to 2 million](https://anysilicon.com/130nm-wafer-mpw-cost/)
3. [Photomask cost by node, SemiAnalysis](https://newsletter.semianalysis.com/p/the-dark-side-of-the-semiconductor)
4. [First-silicon success at 14 percent, 2024 Wilson Research study](https://semiengineering.com/first-time-silicon-success-plummets/)
5. [First-silicon success at 5 percent, 2026 study](https://blogs.sw.siemens.com/verificationhorizons/2025/09/03/why-first-silicon-success-is-getting-harder-for-system-companies/)
6. [Vermont residential electricity, 24.44 cents per kWh, September 2026](https://www.electricchoice.com/electricity-prices-by-state/vermont/)
7. [IEEE 754-2019, Standard for Floating-Point Arithmetic](https://ieeexplore.ieee.org/document/8766229)
8. [OCP Microscaling Formats (MX) Specification v1.0](https://www.opencompute.org/documents/ocp-microscaling-formats-mx-v1-0-spec-final-pdf)
9. [Power laws in citation distributions, Scopus](https://link.springer.com/article/10.1007/s11192-014-1524-z)

The MXFP4 proving compute, the creation span, and every certificate hash come from Q2's own portal analysis records.
