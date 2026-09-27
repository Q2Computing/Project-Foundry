//! Q2Composition, proof certificates that license into larger proofs, and into
//! manufactured silicon.
//!
//! PUBLIC, disclosure-safe. Companion to `q2-anchor` (record a commitment) and
//! `q2-verifier` (the chain re-runs a bounded proof). This contract is the
//! financial instrument for proof-by-construction and for a remote VLSI economy
//! that depends on no company, only on a contract releasing a model for use.
//!
//! Two license classes, economically distinct on purpose:
//!
//! 1. REFERENCE (the commons economy). A proof of a small block is a certificate;
//!    a larger system is certified by REFERENCING child certificates the chain
//!    already holds, never the child design. Referencing pays a per-reference
//!    royalty ONLY to the abstractions you directly use, the child certificates
//!    you name, never to the recursion beneath them: each deeper level was
//!    already settled once, when that abstraction was composed. Every certificate
//!    is CAPPED at its lister-declared listing gas: once that gas is recovered
//!    the certificate is free forever. Foundry-PDK primitives are `commons`, free
//!    from the start. This is cost recovery, never rent, by construction.
//!
//!    Beat-or-fork rule: whoever beats you pays your listing cost. Proving
//!    "better than X" measures against X's proven baseline, which is a reference
//!    to X. So a new certificate claiming an interface that is already certified
//!    must name its `baseline` (the incumbent it beat or forked) and settle that
//!    incumbent's remaining recovery. A competing implementation cannot be listed
//!    silently. Once the incumbent is recovered, forking it is free: the proven
//!    basis has become commons, which is the intended end state.
//!
//! 2. MANUFACTURING (the designer's product). The right to put a design into a
//!    fabricated SoC. The design itself is disclosed only to a designer-authorized
//!    third-party FOUNDRY, never to the licensee; the contract gates release and
//!    the foundry enforces the terms by consuming the license as it manufactures.
//!    Terms are the designer's to set and price (single express-shuttle die,
//!    quantity-limited, per use, unlimited, or free public release).
//!
//! The protocol takes zero in both classes. Value is conserved: every wei paid is
//! credited to a certificate owner or refunded to the payer, and withdrawn by pull.
//!
//! What stays off-chain, stated plainly: the deep functional composition proof
//! (that a parent equals the composition of its children's interfaces) is
//! produced by the lab's prover and committed as `artifact_hash`; this contract
//! settles lineage, binding and licensing, it does not re-run that proof.
#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use alloc::vec::Vec;
use alloy_sol_types::sol;
use stylus_sdk::{
    alloy_primitives::{Address, FixedBytes, U16, U64, U256, U8},
    block,
    call::transfer_eth,
    crypto::keccak,
    evm, msg,
    prelude::*,
};

// Manufacturing terms menu. 0 = no offer published.
const TERMS_NONE: u8 = 0;
const TERMS_FREE_PUBLIC: u8 = 1;        // released to the public, free
const TERMS_SINGLE_SHUTTLE_DIE: u8 = 2; // one express shuttle, one die, consumed on use
const TERMS_QUANTITY_LIMITED: u8 = 3;   // N manufactured components, decremented by the foundry
const TERMS_PER_USE: u8 = 4;            // pay the price on every consumed unit
const TERMS_UNLIMITED: u8 = 5;          // one payment, unlimited manufacture

// Protocol cap on a lister-declared recovery target: 0.005 ETH. Real listing
// gas on Arbitrum is cents, so this is still generous, and it bounds two attacks
// at once: rent disguised as "listing gas", and interface squatting (registering
// someone's interface first with an extortionate price). Adjust deliberately.
const MAX_RECOVERY_TARGET: U256 = U256::from_limbs([5_000_000_000_000_000, 0, 0, 0]);

