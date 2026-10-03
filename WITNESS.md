# Interim witness & leaderboard

Arbitrum paused Stylus contract activation network-wide on 2026-10-02, so the
on-chain settlement gateway is temporarily locked. This is the **interim rail**:
a public, re-checkable way to **register a signature and prove a circuit without
sharing it**, while the chain is down. It commits exactly what the on-chain
`record()` does, so the chain supersedes it when activation returns.

## What it does, and does not, disclose

You hash your design and your test result **locally**. Your wallet signs the
hash. Only the **hash, the measured cost, and the signature** are posted — never
the design, never the testbench. A hash reveals nothing, so this is safe in a
public repo. You reveal the design later, to whomever you choose, and they
recompute the hash to confirm what you committed to.

## Honesty ladder

- **witnessed** — a wallet signed the hash of a design + result, timestamped by
  this workflow. A signed *claim*, not a reproduced proof.
- **verified** — the owner reveals the design and the measurement is re-run
  against the open PDK; the hash and the result are reproduced.
- **settled** — recorded on-chain when Stylus activation returns.

## The leaderboard metric

Ranking is **information-entropy-normalized efficiency** against the three
primary physical resources — time, space, energy — with information as the
normalizer (per useful bit):

- **energy** vs Landauer: `eta_E = (kT ln2) / (energy per bit)` (absolute floor; kT ln2 ≈ 2.87e-21 J at 300 K),
- **space × time** vs the area-time frontier: `eta_AT = best(area·delay/bit) / (area·delay/bit)` (Thompson; frontier-relative per interface),
- **index** = `sqrt(eta_E · eta_AT)` — the fraction of the physical ideal achieved.

Each interface also has a **Pareto frontier** (non-dominated on energy/bit and
area·time/bit): a catalog certifies a frontier, not a single winner.

## How to post a submission

1. Build the submission locally (hashes your files, prints the message to sign):

   ```
   npm i ethers@6
   node tools/attest.mjs \
     --interface sky130_fd_sc_hd__inv_1 --tier standard-cell --verdict pass \
     --signature-file inv_1.sig.v --testbench-file tb_inv_1.v \
     --area 0.9 --delay 0.14 --energy 1.8e-15 --nbits 1 --wallet 0xYourAddress
   ```

2. Sign the printed message in your wallet (MetaMask, `cast wallet sign`, …).
3. Re-run with `--sig 0x<signature>` to write `submissions/<id>.json`.
4. Open a pull request adding that file. The `witness` workflow verifies the
   signature (`ecrecover`) and, on merge, rebuilds the leaderboard. If the
   signature does not recover to your wallet, the run goes red — that is the
   "ask questions" case, by design.

Verify any submission yourself: `node tools/verify-submission.mjs`.

## Record shape (`submissions/*.json`, schema `q2.witness.v1`)

```json
{
  "schema": "q2.witness.v1",
  "interface": "sky130_fd_sc_hd__inv_1",
  "tier": "standard-cell",
  "fingerprint": "0x<sha256 of the canonical design/signature bundle>",
  "result_hash": "0x<sha256 of the testbench + pass/fail bundle>",
  "verdict": "pass",
  "measure": { "area_um2": 0.9, "delay_ns": 0.14, "energy_j": 1.8e-15, "n_bits": 1 },
  "wallet": "0x…",
  "wallet_sig": "0x…",
  "submitted_at": "2026-10-03T20:00:00.000Z"
}
```

The example submissions in `submissions/` are signed with throwaway demo keys to
show the full flow and render the board.
