/-!
# Q2Composition market equilibrium: cost recovery, never rent

A machine-checked account of the reference-license economics in
`q2-composition`, instantiated with the MEASURED cost of proving Q2's MXFP4
GEMM tree.

The claim the contract makes in prose is "cost recovery, never rent". This file
proves the two halves of that claim over a model that mirrors the contract's
arithmetic exactly, then plugs in real numbers:

1. **Cap invariant.** `royalty_due = min(price, target − recovered)`, zero once
   recovered. Iterating it any number of times never pushes `recovered` past
   `target`. So the total a certificate can ever collect is bounded by its
   declared target, hence by the protocol cap `CAP`.
2. **Rent bound.** rent = collected − cost ≤ CAP − cost, for any listing.
3. **Free-entry equilibrium.** If an entrant can list at cost, no price above
   cost is stable (it is undercut). The only sustainable price is the cost
   itself, so equilibrium rent is zero.
4. **Instantiation.** With 80 W, Vermont's 24.44 ¢/kWh, and the measured proving
   time of the MXFP4 tree, the physical cost of the proof is far below the
   0.005 ETH cap, so an honest lister can fully recover it, and the maximum
   rent any lister could ever extract on it is computed exactly.

All money is in wei (ℕ). No mathlib, no `native_decide`, no axioms beyond the
kernel: the trusted base is Lean itself. Parameters (rate, ETH price, wattage)
are stated as definitions, not smuggled in; changing them changes the numbers,
not the theorems.
-/

namespace Q2.Market

/-- Protocol cap on a lister-declared recovery target: 0.005 ETH, in wei.
    Mirrors `MAX_RECOVERY_TARGET` in `q2-composition`. -/
def CAP : Nat := 5000000000000000

/-- A certificate's cost-recovery state. Mirrors the contract's storage for one
    certificate: `recovery_target`, `ref_price`, `recovered`. -/
structure Cert where
  target    : Nat   -- lister-declared listing gas; the contract enforces ≤ CAP
  price     : Nat   -- per-reference pacing price
  recovered : Nat   -- cumulative royalties collected so far

/-- What one reference owes right now. Mirrors `Q2Composition::royalty_due`:
    zero once recovered, otherwise `min(price, target − recovered)`. -/
def due (c : Cert) : Nat :=
  if c.target ≤ c.recovered then 0 else min c.price (c.target - c.recovered)

/-- One reference settles. Mirrors `pay_royalty`: `recovered += due`. -/
def pay (c : Cert) : Cert :=
  { c with recovered := c.recovered + due c }

/-- `n` references in a row. -/
def payN : Nat → Cert → Cert
  | 0,     c => c
  | n + 1, c => payN n (pay c)

/-! ## 1. The cap invariant -/

/-- One payment never pushes `recovered` past `target`. -/
theorem pay_le_target (c : Cert) (h : c.recovered ≤ c.target) :
    (pay c).recovered ≤ c.target := by
  show c.recovered + due c ≤ c.target
  unfold due
  split
  · omega
  · have hm := Nat.min_le_right c.price (c.target - c.recovered)
    omega

/-- Any number of payments stays within the target. This is the contract's
    "capped at its listing gas" guarantee, proved by induction on references. -/
theorem payN_le_target (n : Nat) (c : Cert) (h : c.recovered ≤ c.target) :
    (payN n c).recovered ≤ c.target := by
  induction n generalizing c with
  | zero => exact h
  | succ n ih => exact ih (pay c) (pay_le_target c h)

/-- A fresh certificate with a target within the cap can never collect more
    than the cap, however many times it is referenced. -/
theorem collected_le_cap (n t p : Nat) (ht : t ≤ CAP) :
    (payN n { target := t, price := p, recovered := 0 }).recovered ≤ CAP :=
  Nat.le_trans (payN_le_target n _ (Nat.zero_le _)) ht

/-! ## 2. The rent bound -/

/-- Rent is what is collected beyond the cost of producing the proof. For any
    listing within the cap it is bounded by `CAP − cost`. -/
theorem rent_le_cap_sub_cost (n t p cost : Nat) (ht : t ≤ CAP) :
    ((payN n { target := t, price := p, recovered := 0 }).recovered : Int) - cost
      ≤ (CAP : Int) - cost := by
  have := collected_le_cap n t p ht
  omega

/-! ## 3. Free-entry equilibrium -/