sol! {
    event CertificateRegistered(
        uint256 indexed id,
        address indexed owner,
        bytes32 artifact_hash,
        bytes32 interface_hash,
        uint16 proof_kind,
        bool commons,
        uint256 ref_price,
        uint256 recovery_target,
        uint64 timestamp
    );
    event SystemCertified(
        uint256 indexed id,
        address indexed submitter,
        bytes32 system_hash,
        uint64 child_count,
        uint256 royalties_paid
    );
    event RoyaltyPaid(uint256 indexed cert, address indexed payer, uint256 amount, uint256 recovered, uint256 target);
    event BaselineSettled(uint256 indexed cert, uint256 indexed baseline, uint256 amount);
    event ManufacturingOffer(uint256 indexed cert, uint8 terms, uint256 price, uint256 quantity, address foundry, bytes32 package_hash);
    event BeatClaimed(uint256 indexed cert, uint256 indexed baseline, bytes32 improvement_ref);
    event LicenseIssued(uint256 indexed lic, uint256 indexed cert, address indexed licensee, uint8 terms, uint256 paid);
    event LicenseConsumed(uint256 indexed lic, uint256 units, uint256 remaining, uint256 paid);
    event DisclosureRecorded(uint256 indexed lic, bytes32 package_hash);
    event Withdrawn(address indexed owner, uint256 amount);

    error UnknownCertificate();
    error NoChildren();
    error BindingMismatch();
    error Underpaid();
    error NothingOwed();
    error TransferFailed();
    error NotOwner();
    error NotFoundry();
    error BadTerms();
    error NoManufacturingOffer();
    error UnknownLicense();
    error LicenseInactive();
    error InsufficientUnits();
    error Overflow();
    error NoDisclosure();
    error BaselineRequired();
    error BaselineMismatch();
    error PackageRequired();
    error PackageMismatch();
    error NoBaseline();
    error ImprovementRequired();
    error TargetTooHigh();
}

#[derive(SolidityError)]
pub enum CompositionError {
    UnknownCertificate(UnknownCertificate),
    NoChildren(NoChildren),
    BindingMismatch(BindingMismatch),
    Underpaid(Underpaid),
    NothingOwed(NothingOwed),
    TransferFailed(TransferFailed),
    NotOwner(NotOwner),
    NotFoundry(NotFoundry),
    BadTerms(BadTerms),
    NoManufacturingOffer(NoManufacturingOffer),
    UnknownLicense(UnknownLicense),
    LicenseInactive(LicenseInactive),
    InsufficientUnits(InsufficientUnits),
    Overflow(Overflow),
    NoDisclosure(NoDisclosure),
    BaselineRequired(BaselineRequired),
    BaselineMismatch(BaselineMismatch),
    PackageRequired(PackageRequired),
    PackageMismatch(PackageMismatch),
    NoBaseline(NoBaseline),
    ImprovementRequired(ImprovementRequired),
    TargetTooHigh(TargetTooHigh),
}

sol_storage! {
    #[entrypoint]
    pub struct Q2Composition {
        // ── certificates ─────────────────────────────────────────────────────
        uint256 cert_count;
        mapping(uint256 => bytes32) artifact_hash;    // commitment to the proof artifact (never the design)
        mapping(uint256 => bytes32) interface_hash;    // the interface a parent may rely on
        mapping(uint256 => uint16)  proof_kind;
        mapping(uint256 => address) owner;
        mapping(uint256 => bool)    is_composition;
        mapping(uint256 => uint64)  registered_at;
        // reference license: cost recovery
        mapping(uint256 => bool)    commons;           // PDK primitive: free forever, cannot be priced
        mapping(uint256 => uint256) ref_price;         // per-reference royalty; only paces recovery
        mapping(uint256 => uint256) recovery_target;   // lister-declared listing gas, in wei
        mapping(uint256 => uint256) recovered;         // cumulative collected; collection stops at target
        // lineage
        mapping(uint256 => uint256) child_count;
        mapping(uint256 => mapping(uint256 => uint256)) child_at;
        // beat-or-fork: the first certificate to claim an interface, and the
        // baseline each later claimant of that interface settled against
        mapping(bytes32 => uint256) interface_first;
        mapping(uint256 => uint256) baseline_of;
        // manufacturing offer (the designer's product)
        mapping(uint256 => uint8)   mfg_terms;
        mapping(uint256 => uint256) mfg_price;         // per license, or per unit for TERMS_PER_USE
        mapping(uint256 => uint256) mfg_quantity;      // units included, for TERMS_QUANTITY_LIMITED
        mapping(uint256 => address) foundry;           // designer-authorized third party that consumes licenses
        mapping(uint256 => bytes32) mfg_package;       // designer's commitment to the package the foundry must receive
        // beat vs fork: a fork names a baseline and pays; a beat additionally
        // references a recorded improvement (a verifier champion or anchor id)
        mapping(uint256 => bytes32) beat_ref;

        // ── manufacturing licenses ───────────────────────────────────────────
        uint256 lic_count;
        mapping(uint256 => uint256) lic_cert;
        mapping(uint256 => address) lic_licensee;
        mapping(uint256 => uint8)   lic_terms;
        mapping(uint256 => uint256) lic_remaining;     // units left (quantity / single die); MAX for unlimited & free
        mapping(uint256 => uint256) lic_uses;          // units consumed so far
        mapping(uint256 => bool)    lic_active;
        mapping(uint256 => bytes32) lic_disclosure;    // hash of the package the foundry received
        // The deal is frozen at purchase. A designer changing the offer later
        // (price, foundry, package) cannot alter a license already sold.
        mapping(uint256 => uint256) lic_unit_price;    // per-unit price for TERMS_PER_USE, as sold
        mapping(uint256 => address) lic_foundry;       // the foundry authorized for THIS license
        mapping(uint256 => bytes32) lic_package;       // the package commitment the foundry must match

        // ── pull payments ────────────────────────────────────────────────────
        mapping(address => uint256) owed;
    }
}

