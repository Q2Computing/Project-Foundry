//! Q2Anchor, a generic content-addressed provenance anchor.
//!
//! PUBLIC, disclosure-safe. This is the Arbitrum Stylus buildathon deliverable.
//!
//! What it does: it accepts a `hash` commitment of some off-chain artifact plus
//! an opaque `label` (a coarse outcome code) and an opaque `context` tag, stores
//! them immutably, emits a `Recorded` event, and exposes `get` / `verify` reads.
//! That is the whole contract. It is a black box about *how* the label was
//! produced or whether it is final, the contract never sees the work product,
//! the method, or any verdict logic. The work stays off-chain; only a proof of
//! it is anchored here.
//!
//! Anchoring a hash on-chain for provenance / timestamping is decades-old prior
//! art (Haber–Stornetta 1991; Merkle trees; Certificate Transparency; countless
//! "notarize a hash" contracts). Nothing in this interface encodes any specific
//! mechanism for producing or finalizing a label, deliberately. It is the
//! generic surface, and only the generic surface.
//!
//! Records are non-invertible: a `<hash, label, context>` row lets anyone verify
//! that a given artifact was committed with a given outcome, without revealing
//! the artifact, the outcome's meaning, or anything about how it was reached.
#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use alloy_sol_types::sol;
use stylus_sdk::{
    alloy_primitives::{Address, FixedBytes, U16, U64, U256},
    prelude::*,
};

// The observable provenance stream: a commitment + two opaque coarse codes.
sol! {
    event Recorded(
        uint256 indexed id,
        address indexed submitter,
        bytes32 artifact_hash,
        uint16 label,
        uint16 context,
        uint64 timestamp
    );

    error RecordNotFound();
}

#[derive(SolidityError)]
pub enum AnchorError {
    RecordNotFound(RecordNotFound),
}

sol_storage! {
    #[entrypoint]
    pub struct Q2Anchor {
        uint256 count;
        mapping(uint256 => bytes32) artifact_hash;
        mapping(uint256 => uint16) label;
        mapping(uint256 => uint16) context;
        mapping(uint256 => address) submitter;
        mapping(uint256 => uint64) recorded_at;
    }
}

#[public]
impl Q2Anchor {
    /// Anchor a commitment. Permissionless and append-only: anyone may record a
    /// `<hash, label, context>` fact. Returns the new record id (1-based).
    pub fn record(
        &mut self,
        artifact_hash: FixedBytes<32>,
        label: u16,
        context: u16,
    ) -> Result<U256, AnchorError> {
        let sender = self.vm().msg_sender();
        let now = self.vm().block_timestamp();
        let id = self.count.get() + U256::from(1);
        self.count.set(id);
        self.artifact_hash.setter(id).set(artifact_hash);
        self.label.setter(id).set(U16::from(label));
        self.context.setter(id).set(U16::from(context));
        self.submitter.setter(id).set(sender);
        let ts = now;
        self.recorded_at.setter(id).set(U64::from(ts));
        self.vm().log(Recorded {
            id,
            submitter: sender,
            artifact_hash,
            label,
            context,
            timestamp: ts,
        });
        Ok(id)
    }

    // ── reads ──────────────────────────────────────────────────────────────────

    /// Total number of anchored records.
    pub fn count(&self) -> U256 {
        self.count.get()
    }

    /// The full record: the commitment, the two opaque codes, who submitted it,
    /// and when.
    pub fn get(&self, id: U256) -> Result<(FixedBytes<32>, u16, u16, Address, u64), AnchorError> {
        if id == U256::ZERO || id > self.count.get() {
            return Err(AnchorError::RecordNotFound(RecordNotFound {}));
        }
        Ok((
            self.artifact_hash.get(id),
            self.label.get(id).to::<u16>(),
            self.context.get(id).to::<u16>(),
            self.submitter.get(id),
            self.recorded_at.get(id).to::<u64>(),
        ))
    }

    /// Convenience check: does record `id` commit to `artifact_hash`? Returns
    /// false for an out-of-range id rather than reverting.
    pub fn verify(&self, id: U256, artifact_hash: FixedBytes<32>) -> bool {
        if id == U256::ZERO || id > self.count.get() {
            return false;
        }
        self.artifact_hash.get(id) == artifact_hash
    }
}
