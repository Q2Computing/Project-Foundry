# Certificate characterization

Every circuit registered as a certificate commits to a bundle that conforms to
[`schema/certificate.v1.schema.json`](../schema/certificate.v1.schema.json).
The on-chain record stores `sha256` of that bundle (with its `certificate`
block removed) as `artifact_hash`. One bundle has exactly one hash, computed in
one place, [`tools/cert_hash.py`](../tools/cert_hash.py), so anyone holding the
bundle recomputes the hash and checks it against the chain.

A certificate therefore proves three things at once, without disclosing the
design:

1. **Structure.** `design_hash` and `interface_hash` commit the circuit and the
   interface a parent may rely on. The design stays private; the hash proves we
   possess it.
2. **Conformance.** The external standard the circuit meets, and the exact
   parameters it meets it within. For an arithmetic circuit this is IEEE 754,
   with the rounding mode, subnormal handling, flags and operand range stated.
3. **Cost.** What the circuit consumes to deliver that result, measured and
   pinned to a corner, a temperature and an input activity.

## What a circuit is measured on

A circuit has costs (what it consumes from a mission's budget), deliverables
(what the computation is worth), and a normalizer (what makes the first two
comparable across circuits and processes). The schema separates them.

### Costs, the envelope the mission budgets

| Axis | What it is | Produced by |
| --- | --- | --- |
| Area | 2D die footprint | synthesis (cell area), place and route (die area) |
| Time | latency per operation and throughput, capped by f_max | static timing on the critical path |
| Energy | dynamic (half C V squared times activity, per op) plus static (leakage times time) | post-layout, at a stated activity and duty cycle |
| Power | energy per unit time, a rate with a thermal ceiling | energy times throughput, against the process power-density limit |
| Mass and volume | the payload a non-static system carries | the fabrication stack and package, applied per mission |

Two costs are easy to overlook. **Power** is a rate, not a quantity: a workload
can be power-limited, unable to dissipate heat fast enough, while energy is
abundant. **Mass and volume** are set by the process stack, not the RTL, so they
enter when a circuit is placed in a system, not at registration.

### Deliverables, what the computation is worth

- **Information delivered** per operation, the useful output bits.
- **Precision**, the numerical fidelity: exact (bit-identical to the reference)
  or bounded (within a stated ulp). A smaller, faster, lower-energy circuit can
  be less faithful; precision is the axis traded against the three costs.
- **Reliability** over the mission: soft-error rate and lifetime wear, set by
  the environment. Central to sustained operation, applied per mission.

### Entropy, the normalizer

Entropy is the only quantity that converts to energy through a universal
constant (k ln2 per irreversibly erased bit, the Landauer floor), sets a hard
physical floor, and is defined by the workload rather than the circuit. It is
what makes an area, an energy and a time comparable, and what ties a mission's
workload to a process's capability.

- Information entropy of a calculation is **not intrinsic to the circuit**. It
  is relative to the input distribution. The irreducible quantity is the input
  information the operation necessarily destroys, `bits_discarded_per_op`, which
  depends on the operand statistics. For IEEE 754 the alignment shift (set by
  the exponent difference) and round-to-nearest-even are the dominant,
  operand-dependent information sinks.
- Energy is not entropy. `energy_fj_per_op` is what switching dissipates; the
  Landauer floor is the irreducible part. `thermodynamic_efficiency` is their
  ratio, the distance to the physical floor. Two circuits equal on area and time
  can differ here, and that distance is the licensable improvement.
- Every energy figure names its `activity`, and every entropy figure names its
  `operand_distribution`, because both are distribution-relative.

## Specialization is expected

There is no single scalar. A mission has a binding constraint, and the best
circuit is the one closest to the floor on that axis. So for one interface, say
an FP32 adder, several certified circuits can coexist: one optimizes area and
energy, another energy and time, another area and time. Each is a point on the
cost surface, and the catalog presents them as such rather than ranking them on
one number.

## How each axis is measured

Through the portal's compute pipeline, so every number is reproducible from
public inputs:

- **Conformance**: Berkeley SoftFloat as the reference. Exhaustive enumeration
  where the input space allows it (2^32 for a unary FP32 operation, run on an
  FPGA), the three-stage decomposition plus a Lean glue theorem for the 2^64
  binary operations, directed and randomized vectors otherwise. Simulation with
  vectors is evidence, never a stand-alone proof.
- **Area**: synthesis cell area; placed die area from the place-and-route flow.
- **Time**: f_max and latency from static timing at the target clock.
- **Energy**: dynamic from activity times C times V squared post-layout at a
  stated activity, plus static leakage folded in at a stated duty cycle.
- **Power density**: the above over area, against the process ceiling.
- **Entropy floor**: `bits_discarded_per_op` under a stated operand distribution,
  times k ln2 T, giving the floor and the efficiency ratio.

## The on-chain mapping

| Schema field | On-chain |
| --- | --- |
| sha256 of the bundle (no `certificate` block) | `artifact_hash` (bytes32) |
| `identity.interface_hash` | `interface_hash` (bytes32) |
| `proof_of_record.level` and kind | `proof_kind` (uint16) |
| coarse outcome and context codes | `label`, `context` (uint16) |

The design never goes on chain. The hash commits it, the catalog publishes the
characterization whose hash matches, and a skeptic recomputes the hash and
checks it against the record. The full cost axes live in the bundle, not in the
uint16 codes, because they do not fit and do not need to: the hash commits them
and the catalog shows them.

## Versioning

This is `q2.certificate.v1`. A change to the measured axes or the hashing rule
is a new version, so an older certificate's hash stays verifiable against the
schema it was registered under.