// Private helpers, not part of the ABI.
impl Q2Composition {
    fn credit(&mut self, who: Address, amount: U256) {
        if amount == U256::ZERO {
            return;
        }
        let cur = self.owed.get(who);
        self.owed.setter(who).set(cur + amount);
    }

    fn check_cert(&self, id: U256) -> Result<(), CompositionError> {
        if id == U256::ZERO || id > self.cert_count.get() {
            return Err(CompositionError::UnknownCertificate(UnknownCertificate {}));
        }
        Ok(())
    }

    /// The distinct certificates a composition directly references. A child
    /// named more than once (say 32 instances of one lane multiplier) is one
    /// abstraction used, so it is charged once.
    fn distinct(&self, ids: &[U256]) -> Vec<U256> {
        let mut out: Vec<U256> = Vec::new();
        for id in ids {
            if !out.contains(id) {
                out.push(*id);
            }
        }
        out
    }

    /// Capped royalty due for one certificate right now: its per-reference
    /// price, but never more than what remains of its recovery target, and
    /// zero once recovered or if it is commons.
    fn royalty_due(&self, id: U256) -> U256 {
        if self.commons.get(id) {
            return U256::ZERO;
        }
        let target = self.recovery_target.get(id);
        let got = self.recovered.get(id);
        if got >= target {
            return U256::ZERO;
        }
        let price = self.ref_price.get(id);
        let gap = target - got;
        if price < gap { price } else { gap }
    }

    /// Pay a capped royalty to a certificate's owner and advance its recovery.
    fn pay_royalty(&mut self, cert: U256, amount: U256) {
        if amount == U256::ZERO {
            return;
        }
        let owner = self.owner.get(cert);
        self.credit(owner, amount);
        let got = self.recovered.get(cert) + amount;
        self.recovered.setter(cert).set(got);
        evm::log(RoyaltyPaid {
            cert, payer: msg::sender(), amount,
            recovered: got, target: self.recovery_target.get(cert),
        });
    }

    /// The beat-or-fork rule. If `interface_hash` is already certified, the
    /// newcomer must name a `baseline` with that same interface and owes its
    /// remaining recovery. Returns (interface already existed, amount due).
    fn baseline_due(&self, interface_hash: FixedBytes<32>, baseline: U256) -> Result<(bool, U256), CompositionError> {
        let first = self.interface_first.get(interface_hash);
        if first == U256::ZERO {
            if baseline != U256::ZERO {
                return Err(CompositionError::BaselineMismatch(BaselineMismatch {}));
            }
            return Ok((false, U256::ZERO));
        }
        if baseline == U256::ZERO {
            return Err(CompositionError::BaselineRequired(BaselineRequired {}));
        }
        self.check_cert(baseline)?;
        if self.interface_hash.get(baseline) != interface_hash {
            return Err(CompositionError::BaselineMismatch(BaselineMismatch {}));
        }
        Ok((true, self.royalty_due(baseline)))
    }

