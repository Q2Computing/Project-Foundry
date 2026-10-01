//! Q2Verifier, on-chain conformance verification + a ranked leaderboard for a
//! well-specified VLSI block, on Arbitrum Stylus.
//!
//! This is the "why Stylus" contract: the chain itself RE-RUNS the verification.
//! A submitter sends a gate netlist; the contract evaluates it over EVERY input
//! assignment (an exhaustive, complete equivalence proof at this size) against a
//! golden spec computed on-chain, and only a design that conforms reaches the
//! board. Exhaustive checking of a small block is real compute that is cheap in
//! Rust/WASM and prohibitive in Solidity, which is exactly the edge Stylus exists
//! for. Nobody has to trust the verdict: re-run it, or re-derive it here.
//!
//! Spec (v1): sky130 / add4, a 4-bit binary adder.
//!   Inputs (9), canonical wire order: a0 a1 a2 a3 b0 b1 b2 b3 cin -> wires 0..8
//!   Outputs (5), order:                sum0 sum1 sum2 sum3 cout
//! Gate ops: 0 AND, 1 OR, 2 XOR, 3 NOT(a), 4 NAND, 5 NOR, 6 XNOR, 7 BUF(a).
//!
//! Netlist wire encoding: inputs are wires 0..NUM_INPUTS-1; gate i (0-based)
//! drives wire NUM_INPUTS+i; a gate may only reference earlier wires (acyclic).
#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;
use alloc::vec::Vec;

use alloy_sol_types::sol;
use stylus_sdk::{
    alloy_primitives::{Address, FixedBytes, U32, U64, U256, keccak256},
    prelude::*,
};

const NUM_INPUTS: usize = 9;
const NUM_OUTPUTS: usize = 5;
const MAX_GATES: usize = 512;

sol! {
    event Submitted(
        uint256 indexed id,
        address indexed submitter,
        bytes32 netlist_hash,
        uint32 gate_count,
        uint64 timestamp,
        bool champion
    );
    error BadNetlist(uint8 reason);
    error DidNotConform();
    error RecordNotFound();
}

#[derive(SolidityError)]
pub enum VerifierError {
    BadNetlist(BadNetlist),
    DidNotConform(DidNotConform),
    RecordNotFound(RecordNotFound),
}

sol_storage! {
    #[entrypoint]
    pub struct Q2Verifier {
        uint256 count;
        mapping(uint256 => address) submitter;
        mapping(uint256 => bytes32) netlist_hash;
        mapping(uint256 => uint32) gate_count;
        mapping(uint256 => bool) passed;
        mapping(uint256 => uint64) recorded_at;
        bool has_champion;
        uint32 best_gates;
        uint256 best_id;
    }
}

struct Gate {
    op: u8,
    a: usize,
    b: usize,
}

// The golden spec: 4-bit binary addition. Given input assignment `m` (bit j is
// input wire j), returns the expected [sum0, sum1, sum2, sum3, cout].
fn golden(m: usize) -> [bool; NUM_OUTPUTS] {
    let a = (m & 0xF) as u32;
    let b = ((m >> 4) & 0xF) as u32;
    let cin = ((m >> 8) & 0x1) as u32;
    let s = a + b + cin;
    [
        (s & 1) != 0,
        ((s >> 1) & 1) != 0,
        ((s >> 2) & 1) != 0,
        ((s >> 3) & 1) != 0,
        ((s >> 4) & 1) != 0,
    ]
}

// Decode the binary netlist. Err(reason): 1 wrong num_inputs, 2 wrong
// num_outputs, 3 bad op, 4 forward/cyclic reference, 5 too large, 6 truncated,
// 7 output index out of range.
fn decode(data: &[u8]) -> Result<(Vec<Gate>, Vec<usize>), u8> {
    if data.len() < 3 {
        return Err(6);
    }
    let num_inputs = data[0] as usize;
    if num_inputs != NUM_INPUTS {
        return Err(1);
    }
    let num_gates = ((data[1] as usize) << 8) | (data[2] as usize);
    if num_gates > MAX_GATES {
        return Err(5);
    }
    let mut p = 3usize;
    let mut gates: Vec<Gate> = Vec::new();
    let mut i = 0usize;
    while i < num_gates {
        if p + 5 > data.len() {
            return Err(6);
        }
        let op = data[p];
        let a = ((data[p + 1] as usize) << 8) | (data[p + 2] as usize);
        let b = ((data[p + 3] as usize) << 8) | (data[p + 4] as usize);
        p += 5;
        if op > 7 {
            return Err(3);
        }
        let out_index = num_inputs + i;
        if a >= out_index {
            return Err(4);
        }
        if op != 3 && op != 7 && b >= out_index {
            return Err(4);
        }
        gates.push(Gate { op, a, b });
        i += 1;
    }
    let total_wires = num_inputs + num_gates;
    if p >= data.len() {
        return Err(6);
    }
    let num_outputs = data[p] as usize;
    p += 1;
    if num_outputs != NUM_OUTPUTS {
        return Err(2);
    }
    let mut outs: Vec<usize> = Vec::new();
    let mut k = 0usize;
    while k < num_outputs {
        if p + 2 > data.len() {
            return Err(6);
        }
        let w = ((data[p] as usize) << 8) | (data[p + 1] as usize);
        p += 2;
        if w >= total_wires {
            return Err(7);
        }
        outs.push(w);
        k += 1;
    }
    Ok((gates, outs))
}

