# Soundness of composition for combinational blocks

Machine-checked in Lean 4 (core kernel only). This is the rule the portal's
level-4 check relies on when it accepts an assembly on the strength of a
census of proven children plus one equivalence check of the glue.

## What is proved

A combinational block is a pair of pure functions `impl, spec : α → β` over
abstract input and output types. A block is `Proven` when `impl x = spec x`
for every input `x`.

Three composition forms are defined so that the implementation and the
specification of the composite go through the same wiring:

- `seq b1 b2`: sequential, `impl = b2.impl ∘ b1.impl`, `spec = b2.spec ∘ b1.spec`
- `par b1 b2`: parallel on a product input
- `glue children w`: an indexed family of children (each with its own input
  and output types) and an arbitrary pure wiring function `w` that receives
  the assembly input and an evaluator for every child. `glueList` is the same
  for a homogeneous list of children.

For each form two theorems are proved:

- closed form (`seq_sound`, `par_sound`, `glue_sound`, `glueList_sound`): if
  every child is proven then the composite block is proven. Because the
  composite is itself a `Block`, it can be a child of a further composition.
- assembly form (`*_sound_assembly`): given any block `a` such that
  `a.impl x = w x (children' implementations)` for all `x` (the glue
  hypothesis) and every child is proven (the census hypothesis), then
  `a.impl x = w x (children' specifications)` for all `x`. That is, the
  assembly is proven with respect to the composed specification.

Closure under nesting is stated as corollaries: `glue_nested_sound`,
`glue_nested_sound_assembly` (two levels of glue, both in closed and assembly
form), `seq_par_nested_sound` and `seq_glue_nested_sound`. `seq_as_glue` and
`par_as_glue` show that the binary forms are instances of the general one.

## What is assumed

The Lean development is unconditional on its own terms. The only axiom any
theorem depends on is `Quot.sound` (through function extensionality, in the
`glue` and `glueList` results); the `seq` and `par` theorems depend on no
axioms at all. It uses no mathlib, no `native_decide`, no `sorry` and no
`Classical.choice`.

What is not proved here is the fidelity argument that links the portal to the
model. Applying these theorems to a real assembly assumes:

1. The census instantiates the hypothesis "every child is `Proven`", meaning
   each child's recorded proof really does establish `impl = spec` on every
   input for the netlist actually referenced by the assembly.
2. The equivalence check (Yosys) instantiates the glue hypothesis, meaning the
   assembly netlist really does compute the chosen wiring of the children's
   implementations, and that the specification the portal reports for the
   assembly is the same wiring applied to the children's specifications.
3. The blocks are combinational: pure functions of their inputs with no
   internal state.

Those are properties of the tooling and of the data it is run on. They are
stated here as assumptions and are not discharged by this development.

## How to run

From this directory, with the pinned toolchain in `lean-toolchain`
(elan will select it):

    lake build && lake env lean Audit.lean

`lake build` must complete with no errors. `Audit.lean` prints the axiom list
of every theorem; each list must be empty or a subset of
`[propext, Quot.sound]`.

## Files

- `lean-toolchain`: pinned Lean version
- `lakefile.toml`: single library, no dependencies
- `CompositionSoundness.lean`: definitions and theorems
- `Audit.lean`: `#print axioms` for every theorem