    /// After minting `id`: record its baseline, or claim the interface if first.
    fn bind_interface(&mut self, id: U256, interface_hash: FixedBytes<32>, existed: bool, baseline: U256) {
        if existed {
            self.baseline_of.setter(id).set(baseline);
        } else {
            self.interface_first.setter(interface_hash).set(id);
        }
    }
}

#[public]
impl Q2Composition {
    // ── certificates & the reference license ────────────────────────────────

    /// Register a leaf proof certificate. Permissionless: anyone may prove at
    /// any level of entry, paying only gas. `commons=true` marks a foundry PDK
    /// primitive: free to reference forever and unpriceable. Otherwise
    /// `ref_price` paces recovery of `recovery_target`, the lister-declared
    /// listing gas; collection stops there. If `interface_hash` is already
    /// certified, `baseline` must name the incumbent and its remaining recovery
    /// is owed (beat-or-fork); for a new interface, `baseline` must be 0.
    #[payable]
    pub fn register(
        &mut self,
        artifact_hash: FixedBytes<32>,
        interface_hash: FixedBytes<32>,
        proof_kind: u16,
        commons: bool,
        ref_price: U256,
        recovery_target: U256,
        baseline: U256,
    ) -> Result<U256, CompositionError> {
        if !commons && recovery_target > MAX_RECOVERY_TARGET {
            return Err(CompositionError::TargetTooHigh(TargetTooHigh {}));
        }
        let (existed, due) = self.baseline_due(interface_hash, baseline)?;
        let paid = msg::value();
        if paid < due {
            return Err(CompositionError::Underpaid(Underpaid {}));
        }
        let id = self.cert_count.get() + U256::from(1);
        self.cert_count.set(id);
        self.artifact_hash.setter(id).set(artifact_hash);
        self.interface_hash.setter(id).set(interface_hash);
        self.proof_kind.setter(id).set(U16::from(proof_kind));
        self.owner.setter(id).set(msg::sender());
        self.is_composition.setter(id).set(false);
        let ts = block::timestamp();
        self.registered_at.setter(id).set(U64::from(ts));
        let (rp, rt) = if commons { (U256::ZERO, U256::ZERO) } else { (ref_price, recovery_target) };
        self.commons.setter(id).set(commons);
        self.ref_price.setter(id).set(rp);
        self.recovery_target.setter(id).set(rt);
        // Beat-or-fork settlement: the newcomer repays the incumbent's remaining
        // listing gas. Any excess is the caller's to withdraw.
        if existed {
            self.pay_royalty(baseline, due);
            evm::log(BaselineSettled { cert: id, baseline, amount: due });
        }
        if paid > due {
            self.credit(msg::sender(), paid - due);
        }
        self.bind_interface(id, interface_hash, existed, baseline);
        evm::log(CertificateRegistered {
            id, owner: msg::sender(), artifact_hash, interface_hash, proof_kind,
            commons, ref_price: rp, recovery_target: rt, timestamp: ts,
        });
        Ok(id)
    }

