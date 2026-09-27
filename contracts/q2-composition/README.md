# Q2Composition — proof certificates that license into larger proofs, and into silicon

**Smart contracts predicated on proofs.** A proof of a small VLSI block is a
**certificate**. You certify a *larger* system by **referencing** child
certificates the chain already holds, never the child's design. And you license
a proven design into a manufactured SoC through a **third-party foundry** that
receives the design so the licensee never does. A remote VLSI economy that
depends on no company, only on a contract releasing a model for use.

This is the third of Q2's three Arbitrum Stylus contracts, one per settlement mode:

| Contract | Mode | What the chain does |
|---|---|---|
| `q2-verifier` | **re-verify** | Re-runs a bounded proof on-chain (e.g. an exhaustive adder equivalence). Trustless. |
| `q2-anchor` | **anchor** | Records a content-addressed commitment of an off-chain proof plus an improvement label. |
| `q2-composition` (this) | **compose / license** | Certifies a larger system by reference to child certificates, and settles both license classes. |

## The financial model

Two license classes, economically distinct on purpose. **The protocol takes zero
in both.** Every wei paid is credited to a certificate owner or refunded to the
payer, and withdrawn by pull.

### License 1 · Reference (the commons economy)

- **Anyone can prove at any level of entry.** Registration is permissionless and costs only gas.
- **Foundry PDK primitives are `commons`:** free to reference forever, unpriceable.
- **Everything else is cost recovery, never rent.** A certificate carries a
  lister-declared `recovery_target` (its listing gas) and a `ref_price` that only
  paces recovery. Referencing pays the royalty **only to the abstractions you
  directly use**, the child certificates you name, never to the recursion
  beneath them: each deeper level was settled once, when that abstraction was
  composed. Every certificate is **capped at its target**; once recovered it is
  free forever. The most-used proofs go free fastest, which is the right incentive
  for a commons.
- **Beat-or-fork: whoever beats you pays your listing cost.** Proving "better
  than X" measures against X's proven baseline, which is a reference to X. So a
  new certificate claiming an interface that is already certified must name its
  `baseline` and settle that incumbent's remaining recovery. A competing
  implementation cannot be listed silently. You recover your gas if you are
  used *or* if you are beaten; the only way you don't is if nobody does either.
- **A protocol cap bounds what a lister may declare.** `recovery_target` is
  capped at **0.005 ETH** (`MAX_RECOVERY_TARGET`). Real listing gas is cents, so
  the cap is still generous, and it closes two attacks at once: rent disguised as
  "listing gas", and interface squatting (registering someone's interface
  first with an extortionate price). Arithmetic is checked, never wrapping.
- **Fork vs beat: "best available" is measured, never declared.** A fork only
  names and pays its baseline. A **beat** (`claim_beat`) must additionally
  reference a recorded improvement, a `q2-verifier` champion or a `q2-anchor`
  record id, so the public quality-of-service signal is backed by a measurement
  at the referenced contract, not by a self-assertion.

### License 2 · Manufacturing (the designer's product)

- The designer publishes terms on a certificate, names the **foundry** that
  will receive the design, and **commits to the exact package** that foundry
  must receive (`package_hash`). Terms, priced by the designer (not gas-capped):
  **free public**, **single express-shuttle die**, **quantity-limited** (N
  manufactured components), **per use**, or **unlimited**.
- A licensee **buys** the license and never receives the design. **The deal is
  frozen at purchase:** the unit price, the authorized foundry, and the package
  commitment are snapshotted into the license, so a designer changing the offer
  later cannot reprice, redirect, or strand a license already sold.
- The foundry must **record the hash of the package it received**, and it must
  **match the designer's commitment**, before it may **consume** a single unit
  (free public releases exempt). So the chain proves the foundry received the
  *certified* design, not merely "a package", and no unit is manufactured from a
  design it hasn't provably received.

### What is on-chain vs off-chain (stated, not hidden)

On-chain: the certificate registry, the binding that ties a system to exactly the
certified children it names, the beat-or-fork check, both license settlements,
and disclosure receipts. Off-chain: the deep functional composition proof (that a
parent equals the composition of its children's interfaces), produced by the
lab's prover and committed as `artifact_hash`. Re-running proofs on-chain is
`q2-verifier`'s job, for the ones small enough.

## The interface

Reference license
- `register(artifact_hash, interface_hash, proof_kind, commons, ref_price, recovery_target, baseline) payable -> id`
- `certify(system_hash, interface_hash, proof_kind, child_ids[], binding, ref_price, recovery_target, baseline) payable -> id`
  — binding = `keccak256(system_hash ‖ interface_hash ‖ each direct child's registered interface_hash)`
- `set_ref_price(id, price)` · `reference_terms(id)` · `baseline_of(id)` · `interface_first(interface_hash)`
- `claim_beat(id, improvement_ref)` (owner; requires a baseline and a non-zero improvement reference) · `beat_ref(id)`

Manufacturing license
- `set_manufacturing_terms(id, terms, price, quantity, foundry, package_hash)` — commits the package the foundry must receive
- `buy_license(cert) payable -> lic` · `record_disclosure(lic, package_hash)` (foundry; must match the commitment) · `consume(lic, units) payable` (foundry; requires a recorded disclosure)
- `manufacturing_terms(id)` (includes the committed package hash) · `license(lic)` · `license_count()`

Payouts and lineage
- `withdraw()` · `owed_to(addr)` · `certificate(id)` · `child_count(id)` · `child(id, i)` · `count()`

## The demonstration: a real MXFP4 GEMM accelerator

`demo/mxfp4-certificates.json` is Q2's **actual** MXFP4 (OCP Microscaling FP4)
proof-by-construction tree, exported from the portal. Every block carries the
real content hash of its proof of record, from SPICE-proven sky130 PDK cells at
the bottom (the commons), through equivalence-proven leaves, to composition-proven
assemblies, up to the accelerator.

```bash
node demo/run.mjs      # dry-run: the contract's semantics, simulated exactly
```

It shows both economies end to end: PDK cells pay nothing forever, every Q2
block pays only the direct abstractions it uses with cap progress visible, the
accelerator is certified purely by reference to proven parts, and one
manufacturing license runs buy → disclosure → consume without the licensee ever
seeing the design.

## Build & deploy (Linux; the Windows host link fails on a dependency)

```bash
cargo build --release --target wasm32-unknown-unknown
cargo stylus check --endpoint https://sepolia-rollup.arbitrum.io/rpc
cargo stylus export-abi
cargo stylus deploy --endpoint <arb-sepolia-rpc> --private-key-path <testnet-key-file>
```

Same toolchain pin as `q2-anchor` / `q2-verifier` (stylus-sdk 0.6, alloy 0.7.6).
