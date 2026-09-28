/-!
# Soundness of composition for combinational blocks

This file machine-checks the rule the portal's level-4 check relies on:

> If every child block is proven (its implementation equals its specification
> on every input) and the assembly's implementation is the wiring of the
> children's implementations, then the assembly's implementation is the wiring
> of the children's specifications. The assembly is therefore proven against
> the composed specification, and can itself be a child of a further
> composition.

A combinational block is modelled abstractly as a pair of pure functions
`impl, spec : α → β`. The input and output types are left fully abstract, so
the result holds for any bit-vector-like carrier. Wiring is modelled as a pure
function that takes the assembly input and an evaluator for every child and
returns the assembly output; the assembly's implementation and specification
are obtained by feeding the SAME wiring function the children's
implementations and specifications respectively.

Three composition forms are treated:

* `seq`  : sequential composition `Block α β → Block β γ → Block α γ`
* `par`  : parallel composition  `Block α β → Block γ δ → Block (α × γ) (β × δ)`
* `glue` : general composition of an indexed family of children through an
           arbitrary wiring function (with a `List` variant for homogeneous
           children)

For each form there are two statements:

* the *closed* form (`*_sound`): the composed `Block` is `Proven`, so it can
  be used as a child of a further composition; and
* the *assembly* form (`*_sound_assembly`): an arbitrary block `a` whose
  implementation is certified (by an equivalence check) to equal the wiring of
  the children's implementations, has an implementation equal to the wiring of
  the children's specifications.

Two-level nesting corollaries close the loop.

Trusted base: the Lean 4 kernel only. No mathlib, no `native_decide`, no
`sorry`, no `Classical.choice`. The `seq` and `par` theorems depend on no
axioms at all. The `glue` and `glueList` theorems use function extensionality,
which in Lean core reduces to the single axiom `Quot.sound`; `Audit.lean`
prints the axiom list of every theorem.
-/

namespace Q2.Composition

/-! ## Blocks and what it means to be proven -/

/-- A combinational block: an implementation and a specification over the
    same input and output types. -/
structure Block (α β : Type) where
  impl : α → β
  spec : α → β

/-- A block is proven when its implementation agrees with its specification on
    every input. -/
def Proven {α β : Type} (b : Block α β) : Prop :=
  ∀ x, b.impl x = b.spec x

/-! ## Sequential composition -/

/-- Sequential composition: the output of `b1` feeds the input of `b2`. The
    implementation is the composition of implementations, the specification is
    the composition of specifications. -/
def seq {α β γ : Type} (b1 : Block α β) (b2 : Block β γ) : Block α γ :=
  { impl := fun x => b2.impl (b1.impl x)
    spec := fun x => b2.spec (b1.spec x) }

/-- Soundness of `seq` (closed form): proven children give a proven
    composite. -/
theorem seq_sound {α β γ : Type} (b1 : Block α β) (b2 : Block β γ)
    (h1 : Proven b1) (h2 : Proven b2) : Proven (seq b1 b2) := by
  intro x
  show b2.impl (b1.impl x) = b2.spec (b1.spec x)
  rw [h1 x, h2 (b1.spec x)]

/-- Soundness of `seq` (assembly form): if an assembly `a` is certified to
    implement `b2.impl ∘ b1.impl` and both children are proven, then `a`
    implements `b2.spec ∘ b1.spec`. -/
theorem seq_sound_assembly {α β γ : Type} (b1 : Block α β) (b2 : Block β γ)
    (a : Block α γ)
    (hglue : ∀ x, a.impl x = b2.impl (b1.impl x))
    (h1 : Proven b1) (h2 : Proven b2) :
    ∀ x, a.impl x = b2.spec (b1.spec x) := by
  intro x
  rw [hglue x, h1 x, h2 (b1.spec x)]

/-! ## Parallel composition -/

/-- Parallel composition: `b1` and `b2` run side by side on the two halves of a
    product input. -/
def par {α β γ δ : Type} (b1 : Block α β) (b2 : Block γ δ) :
    Block (α × γ) (β × δ) :=
  { impl := fun p => (b1.impl p.1, b2.impl p.2)
    spec := fun p => (b1.spec p.1, b2.spec p.2) }