    /// Certify a larger system by reference. The contract recomputes
    /// keccak(system_hash ‖ interface_hash ‖ each direct child's REGISTERED
    /// interface_hash) and requires it to equal `binding`, so the parent is bound
    /// to exactly those certified interfaces and no child design was needed.
    /// Royalties go ONLY to the direct children, the abstractions this system
    /// actually uses, each capped at its recovery target; the recursion beneath
    /// them was settled once when those abstractions were composed. Excess
    /// payment is credited back to the caller. Mints the parent as a new
    /// certificate, licensable one rung up. If `interface_hash` is already
    /// certified, `baseline` must name the incumbent and its remaining recovery
    /// is owed too (beat-or-fork); for a new interface, `baseline` must be 0.
    #[payable]
    pub fn certify(
        &mut self,
        system_hash: FixedBytes<32>,
        interface_hash: FixedBytes<32>,
        proof_kind: u16,
        child_ids: Vec<U256>,
        binding: FixedBytes<32>,
        ref_price: U256,
        recovery_target: U256,
        baseline: U256,
    ) -> Result<U256, CompositionError> {
        let n = child_ids.len();
        if n == 0 {
            return Err(CompositionError::NoChildren(NoChildren {}));
        }
        if recovery_target > MAX_RECOVERY_TARGET {
            return Err(CompositionError::TargetTooHigh(TargetTooHigh {}));
        }
        // Binding over the DIRECT children's registered interfaces.
        let mut buf: Vec<u8> = Vec::with_capacity(64 + n * 32);
        buf.extend_from_slice(system_hash.as_slice());
        buf.extend_from_slice(interface_hash.as_slice());
        for i in 0..n {
            self.check_cert(child_ids[i])?;
            buf.extend_from_slice(self.interface_hash.get(child_ids[i]).as_slice());
        }
        let recomputed: FixedBytes<32> = keccak(&buf);
        if recomputed != binding {
            return Err(CompositionError::BindingMismatch(BindingMismatch {}));
        }

        // Capped royalties to the direct abstractions used, and nothing deeper,
        // plus the beat-or-fork settlement if this interface is already certified.
        let used = self.distinct(&child_ids);
        let (existed, mut bdue) = self.baseline_due(interface_hash, baseline)?;
        // A baseline that is also a referenced child is paid once, as a child.
        if existed && used.contains(&baseline) {
            bdue = U256::ZERO;
        }
        // Checked, never wrapping: in a release build an overflowing sum would
        // wrap toward zero, let the underpaid check pass, and mint a
        // certification for free while crediting royalties the contract cannot
        // cover.
        let mut total = bdue;
        for id in used.iter() {
            total = total
                .checked_add(self.royalty_due(*id))
                .ok_or(CompositionError::Overflow(Overflow {}))?;
        }
        let paid = msg::value();
        if paid < total {
            return Err(CompositionError::Underpaid(Underpaid {}));
        }
        for id in used.iter() {
            let due = self.royalty_due(*id);
            self.pay_royalty(*id, due);
        }
        if bdue > U256::ZERO {
            self.pay_royalty(baseline, bdue);
        }
        if paid > total {
            self.credit(msg::sender(), paid - total);
        }

        // Mint the parent: it can now be referenced one rung up.
        let id = self.cert_count.get() + U256::from(1);
        self.cert_count.set(id);
        self.artifact_hash.setter(id).set(system_hash);
        self.interface_hash.setter(id).set(interface_hash);
        self.proof_kind.setter(id).set(U16::from(proof_kind));
        self.owner.setter(id).set(msg::sender());
        self.is_composition.setter(id).set(true);
        self.registered_at.setter(id).set(U64::from(block::timestamp()));
        self.commons.setter(id).set(false);
        self.ref_price.setter(id).set(ref_price);
        self.recovery_target.setter(id).set(recovery_target);
        self.child_count.setter(id).set(U256::from(n));
        for i in 0..n {
            self.child_at.setter(id).setter(U256::from(i)).set(child_ids[i]);
        }
        self.bind_interface(id, interface_hash, existed, baseline);
        if existed {
            evm::log(BaselineSettled { cert: id, baseline, amount: bdue });
        }
        evm::log(SystemCertified {
            id, submitter: msg::sender(), system_hash,
            child_count: n as u64, royalties_paid: total,
        });
        Ok(id)
    }

    /// Re-pace recovery of a certificate you own. Commons cannot be priced.
    pub fn set_ref_price(&mut self, id: U256, price: U256) -> Result<(), CompositionError> {
        self.check_cert(id)?;
        if self.owner.get(id) != msg::sender() {
            return Err(CompositionError::NotOwner(NotOwner {}));
        }
        if self.commons.get(id) {
            return Err(CompositionError::BadTerms(BadTerms {}));
        }
        self.ref_price.setter(id).set(price);
        Ok(())
    }

    // ── the manufacturing license ───────────────────────────────────────────