// Exhaustive conformance to golden(). Returns (passed, counterexample_m).
fn conforms(gates: &[Gate], outs: &[usize]) -> (bool, usize) {
    let total = NUM_INPUTS + gates.len();
    let mut vals: Vec<bool> = Vec::new();
    vals.resize(total, false);
    let combos = 1usize << NUM_INPUTS;
    let mut m = 0usize;
    while m < combos {
        let mut j = 0usize;
        while j < NUM_INPUTS {
            vals[j] = ((m >> j) & 1) != 0;
            j += 1;
        }
        let mut i = 0usize;
        while i < gates.len() {
            let g = &gates[i];
            let a = vals[g.a];
            let b = vals[g.b];
            let o = match g.op {
                0 => a && b,
                1 => a || b,
                2 => a ^ b,
                3 => !a,
                4 => !(a && b),
                5 => !(a || b),
                6 => !(a ^ b),
                7 => a,
                _ => false,
            };
            vals[NUM_INPUTS + i] = o;
            i += 1;
        }
        let exp = golden(m);
        let mut k = 0usize;
        while k < NUM_OUTPUTS {
            if vals[outs[k]] != exp[k] {
                return (false, m);
            }
            k += 1;
        }
        m += 1;
    }
    (true, 0)
}

#[public]
impl Q2Verifier {
    /// Read-only conformance check. Returns (passed, gate_count, counterexample),
    /// where counterexample is the input assignment (bit j = input wire j) that
    /// first disagreed with the spec, or 0 when it passed. No storage: this is the
    /// free "check, and get the counterexample" path before you commit a submission.
    pub fn check(&self, netlist: Vec<u8>) -> Result<(bool, u32, u64), VerifierError> {
        let (gates, outs) =
            decode(&netlist).map_err(|r| VerifierError::BadNetlist(BadNetlist { reason: r }))?;
        let (ok, cex) = conforms(&gates, &outs);
        Ok((ok, gates.len() as u32, cex as u64))
    }

    /// Submit a design. Reverts if it does not conform, so only conformant designs
    /// reach the board. Stores the entry, updates the champion when strictly
    /// cheaper (fewer gates), and returns (gate_count, id).
    pub fn submit(&mut self, netlist: Vec<u8>) -> Result<(u32, U256), VerifierError> {
        let sender = self.vm().msg_sender();
        let now = self.vm().block_timestamp();
        let (gates, outs) =
            decode(&netlist).map_err(|r| VerifierError::BadNetlist(BadNetlist { reason: r }))?;
        let (ok, _cex) = conforms(&gates, &outs);
        if !ok {
            return Err(VerifierError::DidNotConform(DidNotConform {}));
        }
        let gcount = gates.len() as u32;
        let id = self.count.get() + U256::from(1);
        self.count.set(id);
        let h = keccak256(&netlist);
        self.submitter.setter(id).set(sender);
        self.netlist_hash.setter(id).set(h);
        self.gate_count.setter(id).set(U32::from(gcount));
        self.passed.setter(id).set(true);
        let ts = now;
        self.recorded_at.setter(id).set(U64::from(ts));
        let champion = !self.has_champion.get() || gcount < self.best_gates.get().to::<u32>();
        if champion {
            self.has_champion.set(true);
            self.best_gates.set(U32::from(gcount));
            self.best_id.set(id);
        }
        self.vm().log(Submitted {
            id,
            submitter: sender,
            netlist_hash: h,
            gate_count: gcount,
            timestamp: ts,
            champion,
        });
        Ok((gcount, id))
    }

    /// Total number of conformant entries on the board.
    pub fn count(&self) -> U256 {
        self.count.get()
    }

    /// Current champion: (exists, id, submitter, gate_count).
    pub fn champion(&self) -> (bool, U256, Address, u32) {
        if !self.has_champion.get() {
            return (false, U256::ZERO, Address::ZERO, 0);
        }
        let id = self.best_id.get();
        (
            true,
            id,
            self.submitter.get(id),
            self.best_gates.get().to::<u32>(),
        )
    }

    /// A leaderboard entry: (submitter, netlist_hash, gate_count, passed, timestamp).
    pub fn get(
        &self,
        id: U256,
    ) -> Result<(Address, FixedBytes<32>, u32, bool, u64), VerifierError> {
        if id == U256::ZERO || id > self.count.get() {
            return Err(VerifierError::RecordNotFound(RecordNotFound {}));
        }
        Ok((
            self.submitter.get(id),
            self.netlist_hash.get(id),
            self.gate_count.get(id).to::<u32>(),
            self.passed.get(id),
            self.recorded_at.get(id).to::<u64>(),
        ))
    }

    /// Spec identifier: 1 = sky130 add4 (4-bit binary adder).
    pub fn spec_id(&self) -> u16 {
        1
    }
}