/-- An entrant can list the same proof at any price at or above the common cost
    (beat-or-fork lets them in for at most one reference's royalty). A listed
    price `p` is undercuttable if some such entrant price beats it. -/
def undercuttable (cost p : Nat) : Prop := ∃ q, cost ≤ q ∧ q < p

/-- A price is stable when no entrant can undercut it. -/
def stable (cost p : Nat) : Prop := ¬ undercuttable cost p

/-- The only sustainable price at or above cost is the cost itself. -/
theorem stable_iff_eq_cost (cost p : Nat) (hp : cost ≤ p) :
    stable cost p ↔ p = cost := by
  constructor
  · intro hs
    cases Nat.eq_or_lt_of_le hp with
    | inl h => exact h.symm
    | inr h => exact absurd ⟨cost, Nat.le_refl _, h⟩ hs
  · intro he ⟨q, hq1, hq2⟩
    omega

/-- Hence equilibrium rent is zero: price equals cost. -/
theorem equilibrium_rent_zero (cost p : Nat) (hp : cost ≤ p) (hs : stable cost p) :
    (p : Int) - cost = 0 := by
  have := (stable_iff_eq_cost cost p hp).1 hs
  omega

/-! ## 4. Instantiation: the measured cost of proving the MXFP4 tree

Parameters are explicit. Units are chosen so everything is an integer:
micro-dollars (µ$) for money, milli-hours (mh) for time, watts for power.
-/

/-- Machine power while proving, watts (as specified). -/
def POWER_W : Nat := 80

/-- Vermont residential electricity, µ$ per kWh: 24.44 ¢/kWh (Sept 2026). -/
def RATE_uUSD_per_kWh : Nat := 244400

/-- ETH price parameter, µ$ per ETH: $3,000. Change it and the wei figures
    move; the theorems do not. -/
def ETH_uUSD : Nat := 3000000000

/-- Measured compute time of the 23 completed MXFP4 proof runs (portal
    `analysis` table, completed − started): 3.724 h. -/
def COMPUTE_mh : Nat := 3724

/-- Wall-clock span of the MXFP4 build, first request to last completion:
    101.72 h. The upper bound if the machine ran the whole time. -/
def SPAN_mh : Nat := 101720

/-- Energy cost in µ$: W × mh × (µ$/kWh) / (1000 W/kW × 1000 mh/h). -/
def energy_uUSD (mh : Nat) : Nat := POWER_W * mh * RATE_uUSD_per_kWh / 1000000

/-- The same cost in wei at the ETH parameter. -/
def cost_wei (mh : Nat) : Nat := energy_uUSD mh * 1000000000000000000 / ETH_uUSD

/-- Cost of the proof on the machine-proving basis: ≈ 2.43e13 wei ≈ $0.073. -/
def COST_COMPUTE : Nat := cost_wei COMPUTE_mh

/-- Cost on the whole-span basis: ≈ 6.63e14 wei ≈ $1.99. -/
def COST_SPAN : Nat := cost_wei SPAN_mh

/-- The exact dollar figures, so no one has to trust the prose. -/
theorem energy_compute_uUSD : energy_uUSD COMPUTE_mh = 72811 := by decide
theorem energy_span_uUSD    : energy_uUSD SPAN_mh    = 1988829 := by decide

/-- The physical cost of the proof sits far below the cap on both bases, so an
    honest lister can declare the true cost as their target and recover all of
    it. The cap never prevents cost recovery; it only bounds extraction. -/
theorem cost_compute_lt_cap : COST_COMPUTE < CAP := by decide
theorem cost_span_lt_cap    : COST_SPAN    < CAP := by decide

/-- The most rent ANY lister could ever extract on the MXFP4 proof, even setting
    the target at the cap and being referenced forever, computed exactly. -/
theorem mxfp4_max_rent_wei_compute : CAP - COST_COMPUTE = 4975729666666667 := by decide
theorem mxfp4_max_rent_wei_span    : CAP - COST_SPAN    = 4337057000000000 := by decide

/-- The rent bound, instantiated on the measured cost. -/
theorem mxfp4_rent_bound (n t p : Nat) (ht : t ≤ CAP) :
    ((payN n { target := t, price := p, recovered := 0 }).recovered : Int) - COST_COMPUTE
      ≤ (CAP : Int) - COST_COMPUTE :=
  rent_le_cap_sub_cost n t p COST_COMPUTE ht

/-- And at free-entry equilibrium the MXFP4 proof sells at exactly its cost:
    rent is zero. -/
theorem mxfp4_equilibrium_price (p : Nat) (hp : COST_COMPUTE ≤ p)
    (hs : stable COST_COMPUTE p) : p = COST_COMPUTE :=
  (stable_iff_eq_cost COST_COMPUTE p hp).1 hs


/-! ## 5. The manufacturing license, priced per mask

The second economy, modeled honestly. A company taping out an SoC has the whole
RTL→GDSII flow and can prove the block itself; its own signoff would catch the
same bugs. So the certificate does NOT sell a de-risked mask spin, and it does
not sell saved compute (cents). What it sells is MAKE-VERSUS-BUY: the engineer
time and calendar the licensee would spend designing, proving, and signing off
an equivalent block. A rational buyer pays at most that replication cost,
spread over however many mask sets they will ship the block in.

"Per mask" is therefore the UNIT of the license (one payment per mask set the
block ships in), not a value anchor. The mask cost matters only for adoption:
the license is a rounding error on a tapeout, which is why buying beats
building.

Anchors (Sept 2026): sky130 chipIgnite shuttle $14,950; full 130 nm mask set
≈ $1.5M; replication of a signoff-clean block ≈ $4,000 (about four
engineer-days) for a team that already has the flow.
-/

/-- sky130 chipIgnite shuttle, µ$: $14,950. The unit a per-mask license rides on. -/
def SHUTTLE_uUSD : Nat := 14950000000

/-- Full 130 nm custom mask set, µ$: $1,500,000. -/
def MASKSET_uUSD : Nat := 1500000000000

/-- Replication cost for a team that has the RTL→GDSII flow, µ$: $4,000. This is
    the value of the license to a competent buyer, and the ceiling on what they
    will pay: above it, they build. -/
def REPLICATION_uUSD : Nat := 4000000000

/-- The Charter fraction of that value the designer charges, bps: 2000 = 20%. -/
def F_bps : Nat := 2000

/-- What a competent buyer gains by licensing instead of building: exactly the
    replication cost. Time-to-market is real extra value, left out to stay
    conservative. -/
def buyer_value : Nat := REPLICATION_uUSD

/-- A per-mask price `p` over `n` masks is accepted iff the total does not
    exceed what building would cost. -/
def accepts (p n : Nat) : Prop := n * p ≤ buyer_value

/-- Revenue ceiling per licensee, whatever the schedule: never more than
    replication. "They could just prove it themselves" is exactly this bound. -/
theorem revenue_le_replication (p n : Nat) (h : accepts p n) : n * p ≤ REPLICATION_uUSD := h

/-- The Charter price: a fraction of buyer value, so most of the surplus stays
    with the buyer, which is what makes buying beat building. This is the
    unlimited-use price, and the per-mask price for a single-mask buyer. -/
def charter_price : Nat := F_bps * buyer_value / 10000

/-- The Charter price never exceeds the buyer's value. -/
theorem charter_price_le_value : charter_price ≤ buyer_value := by
  unfold charter_price
  have h : F_bps * buyer_value ≤ 10000 * buyer_value :=
    Nat.mul_le_mul_right buyer_value (by decide : F_bps ≤ 10000)
  calc F_bps * buyer_value / 10000 ≤ 10000 * buyer_value / 10000 := Nat.div_le_div_right h
    _ = buyer_value := Nat.mul_div_cancel_left buyer_value (by decide : 0 < 10000)

/-- A single-mask buyer accepts the Charter price. -/
theorem single_mask_accepts : accepts charter_price 1 := by
  show 1 * charter_price ≤ buyer_value
  rw [Nat.one_mul]
  exact charter_price_le_value

/-- Per-mask pricing for a buyer expecting `n` masks: the Charter price spread
    over the masks, so the total stays at the Charter fraction and is accepted. -/
def per_mask_price (n : Nat) : Nat := charter_price / n

theorem per_mask_accepts (n : Nat) : accepts (per_mask_price n) n := by
  show n * (charter_price / n) ≤ buyer_value
  exact Nat.le_trans (Nat.mul_div_le charter_price n) charter_price_le_value

/-! ### The numbers, kernel-checked. -/

/-- The Charter price on a $4,000 replication cost: $800. -/
theorem charter_price_usd : charter_price = 800000000 := by decide

/-- What the buyer keeps by licensing rather than building: $3,200, plus the
    calendar. This surplus is why a competent buyer still buys. -/
theorem buyer_keeps : buyer_value - charter_price = 3200000000 := by decide

/-- Affordability, the only role the mask cost plays: the license as a share of
    the tapeout it ships in. 535 bps (5.35%) of a shuttle slot; 5 bps (0.05%)
    of a full mask set. A rounding error on the spin. -/
def share_bps (price tapeout : Nat) : Nat := price * 10000 / tapeout
theorem shuttle_share : share_bps charter_price SHUTTLE_uUSD = 535 := by decide
theorem maskset_share : share_bps charter_price MASKSET_uUSD = 5 := by decide


/-! ### The incumbent segment (Intel, NVIDIA, Marvell)

For a fabless incumbent the block-level make-versus-buy is trivially small: they
can replicate any single block for pocket change, so a block certificate earns
no leverage. Their replication cost is nonetheless higher than a small team's,
because it is paid at their loaded rate and their signoff rigor (formal, DFT,
corner analysis): 2–6 engineer-weeks of a senior engineer at about $1,600/day,
i.e. $16k–$50k per block. We instantiate the $30k midpoint. The seat at the
table comes from the commons, the method, and the patent-pending attestation
primitive, not from this number; this number is only the per-block ceiling. -/

/-- Incumbent replication cost per block, µ$: $30,000 (midpoint of $16k–$50k). -/
def REPLICATION_INCUMBENT_uUSD : Nat := 30000000000

/-- The Charter price for an incumbent: 20% of their replication cost. -/
def charter_price_incumbent : Nat := F_bps * REPLICATION_INCUMBENT_uUSD / 10000

/-- Never above what building costs them. -/
theorem charter_incumbent_le_replication : charter_price_incumbent ≤ REPLICATION_INCUMBENT_uUSD := by
  unfold charter_price_incumbent
  have h : F_bps * REPLICATION_INCUMBENT_uUSD ≤ 10000 * REPLICATION_INCUMBENT_uUSD :=
    Nat.mul_le_mul_right REPLICATION_INCUMBENT_uUSD (by decide : F_bps ≤ 10000)
  calc F_bps * REPLICATION_INCUMBENT_uUSD / 10000
      ≤ 10000 * REPLICATION_INCUMBENT_uUSD / 10000 := Nat.div_le_div_right h
    _ = REPLICATION_INCUMBENT_uUSD := Nat.mul_div_cancel_left _ (by decide : 0 < 10000)

/-- $6,000 per block; the incumbent keeps $24,000 of value plus the calendar. -/
theorem charter_incumbent_usd : charter_price_incumbent = 6000000000 := by decide
theorem incumbent_keeps : REPLICATION_INCUMBENT_uUSD - charter_price_incumbent = 24000000000 := by decide

/-- Even at $6,000 the license is 0.4% of a $1.5M mask set: still a rounding
    error on the spin, so inclusion costs them nothing they would notice. -/
theorem incumbent_maskset_share : share_bps charter_price_incumbent MASKSET_uUSD = 40 := by decide


/-! ## 6. The floor: $100 per mask, SoC down

Limit pricing at marginal cost. Instead of pricing each buyer near their own
replication cost, set ONE price so far below every replication cost that no
entrant can survive under it whatever compute or headcount they bring, while
every buyer finds it too small to refuse. It works because Q2's marginal cost
per license is zero (the proofs are sunk) and an entrant's replication cost is
not: the cost of producing proven silicon collapses THROUGH the certified
commons (compose proven parts), and anyone taking that route is a participant;
building outside it pays full replication, which does not go to zero.

Scope: one fee per mask set, licensed at the top (SoC-level) certificate, whose
lineage was already settled by composition, so every certified block in that
mask is covered: "SoC down". -/

/-- The floor, µ$: $100 per mask set. -/
def FLOOR_uUSD : Nat := 100000000

/-- Q2's marginal cost of one more license: zero. The proofs are sunk. -/
def MARGINAL_uUSD : Nat := 0

/-- Masks an entrant with replication cost `R` must sell at the floor just to
    break even. Q2 is in profit on the first one. -/
def entrant_breakeven_masks (R : Nat) : Nat := R / FLOOR_uUSD

theorem small_team_entrant_breakeven : entrant_breakeven_masks REPLICATION_uUSD = 40 := by decide
theorem incumbent_entrant_breakeven  : entrant_breakeven_masks REPLICATION_INCUMBENT_uUSD = 300 := by decide

/-- Q2 can always price at or below any entrant who must recoup a replication
    cost over `m` masks, because Q2's own floor is zero. -/
theorem q2_undercuts_any_entrant (R m : Nat) : MARGINAL_uUSD ≤ R / m := Nat.zero_le _

/-- Every license at the floor is pure margin. -/
theorem floor_is_margin : MARGINAL_uUSD < FLOOR_uUSD := by decide

/-- Every buyer accepts: the floor is below every replication cost. -/
theorem floor_lt_small_team : FLOOR_uUSD < REPLICATION_uUSD := by decide
theorem floor_lt_incumbent  : FLOOR_uUSD < REPLICATION_INCUMBENT_uUSD := by decide

/-- A buyer accepts per-mask pricing at the floor while their total stays under
    replication: up to `R / FLOOR` masks. Past that an unlimited tier keeps them;
    the crossover is explicit, never hidden. -/
abbrev accepts_floor (R n : Nat) : Prop := n * FLOOR_uUSD ≤ R
theorem small_team_accepts_upto_40 : accepts_floor REPLICATION_uUSD 40 := by decide
theorem incumbent_accepts_upto_300 : accepts_floor REPLICATION_INCUMBENT_uUSD 300 := by decide

/-- Producing the IEEE 754 library costs about $100k (the cost estimate). At
    the floor that is 1,000 masks to break even. -/
def LIBRARY_FIXED_uUSD : Nat := 100000000000
theorem library_breakeven_masks : LIBRARY_FIXED_uUSD / FLOOR_uUSD = 1000 := by decide

/-- A comfortable $120k/yr is 1,200 masks a year at the floor. The model is
    volume, and the floor is what produces the volume. -/
def INCOME_TARGET_uUSD : Nat := 120000000000
theorem income_masks_per_year : INCOME_TARGET_uUSD / FLOOR_uUSD = 1200 := by decide

/-- Adoption: the floor is 66 bps (0.66%) of a shuttle slot, and it rounds to
    ZERO basis points of a full mask set. There is nothing to refuse. -/
theorem floor_shuttle_share : share_bps FLOOR_uUSD SHUTTLE_uUSD = 66 := by decide
theorem floor_maskset_share : share_bps FLOOR_uUSD MASKSET_uUSD = 0 := by decide


/-! ## 7. Capstone: what the AI produced it for, what the floor returns

The MXFP4 GEMM tree was constructed by AI through the certified commons for
$1.99 of electricity on the creation-span basis (7.3 cents on proving compute
alone; both proved in Section 4). The floor returns $100 per mask. Production is
a ONE-TIME cost, recovered on the first mask; every mask after that is the full
floor, because the marginal cost of a license is zero. The margin is what funds
the objective: reshoring manufacturing on a product that costs two dollars to
make and cannot be undercut. -/

/-- What the AI paid to produce the whole MXFP4 tree, µ$: $1.99 (creation-span
    basis, kernel-checked in Section 4). -/
def PRODUCTION_uUSD : Nat := energy_uUSD SPAN_mh

theorem production_usd : PRODUCTION_uUSD = 1988829 := by decide

/-- Production is recovered on the very first mask. -/
theorem production_lt_floor : PRODUCTION_uUSD < FLOOR_uUSD := by decide

/-- Margin on the first mask, after recovering production: $98.01. -/
theorem first_mask_margin : FLOOR_uUSD - PRODUCTION_uUSD = 98011171 := by decide

/-- Margin on every subsequent mask: the full $100, marginal cost being zero. -/
theorem subsequent_mask_margin : FLOOR_uUSD - MARGINAL_uUSD = 100000000 := by decide

/-- The asymmetry that makes the floor unbeatable "no matter the compute or
    personnel": a human-engineered replication ($4,000) costs 2,011 times what
    the AI-plus-commons pipeline paid to produce the tree. -/
theorem replication_over_production : REPLICATION_uUSD / PRODUCTION_uUSD = 2011 := by decide

/-- The AI production cost is under 2% of the floor. -/
theorem production_share_of_floor : share_bps PRODUCTION_uUSD FLOOR_uUSD = 198 := by decide

/-- Annual margin at the income-target volume of 1,200 masks: $119,998.01
    (1,200 × $100 minus the one-time $1.99). One more mask clears $120k. -/
theorem annual_margin_1200 : 1200 * FLOOR_uUSD - PRODUCTION_uUSD = 119998011171 := by decide
theorem income_cleared_at_1201 : INCOME_TARGET_uUSD ≤ 1201 * FLOOR_uUSD - PRODUCTION_uUSD := by decide

/-- The reshoring rate: every 1,000 masks of a $2 product returns $99,998 of
    margin to a domestic designer. -/
theorem reshoring_per_1000_masks : 1000 * FLOOR_uUSD - PRODUCTION_uUSD = 99998011171 := by decide


/-! ## 8. The descending floor: converging on the physical cost

$100 is the first floor, not the equilibrium. As adoption grows the floor is
walked down, and the market converges on a price that reflects what a proof
PHYSICALLY costs to produce and settle (energy, compute, on-chain gas), not the
human-labor premium that makes replication cost $4k–$30k today. Three things
are proved: the true per-mask physical cost falls with volume; deterrence
strengthens as the floor falls; and a safe-descent rule, the floor drops only
as fast as adoption pays for it, keeps the business solvent at every step,
with the exact volume required at each floor computed. The elasticity of
demand (does volume rise as the floor falls?) is the one empirical bet; every
theorem here makes that bet testable at each step rather than assumed. -/

/-- On-chain settlement per mask (the consume transaction), µ$: about 1 cent. -/
def GAS_PER_MASK_uUSD : Nat := 10000

/-- The true physical cost of one mask at volume `v`: the one-time production
    amortized over the masks, plus settlement. -/
def phys_per_mask (v : Nat) : Nat := PRODUCTION_uUSD / v + GAS_PER_MASK_uUSD

/-- Physical cost per mask falls as volume rises. -/
theorem phys_antitone (v w : Nat) (hv : 0 < v) (h : v ≤ w) :
    phys_per_mask w ≤ phys_per_mask v := by
  unfold phys_per_mask
  exact Nat.add_le_add_right (Nat.div_le_div_left h hv) _

/-- The Charter's lower bound on any floor: never below the physical cost, so
    the price converges on it from above and never subsidizes below it. -/
abbrev floor_ok (p v : Nat) : Prop := phys_per_mask v ≤ p

/-- Deterrence strengthens as the floor falls: an entrant needs MORE masks to
    break even at a lower floor. -/
theorem breakeven_mono (R p q : Nat) (hq : 0 < q) (h : q ≤ p) : R / p ≤ R / q :=
  Nat.div_le_div_left h hq

/-- Solvency at a floor: volume times margin over physical cost meets the
    income target. This is the safe-descent test, applied before each drop. -/
abbrev comfortable (p v : Nat) : Prop := INCOME_TARGET_uUSD ≤ v * (p - phys_per_mask v)

/-! ### The descent ladder, kernel-checked: the volume each floor needs. -/

/-- At the $100 floor the physical cost per mask is $0.0117 (1.2 cents), so the
    floor is ~8,600× the physical cost: the room to descend is enormous. -/
theorem phys_at_1200 : phys_per_mask 1200 = 11657 := by decide

/-- $100 per mask: 1,201 masks a year is comfortable (1,200 is $1.99 short). -/
theorem ladder_100  : comfortable 100000000 1201 := by decide
/-- $10 per mask: 12,100 masks. The floor fell 10×; volume must rise ~10×. -/
theorem ladder_10   : comfortable 10000000 12100 := by decide
/-- $1 per mask: 122,000 masks. -/
theorem ladder_1    : comfortable 1000000 122000 := by decide
/-- 10 cents per mask: 1.34 million masks. The scale of a reshored industry. -/
theorem ladder_0_10 : comfortable 100000 1340000 := by decide

/-- The physical-cost equilibrium: at a million masks the true cost per mask is
    1.0 cents, dominated by settlement gas; production has amortized to nothing.
    This is the price the market converges on, and it is where extraction ends. -/
theorem phys_at_1M : phys_per_mask 1000000 = 10001 := by decide

/-- At that equilibrium a floor of 2 cents is still above physical cost and
    still deters entry: an entrant with a $4,000 replication cost would need
    200,000 masks to break even. -/
theorem equilibrium_floor_ok : floor_ok 20000 1000000 := by decide
theorem equilibrium_deterrence : REPLICATION_uUSD / 20000 = 200000 := by decide

end Q2.Market