    /// Publish (or withdraw, with terms=0) a manufacturing offer on a
    /// certificate you own, authorize the third-party foundry that will receive
    /// the design and consume licenses, and COMMIT to the package that foundry
    /// must receive (`package_hash`). The foundry can later only record a
    /// disclosure that matches this commitment, so the chain proves it got the
    /// certified design, not merely "a package". This is the designer's
    /// product: priced by the designer, not gas-capped.
    pub fn set_manufacturing_terms(
        &mut self,
        id: U256,
        terms: u8,
        price: U256,
        quantity: U256,
        foundry: Address,
        package_hash: FixedBytes<32>,
    ) -> Result<(), CompositionError> {
        self.check_cert(id)?;
        if self.owner.get(id) != msg::sender() {
            return Err(CompositionError::NotOwner(NotOwner {}));
        }
        if terms > TERMS_UNLIMITED {
            return Err(CompositionError::BadTerms(BadTerms {}));
        }
        if terms == TERMS_QUANTITY_LIMITED && quantity == U256::ZERO {
            return Err(CompositionError::BadTerms(BadTerms {}));
        }
        // Every confidential handoff needs a committed package. Free public
        // releases have no confidential handoff to commit to.
        if terms != TERMS_NONE && terms != TERMS_FREE_PUBLIC && package_hash == FixedBytes::<32>::ZERO {
            return Err(CompositionError::PackageRequired(PackageRequired {}));
        }
        self.mfg_terms.setter(id).set(U8::from(terms));
        self.mfg_price.setter(id).set(price);
        self.mfg_quantity.setter(id).set(quantity);
        self.foundry.setter(id).set(foundry);
        self.mfg_package.setter(id).set(package_hash);
        evm::log(ManufacturingOffer { cert: id, terms, price, quantity, foundry, package_hash });
        Ok(())
    }

    /// Take a manufacturing license on a certificate under its published terms.
    /// The licensee never receives the design; it is released to the foundry.
    /// Payment goes to the designer in full. Per-use terms pay nothing here and
    /// pay on each consumed unit instead.
    #[payable]
    pub fn buy_license(&mut self, cert: U256) -> Result<U256, CompositionError> {
        self.check_cert(cert)?;
        let terms = self.mfg_terms.get(cert).to::<u8>();
        if terms == TERMS_NONE {
            return Err(CompositionError::NoManufacturingOffer(NoManufacturingOffer {}));
        }
        let price = match terms {
            TERMS_FREE_PUBLIC | TERMS_PER_USE => U256::ZERO,
            _ => self.mfg_price.get(cert),
        };
        let paid = msg::value();
        if paid < price {
            return Err(CompositionError::Underpaid(Underpaid {}));
        }
        let owner = self.owner.get(cert);
        self.credit(owner, price);
        if paid > price {
            self.credit(msg::sender(), paid - price);
        }
        let remaining = match terms {
            TERMS_SINGLE_SHUTTLE_DIE => U256::from(1),
            TERMS_QUANTITY_LIMITED => self.mfg_quantity.get(cert),
            TERMS_PER_USE => U256::ZERO,
            _ => U256::MAX, // unlimited, free public
        };
        let lic = self.lic_count.get() + U256::from(1);
        self.lic_count.set(lic);
        self.lic_cert.setter(lic).set(cert);
        self.lic_licensee.setter(lic).set(msg::sender());
        self.lic_terms.setter(lic).set(U8::from(terms));
        self.lic_remaining.setter(lic).set(remaining);
        self.lic_uses.setter(lic).set(U256::ZERO);
        self.lic_active.setter(lic).set(true);
        // Freeze the deal as sold: unit price, foundry, and package commitment.
        self.lic_unit_price.setter(lic).set(self.mfg_price.get(cert));
        self.lic_foundry.setter(lic).set(self.foundry.get(cert));
        self.lic_package.setter(lic).set(self.mfg_package.get(cert));
        evm::log(LicenseIssued { lic, cert, licensee: msg::sender(), terms, paid: price });
        Ok(lic)
    }

