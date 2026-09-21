# q2-edp-driver — beat a foundry cell, prove it in public

Pick a standard cell the foundry ships. Have an agent try to design a custom
cell that beats it — on **area, speed, and energy**. Re-measure everything in
the open, from scratch, in continuous integration. Anchor the provenance of the
wins on-chain, without publishing the design.

The point is not one clever transistor sizing. It is a **loop** that turns
"we think we can do better than the prefab" into a public, re-runnable fact, and
accumulates a hash-addressed trail of measured improvements.

## The loop

```
  generate                 assess (the oracle)               anchor
  ─────────                 ───────────────────               ──────
  agent proposes    ──►     GitHub Actions re-measures  ──►   hash + coarse
  many candidate            baseline + every candidate        label recorded
  cell designs              in one ngspice bench, on           via q2-anchor
  (sizings, stage           the open sky130 PDK, and           (Arbitrum Stylus)
  counts, Vt mixes)         decides who actually wins          — netlist stays
                                                               private
```

Two properties make it credible:

1. **The judge is independent of the generator.** Generation is exploratory and
   can use any LLM ("hey Gemini, beat this part") offline, where an API key and
   nondeterminism are fine. Assessment is deterministic and runs in CI, so the
   verdict is a public artifact anyone can re-run — not our word.

2. **Everyone is measured on the same ruler.** ngspice is the single measurement
   operator. The custom cell and the foundry cell are simulated in the *same*
   testbench, at the same load, slew, and corner, built from the same
   `sky130_fd_pr` devices. Delay is a 50%→50% propagation measurement; energy is
   the integral of supply current over a switching cycle.

## What "beats the part" means

A candidate beats the foundry part when it is, at the operating point:

- **functional** — output swings rail-to-rail (a real buffer),
- **dominating** — no worse on any of {area, delay, energy} and strictly better
  on at least one (Pareto dominance), and
- **unique** — a design hash not already recorded.

Objectives (all minimized): `area_um` (transistor-width proxy — see caveat),
`tpd_ns` (propagation delay), `energy_fj` (supply energy per cycle). Reported
scalars: **EDP** = energy·delay and **ED²P** = energy·delay².

## How the custom cell can win at all

The sky130 buffer ladder is quantized (buf_1, 2, 4, 6, 8, 12, 16) and every
buffer is a fixed **2-stage** design built from parallel unit inverters. That
leaves real gaps a device-layer design can exploit:

- **Between rungs.** For a load where no rung is well matched, the smaller rung
  is too slow and the larger one wastes energy and area. A cell sized to the
  actual load sits in the gap.
- **Stage count.** At large loads the delay-optimal number of stages is ~3–4,
  but the ladder is stuck at 2. A 4-stage taper spends less energy for the same
  speed.
- **Vt mixing.** A low-Vt output stage with high-Vt earlier stages — a trade the
  single-flavor prefab can't make.

## Honesty about scope

This measures **electrical** figures of merit against the open PDK's SPICE
models. It is deliberately explicit about what it does *not* yet claim:

- `area_um` is a **transistor-width proxy** (Σ device widths, L fixed), not a
  laid-out cell area. Real area needs the layout flow (magic/klayout) — phase 2.
- A candidate that beats the part here is **deck-clean + SPICE-characterized**,
  not **foundry-qualified**. Qualification is DRC/LVS/antenna/latchup across all
  corners and a signoff the foundry owns. That boundary is not crossed here.
- A run where nothing beats the part is a real result too, recorded as a dated
  negative finding. The part standing is information, not failure.

## Disclosure-safe provenance

For each verified, unique win, `anchor.py` commits a SHA-256 hash over a
canonical bundle — the design's canonical form, the measured metrics, the
operating point, and the pinned PDK version — and prepares a call to the
`q2-anchor` Stylus contract:

```
record(bytes32 artifact_hash, uint16 label, uint16 context)
```

`label` is basis points of EDP improvement; `context` is the part's drive
strength. The **hash is the on-chain artifact; the netlist need never be
published.** A holder of the netlist can recompute the hash and verify; without
it, the record is an opaque commitment to a measured improvement. That is the
whole idea: anchor the *fact* of a unique, measured win without exposing the IP
that produced it. `anchor.py` never transacts — submitting uses a funded key,
an explicit step.

## Reproduce it

Requires Docker and the open sky130 PDK (via [ciel](https://github.com/fabulous-labs/ciel)).

```bash
./run.sh assess     # re-measure committed candidates vs the part (the CI gate)
./run.sh propose    # search the design grid, keep dominating survivors
./run.sh anchor     # prepare disclosure-safe provenance records
```

CI (`.github/workflows/assess.yml`) does the same on a clean ubuntu runner:
installs ngspice, fetches the pinned PDK from the open source, runs the oracle,
and fails the build if a committed "beats the part" claim doesn't hold.

## Layout

```
tools/
  candidate.py   build a driver cell from a device-layer spec (unit inverters)
  measure.py     the measurement operator (ngspice): delay, energy, area, function
  propose.py     generation: deterministic grid (+ LLM seam); pre-filters locally
  assess.py      the oracle: re-measure, judge Pareto dominance, dedupe, report
  anchor.py      disclosure-safe provenance records for verified wins
candidates/manifest.json   the committed designs CI re-verifies
results/                   leaderboard.json, report.md, pareto.svg (CI artifacts)
provenance/                anchor records (hash + coarse label; no netlists)
```

## Results (committed run)

Part to beat: **`sky130_fd_sc_hd__buf_16`** — the largest buffer sky130 HD ships —
at a **250 fF** load (tt, 1.8 V). This is the "large fanout the prefabs didn't
provide": the ladder caps at drive-16, but this load wants ~drive-32.

| design | tpd (ns) | E (fJ) | area (µm) | EDP | vs buf_16 |
|---|---|---|---|---|---|
| `buf_16` (part) | 0.146 | 1008 | 36.3 | 146.9 | — |
| **custom `[13,32]`** | **0.104** | 1199 | 74.2 | **125.1** | **EDP +14.8%, 28% faster** |
| custom `[11,32]` | 0.111 | 1191 | 70.9 | 132.1 | EDP +10.0% |
| custom `[16,48]` | 0.099 | 1368 | 106 | 135.0 | EDP +8.1%, 32% faster |

Five custom drivers beat buf_16 on EDP; the best is **+14.8% EDP and 28%
faster**, built from the *same* nfet_01v8 + pfet_01v8_hvt unit devices. It does
**not** Pareto-dominate — the extra speed costs area and energy, which is the
honest shape of beating a point on the foundry's frontier. Two controls behaved
exactly as they should: a `[6,16]` cell reproduces buf_16 to 5 significant
figures (a same-ruler check), and an under-drive and an over-segmented 4-stage
both lose. See [`results/report.md`](results/report.md) and
[`results/pareto.svg`](results/pareto.svg).