/-- Soundness of `par` (closed form). -/
theorem par_sound {α β γ δ : Type} (b1 : Block α β) (b2 : Block γ δ)
    (h1 : Proven b1) (h2 : Proven b2) : Proven (par b1 b2) := by
  intro p
  show (b1.impl p.1, b2.impl p.2) = (b1.spec p.1, b2.spec p.2)
  rw [h1 p.1, h2 p.2]

/-- Soundness of `par` (assembly form). -/
theorem par_sound_assembly {α β γ δ : Type} (b1 : Block α β) (b2 : Block γ δ)
    (a : Block (α × γ) (β × δ))
    (hglue : ∀ p, a.impl p = (b1.impl p.1, b2.impl p.2))
    (h1 : Proven b1) (h2 : Proven b2) :
    ∀ p, a.impl p = (b1.spec p.1, b2.spec p.2) := by
  intro p
  rw [hglue p, h1 p.1, h2 p.2]

/-! ## General glue composition (indexed family of children)

`ι` indexes the children; child `i` has input type `In i` and output type
`Out i`. A wiring is a pure function from the assembly input and an evaluator
for every child to the assembly output. The wiring may call any child any
number of times on any value it likes (fan-out, sharing, data-dependent
routing) and may compute arbitrary glue logic of its own; the only thing that
matters is that impl and spec go through the SAME wiring. -/

/-- A wiring for an assembly with input `α`, output `β`, and children indexed
    by `ι`. -/
abbrev Wiring (ι : Type) (In Out : ι → Type) (α β : Type) : Type :=
  α → ((i : ι) → In i → Out i) → β

/-- The children's implementations, as an evaluator. -/
def impls {ι : Type} {In Out : ι → Type}
    (children : (i : ι) → Block (In i) (Out i)) : (i : ι) → In i → Out i :=
  fun i => (children i).impl

/-- The children's specifications, as an evaluator. -/
def specs {ι : Type} {In Out : ι → Type}
    (children : (i : ι) → Block (In i) (Out i)) : (i : ι) → In i → Out i :=
  fun i => (children i).spec

/-- Glue composition: the assembly's implementation is the wiring applied to
    the children's implementations, and its specification is the same wiring
    applied to the children's specifications. -/
def glue {ι : Type} {In Out : ι → Type} {α β : Type}
    (children : (i : ι) → Block (In i) (Out i))
    (w : Wiring ι In Out α β) : Block α β :=
  { impl := fun x => w x (impls children)
    spec := fun x => w x (specs children) }

/-- The census lemma: if every child is proven, the implementation evaluator
    and the specification evaluator are the same function. This is the only
    place function extensionality is used. -/
theorem impls_eq_specs {ι : Type} {In Out : ι → Type}
    (children : (i : ι) → Block (In i) (Out i))
    (hc : ∀ i, Proven (children i)) :
    impls children = specs children := by
  funext i x
  exact hc i x

/-- Soundness of `glue` (closed form): proven children give a proven
    assembly. -/
theorem glue_sound {ι : Type} {In Out : ι → Type} {α β : Type}
    (children : (i : ι) → Block (In i) (Out i))
    (w : Wiring ι In Out α β)
    (hc : ∀ i, Proven (children i)) : Proven (glue children w) := by
  intro x
  show w x (impls children) = w x (specs children)
  rw [impls_eq_specs children hc]

/-- Soundness of `glue` (assembly form). `hglue` is what the equivalence check
    certifies: the assembly's implementation equals the wiring of the children's
    implementations. `hc` is what the census certifies: every child is proven.
    The conclusion is that the assembly implements the wiring of the children's
    specifications. -/
theorem glue_sound_assembly {ι : Type} {In Out : ι → Type} {α β : Type}
    (children : (i : ι) → Block (In i) (Out i))
    (w : Wiring ι In Out α β)
    (a : Block α β)
    (hglue : ∀ x, a.impl x = w x (impls children))
    (hc : ∀ i, Proven (children i)) :
    ∀ x, a.impl x = w x (specs children) := by
  intro x
  rw [hglue x, impls_eq_specs children hc]