    /// The authorized foundry consumes a license as it manufactures: burns the
    /// single die, decrements the quantity, or charges per unit. Only the
    /// foundry the designer named may call this, and only after it has recorded
    /// the disclosure it received (`record_disclosure`), except for free public
    /// releases.
    #[payable]
    pub fn consume(&mut self, lic: U256, units: U256) -> Result<U256, CompositionError> {
        if lic == U256::ZERO || lic > self.lic_count.get() {
            return Err(CompositionError::UnknownLicense(UnknownLicense {}));
        }
        if !self.lic_active.get(lic) {
            return Err(CompositionError::LicenseInactive(LicenseInactive {}));
        }
        let cert = self.lic_cert.get(lic);
        // The foundry authorized for THIS license, as sold; a later change to the
        // offer cannot redirect or strand an existing license.
        if msg::sender() != self.lic_foundry.get(lic) {
            return Err(CompositionError::NotFoundry(NotFoundry {}));
        }
        if units == U256::ZERO {
            return Err(CompositionError::InsufficientUnits(InsufficientUnits {}));
        }
        let terms = self.lic_terms.get(lic).to::<u8>();
        // No unit is manufactured from a design the foundry has not provably
        // received: disclosure must be recorded first. Free public releases are
        // exempt, there is no confidential handoff to record.
        if terms != TERMS_FREE_PUBLIC && self.lic_disclosure.get(lic) == FixedBytes::<32>::ZERO {
            return Err(CompositionError::NoDisclosure(NoDisclosure {}));
        }
        let mut remaining = self.lic_remaining.get(lic);
        let mut paid_now = U256::ZERO;
        match terms {
            TERMS_SINGLE_SHUTTLE_DIE => {
                if remaining < U256::from(1) || units != U256::from(1) {
                    return Err(CompositionError::InsufficientUnits(InsufficientUnits {}));
                }
                remaining = U256::ZERO;
                self.lic_active.setter(lic).set(false);
            }
            TERMS_QUANTITY_LIMITED => {
                if remaining < units {
                    return Err(CompositionError::InsufficientUnits(InsufficientUnits {}));
                }
                remaining -= units;
                if remaining == U256::ZERO {
                    self.lic_active.setter(lic).set(false);
                }
            }
            TERMS_PER_USE => {
                // The per-unit price as sold, never the designer's current price.
                let cost = self
                    .lic_unit_price
                    .get(lic)
                    .checked_mul(units)
                    .ok_or(CompositionError::Overflow(Overflow {}))?;
                let paid = msg::value();
                if paid < cost {
                    return Err(CompositionError::Underpaid(Underpaid {}));
                }
                let owner = self.owner.get(cert);
                self.credit(owner, cost);
                if paid > cost {
                    self.credit(msg::sender(), paid - cost);
                }
                paid_now = cost;
            }
            _ => { /* unlimited / free public: nothing to decrement */ }
        }
        self.lic_remaining.setter(lic).set(remaining);
        let uses = self.lic_uses.get(lic) + units;
        self.lic_uses.setter(lic).set(uses);
        evm::log(LicenseConsumed { lic, units, remaining, paid: paid_now });
        Ok(remaining)
    }

    /// The foundry records the hash of the design package it received for a
    /// license. It must equal the package the designer committed to in
    /// `set_manufacturing_terms`, so the chain proves the foundry received the
    /// certified design, without the design ever going on-chain.
    pub fn record_disclosure(&mut self, lic: U256, package_hash: FixedBytes<32>) -> Result<(), CompositionError> {
        if lic == U256::ZERO || lic > self.lic_count.get() {
            return Err(CompositionError::UnknownLicense(UnknownLicense {}));
        }
        // Both the authorized foundry and the package commitment are the ones
        // frozen into this license at purchase.
        if msg::sender() != self.lic_foundry.get(lic) {
            return Err(CompositionError::NotFoundry(NotFoundry {}));
        }
        let committed = self.lic_package.get(lic);
        if committed == FixedBytes::<32>::ZERO || package_hash != committed {
            return Err(CompositionError::PackageMismatch(PackageMismatch {}));
        }
        self.lic_disclosure.setter(lic).set(package_hash);
        evm::log(DisclosureRecorded { lic, package_hash });
        Ok(())
    }

    /// Upgrade a fork into a beat. A fork only names a baseline and pays it; a
    /// beat additionally references a recorded improvement measurement (a
    /// `q2-verifier` champion or a `q2-anchor` record id), so "best available"
    /// is a measured public signal, not a declaration. Owner-only; the
    /// certificate must already have a baseline.
    pub fn claim_beat(&mut self, id: U256, improvement_ref: FixedBytes<32>) -> Result<(), CompositionError> {
        self.check_cert(id)?;
        if self.owner.get(id) != msg::sender() {
            return Err(CompositionError::NotOwner(NotOwner {}));
        }
        let baseline = self.baseline_of.get(id);
        if baseline == U256::ZERO {
            return Err(CompositionError::NoBaseline(NoBaseline {}));
        }
        if improvement_ref == FixedBytes::<32>::ZERO {
            return Err(CompositionError::ImprovementRequired(ImprovementRequired {}));
        }
        self.beat_ref.setter(id).set(improvement_ref);
        evm::log(BeatClaimed { cert: id, baseline, improvement_ref });
        Ok(())
    }

