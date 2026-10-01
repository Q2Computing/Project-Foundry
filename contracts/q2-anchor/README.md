# Q2Anchor, a content-addressed provenance anchor (Arbitrum Stylus)

> **Disclosure-safe to submit.** This contract is a *generic* hash anchor -> decades-old prior art (Haber–Stornetta 1991; Git; Certificate Transparency).
> Publishing it discloses nothing novel that Q2 claims, so it does not bar Q2's
> pending patents. The patentable mechanism stays private (`contracts/q2-attestation`,
> `confidential/`) and is never referenced here.
>
> **One residual risk to keep in mind (no lawyer needed to act on it):** if a
> *future* patent filing were drafted so broadly that its claims read on "anchor
> any hash + label on-chain," this public contract could be prior art against
> those over-broad claims. Mitigation is free and later: keep future claims aimed
> at the withheld *mechanism*, not the anchor. Full analysis in
> `confidential/patent/Q2-PAT-attestation-settlement/counsel-memo.md` §5, for
> Q2's own reference; not a prerequisite to submitting.

A minimal smart contract, written in Rust for [Arbitrum Stylus](https://arbitrum.io/stylus),
that does one thing: it lets anyone **anchor a hash of an off-chain artifact,
together with an opaque outcome label, immutably on-chain**, and verify it later.

That is the whole contract. Anchoring a hash for provenance and timestamping is a
decades-old primitive (Haber–Stornetta 1991; Merkle trees; Certificate
Transparency; Git). Q2Anchor is a clean Stylus implementation of it, and nothing
more. The contract is deliberately a **black box** about how a label was produced
or whether it is final, it never sees the work product, the method, or any
decision logic. The work stays off-chain; only a proof of it is anchored here.

## Interface

```solidity
interface IQ2Anchor {
    function record(bytes32 artifact_hash, uint16 label, uint16 context) external returns (uint256);
    function count() external view returns (uint256);
    function get(uint256 id) external view returns (bytes32, uint16, uint16, address, uint64);
    function verify(uint256 id, bytes32 artifact_hash) external view returns (bool);
    error RecordNotFound();
    // event Recorded(uint256 indexed id, address indexed submitter,
    //                bytes32 artifact_hash, uint16 label, uint16 context, uint64 timestamp);
}
```

- **`record`**, permissionless and append-only. `artifact_hash` is a commitment
  (e.g. a keccak/sha256 of some file). `label` and `context` are opaque coarse
  codes whose meaning is defined entirely off-chain. Emits `Recorded` and returns
  a 1-based record id.
- **`get` / `count` / `verify`**, reads. `verify(id, hash)` is a convenience:
  does record `id` commit to `hash`?

Records are **non-invertible**: a `<hash, label, context>` row lets anyone confirm
that a specific artifact was committed with a specific coarse outcome, without
revealing the artifact, the outcome's meaning, or how it was reached.

## Why so small

This is intentional. The interesting part of Q2's system, how an outcome is
produced and how work is settled, is **off-chain and out of scope for this
contract**. On-chain, we want only the least, most generic thing: a durable,
public, verifiable commitment. Keeping the on-chain surface generic is both good
architecture (content off-chain, proof on-chain) and a deliberate constraint: the
public contract commits Q2 to nothing about its off-chain process.

## The discovery layer (off-chain)

The contract is the generic anchor; the **meaning** lives off-chain, in a small,
dependency-light Node layer under `verify/` and `scripts/`. This is what turns a
hash anchor into a **settlement primitive for verifiable hardware IP**:

- **`verify/harness.mjs`**, the "re-run it" layer. Given a submission bundle it
  (1) re-derives the two designs from their declared source, (2) **proves** they
  compute the same function, exhaustively over every input assignment, a
  complete proof at this size, (3) **measures** the cost improvement (gates,
  depth), (4) captures git provenance, and (5) computes the canonical commitment
  hash that gets anchored. It is transient (keeps nothing), deterministic (same
  bundle → same hash), and portable (pure Node, runs on Q2 infra or a stranger's
  laptop).
- **`scripts/pipeline.mjs`**, end to end: prove → re-run (determinism) → anchor
  on Arbitrum → read back and `verify`. `--dry-run` proves without touching chain.
- **`scripts/discovery.mjs`**, reads every anchored record and ranks it by proven
  improvement: the "who can actually move this benchmark" signal, which is the
  product.

The differentiator, embodied not asserted: **don't trust our proof, re-run the
harness and compare the hash to the one on-chain.** The trusted elements are named
(the open PDK and human sign-off); nothing here claims to be trustless. Full
design in `HARNESS.md`.

```bash
npm install
npm run verify              # prove + measure the sample submission
node scripts/pipeline.mjs --dry-run   # full flow, no chain
```

## Build & validate

Requires Docker (the build runs in a Linux container; the Stylus toolchain does
not link cleanly on Windows). From `contracts/q2-anchor`:

```bash
# build the deployable wasm (cdylib)
cargo build --release --target wasm32-unknown-unknown

# validate it is a well-formed, activatable Stylus contract
cargo stylus check --endpoint https://sepolia-rollup.arbitrum.io/rpc

# regenerate the Solidity interface
cargo stylus export-abi
```

Last validated run: **contract size 10.4 KB** (well under the 24 KB on-chain
limit), **activation data fee ≈ 0.000091 ETH**, reproducible deployment hash
computed. Toolchain pinned in `rust-toolchain.toml` (Rust 1.98.1); dependency set
pinned in `Cargo.lock` for reproducible verification.

## Deploy (gated)

Deployment needs one thing: **a funded Arbitrum Sepolia key** (free from a
faucet). It is a human action performed with your own key, see `DEPLOY.md` for
the exact command.

## License

MIT OR Apache-2.0.