/-- The same, packaged as a `Block` so the certified assembly can be passed on
    as a child: the block whose implementation is `a.impl` and whose
    specification is the composed specification is proven. -/
theorem glue_sound_assembly_block {ι : Type} {In Out : ι → Type} {α β : Type}
    (children : (i : ι) → Block (In i) (Out i))
    (w : Wiring ι In Out α β)
    (a : Block α β)
    (hglue : ∀ x, a.impl x = w x (impls children))
    (hc : ∀ i, Proven (children i)) :
    Proven { impl := a.impl, spec := (glue children w).spec } :=
  glue_sound_assembly children w a hglue hc

/-! ## Closure: composites are children

`seq`, `par` and `glue` all return a `Block`, and the `*_sound` theorems show
the returned block is `Proven`. So a composite can be fed straight back into
any of the composition forms as a child. The corollaries below spell out
two-level nesting for each form. -/

/-- Two-level nesting through `glue`: every inner assembly is itself a glue of
    proven leaves, and the outer assembly is a glue of the inner assemblies. -/
theorem glue_nested_sound
    {κ : Type} {ι : κ → Type}
    {In Out : (j : κ) → ι j → Type}
    {α' β' : κ → Type} {α β : Type}
    (leaves : (j : κ) → (i : ι j) → Block (In j i) (Out j i))
    (wIn : (j : κ) → Wiring (ι j) (In j) (Out j) (α' j) (β' j))
    (wOut : Wiring κ α' β' α β)
    (hleaves : ∀ j i, Proven (leaves j i)) :
    Proven (glue (fun j => glue (leaves j) (wIn j)) wOut) :=
  glue_sound _ wOut (fun j => glue_sound (leaves j) (wIn j) (hleaves j))

/-- Two-level nesting, assembly form: each inner assembly `inner j` is
    certified against the wiring of its leaves, the outer assembly `a` is
    certified against the wiring of the inner assemblies' implementations, and
    all leaves are proven. Then `a` implements the outer wiring of the inner
    composed specifications. -/
theorem glue_nested_sound_assembly
    {κ : Type} {ι : κ → Type}
    {In Out : (j : κ) → ι j → Type}
    {α' β' : κ → Type} {α β : Type}
    (leaves : (j : κ) → (i : ι j) → Block (In j i) (Out j i))
    (wIn : (j : κ) → Wiring (ι j) (In j) (Out j) (α' j) (β' j))
    (inner : (j : κ) → Block (α' j) (β' j))
    (hinner : ∀ j x, (inner j).impl x = wIn j x (impls (leaves j)))
    (wOut : Wiring κ α' β' α β)
    (a : Block α β)
    (hglue : ∀ x, a.impl x = wOut x (impls inner))
    (hleaves : ∀ j i, Proven (leaves j i)) :
    ∀ x, a.impl x = wOut x (fun j => (glue (leaves j) (wIn j)).spec) := by
  -- First certify each inner assembly against its composed specification.
  have hinnerProven :
      ∀ j, Proven { impl := (inner j).impl, spec := (glue (leaves j) (wIn j)).spec } :=
    fun j => glue_sound_assembly_block (leaves j) (wIn j) (inner j) (hinner j) (hleaves j)
  -- Then apply the one-level result to the outer assembly, whose children are
  -- the certified inner blocks.
  have h := glue_sound_assembly
    (fun j => ({ impl := (inner j).impl, spec := (glue (leaves j) (wIn j)).spec } : Block (α' j) (β' j)))
    wOut a hglue hinnerProven
  exact h

/-- Two-level nesting through `seq` and `par`: a parallel pair feeding a
    sequential stage. -/
theorem seq_par_nested_sound {α β γ δ ε : Type}
    (b1 : Block α β) (b2 : Block γ δ) (b3 : Block (β × δ) ε)
    (h1 : Proven b1) (h2 : Proven b2) (h3 : Proven b3) :
    Proven (seq (par b1 b2) b3) :=
  seq_sound (par b1 b2) b3 (par_sound b1 b2 h1 h2) h3