    // ── payouts ─────────────────────────────────────────────────────────────

    /// Withdraw everything credited to you. Balance is zeroed before the
    /// transfer, so there is no reentrancy on the payout.
    pub fn withdraw(&mut self) -> Result<U256, CompositionError> {
        let who = msg::sender();
        let amount = self.owed.get(who);
        if amount == U256::ZERO {
            return Err(CompositionError::NothingOwed(NothingOwed {}));
        }
        self.owed.setter(who).set(U256::ZERO);
        transfer_eth(who, amount).map_err(|_| CompositionError::TransferFailed(TransferFailed {}))?;
        evm::log(Withdrawn { owner: who, amount });
        Ok(amount)
    }

    // ── reads ───────────────────────────────────────────────────────────────

    pub fn count(&self) -> U256 {
        self.cert_count.get()
    }

    /// Core certificate: proof commitment, interface, kind, owner, composed?, when.
    pub fn certificate(
        &self,
        id: U256,
    ) -> Result<(FixedBytes<32>, FixedBytes<32>, u16, Address, bool, u64), CompositionError> {
        self.check_cert(id)?;
        Ok((
            self.artifact_hash.get(id),
            self.interface_hash.get(id),
            self.proof_kind.get(id).to::<u16>(),
            self.owner.get(id),
            self.is_composition.get(id),
            self.registered_at.get(id).to::<u64>(),
        ))
    }

    /// Reference-license economics: commons?, per-reference price, recovery
    /// target, recovered so far, and what the next reference would owe.
    pub fn reference_terms(&self, id: U256) -> Result<(bool, U256, U256, U256, U256), CompositionError> {
        self.check_cert(id)?;
        Ok((
            self.commons.get(id),
            self.ref_price.get(id),
            self.recovery_target.get(id),
            self.recovered.get(id),
            self.royalty_due(id),
        ))
    }

    /// The manufacturing offer on a certificate: terms, price, quantity,
    /// foundry, and the committed package hash the foundry must receive.
    pub fn manufacturing_terms(&self, id: U256) -> Result<(u8, U256, U256, Address, FixedBytes<32>), CompositionError> {
        self.check_cert(id)?;
        Ok((
            self.mfg_terms.get(id).to::<u8>(),
            self.mfg_price.get(id),
            self.mfg_quantity.get(id),
            self.foundry.get(id),
            self.mfg_package.get(id),
        ))
    }

    /// The improvement reference behind a beat claim, or 0 for a plain fork or
    /// a first listing. Non-zero means "best available" is backed by a
    /// recorded measurement at the referenced contract.
    pub fn beat_ref(&self, id: U256) -> FixedBytes<32> {
        self.beat_ref.get(id)
    }

    /// A manufacturing license: certificate, licensee, terms, remaining, uses, active, disclosure hash.
    pub fn license(
        &self,
        lic: U256,
    ) -> Result<(U256, Address, u8, U256, U256, bool, FixedBytes<32>), CompositionError> {
        if lic == U256::ZERO || lic > self.lic_count.get() {
            return Err(CompositionError::UnknownLicense(UnknownLicense {}));
        }
        Ok((
            self.lic_cert.get(lic),
            self.lic_licensee.get(lic),
            self.lic_terms.get(lic).to::<u8>(),
            self.lic_remaining.get(lic),
            self.lic_uses.get(lic),
            self.lic_active.get(lic),
            self.lic_disclosure.get(lic),
        ))
    }

    pub fn license_count(&self) -> U256 {
        self.lic_count.get()
    }

    pub fn child_count(&self, id: U256) -> U256 {
        self.child_count.get(id)
    }

    pub fn child(&self, id: U256, index: U256) -> U256 {
        self.child_at.getter(id).get(index)
    }

    /// The incumbent a certificate settled against under beat-or-fork, or 0 if
    /// it was the first to claim its interface.
    pub fn baseline_of(&self, id: U256) -> U256 {
        self.baseline_of.get(id)
    }

    /// The first certificate to claim an interface, or 0 if none has.
    pub fn interface_first(&self, interface_hash: FixedBytes<32>) -> U256 {
        self.interface_first.get(interface_hash)
    }

    pub fn owed_to(&self, who: Address) -> U256 {
        self.owed.get(who)
    }
}