/-- A `glue` assembly used as a child of `seq`. -/
theorem seq_glue_nested_sound {ι : Type} {In Out : ι → Type} {α β γ : Type}
    (children : (i : ι) → Block (In i) (Out i))
    (w : Wiring ι In Out α β) (b : Block β γ)
    (hc : ∀ i, Proven (children i)) (hb : Proven b) :
    Proven (seq (glue children w) b) :=
  seq_sound (glue children w) b (glue_sound children w hc) hb

/-! ## List variant (homogeneous children)

When all children share one interface, a `List` is a convenient census. The
wiring receives the list of child evaluators. -/

/-- Glue over a list of homogeneous children. -/
def glueList {α β γ δ : Type}
    (children : List (Block α β))
    (w : γ → List (α → β) → δ) : Block γ δ :=
  { impl := fun x => w x (children.map Block.impl)
    spec := fun x => w x (children.map Block.spec) }

/-- Census on a list: every member is proven. -/
def AllProven {α β : Type} : List (Block α β) → Prop
  | [] => True
  | b :: bs => Proven b ∧ AllProven bs

/-- Pointwise proven implies equal as a function. -/
theorem Proven.impl_eq_spec {α β : Type} {b : Block α β} (h : Proven b) :
    b.impl = b.spec :=
  funext h

/-- The list census lemma. -/
theorem map_impl_eq_map_spec {α β : Type} :
    ∀ (children : List (Block α β)), AllProven children →
      children.map Block.impl = children.map Block.spec
  | [], _ => rfl
  | b :: bs, ⟨hb, hbs⟩ => by
    show b.impl :: bs.map Block.impl = b.spec :: bs.map Block.spec
    rw [hb.impl_eq_spec, map_impl_eq_map_spec bs hbs]

/-- Soundness of `glueList` (closed form). -/
theorem glueList_sound {α β γ δ : Type}
    (children : List (Block α β)) (w : γ → List (α → β) → δ)
    (hc : AllProven children) : Proven (glueList children w) := by
  intro x
  show w x (children.map Block.impl) = w x (children.map Block.spec)
  rw [map_impl_eq_map_spec children hc]

/-- Soundness of `glueList` (assembly form). -/
theorem glueList_sound_assembly {α β γ δ : Type}
    (children : List (Block α β)) (w : γ → List (α → β) → δ)
    (a : Block γ δ)
    (hglue : ∀ x, a.impl x = w x (children.map Block.impl))
    (hc : AllProven children) :
    ∀ x, a.impl x = w x (children.map Block.spec) := by
  intro x
  rw [hglue x, map_impl_eq_map_spec children hc]

/-! ## `seq` and `par` are instances of `glue`

Not needed for soundness (each has its own axiom-free proof above), but it
shows the three forms are one rule. -/

/-- A two-element index for binary compositions. -/
inductive Two where
  | fst | snd

/-- Sequential composition, expressed as a glue of two children. -/
theorem seq_as_glue {α β γ : Type} (b1 : Block α β) (b2 : Block β γ) :
    Proven (seq b1 b2) ↔
    Proven (glue (ι := Two)
      (In := fun i => match i with | .fst => α | .snd => β)
      (Out := fun i => match i with | .fst => β | .snd => γ)
      (fun i => match i with | .fst => b1 | .snd => b2)
      (fun (x : α) ev => ev .snd (ev .fst x))) :=
  Iff.rfl

/-- Parallel composition, expressed as a glue of two children. -/
theorem par_as_glue {α β γ δ : Type} (b1 : Block α β) (b2 : Block γ δ) :
    Proven (par b1 b2) ↔
    Proven (glue (ι := Two)
      (In := fun i => match i with | .fst => α | .snd => γ)
      (Out := fun i => match i with | .fst => β | .snd => δ)
      (fun i => match i with | .fst => b1 | .snd => b2)
      (fun (p : α × γ) ev => (ev .fst p.1, ev .snd p.2))) :=
  Iff.rfl

end Q2.Composition
