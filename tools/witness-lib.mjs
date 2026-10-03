// Shared logic for the interim off-chain witness: the canonical message a wallet
// signs, the physical floors, and record validation. Used by attest.mjs (to build
// the message to sign), verify-submission.mjs (to check it), and leaderboard.mjs.
//
// Interim rail: while Arbitrum Stylus activation is paused, a wallet signs the
// HASH of a design + result (never the design itself), and GitHub Actions
// witnesses the commitment. Same committed shape as the on-chain record(), so the
// chain supersedes it when activation returns.
import { createHash } from "node:crypto";

export const SCHEMA = "q2.witness.v1";
export const K_B = 1.380649e-23;   // Boltzmann constant, J/K
export const LN2 = Math.LN2;

/** Landauer limit: minimum energy to irreversibly handle nBits, at tempK. */
export function landauerFloorJ(nBits, tempK = 300) {
  return nBits * K_B * tempK * LN2;
}

export function sha256Hex(buf) {
  return "0x" + createHash("sha256").update(buf).digest("hex");
}

/** The exact string the wallet signs (EIP-191 personal_sign). Binds every field,
 *  so altering a measured number invalidates the signature. Must be byte-identical
 *  on the signing and verifying sides. */
export function canonicalMessage(rec) {
  const m = rec.measure ?? {};
  return [
    "Q2 witness v1",
    `schema=${rec.schema}`,
    `interface=${rec.interface}`,
    `tier=${rec.tier}`,
    `fingerprint=${rec.fingerprint}`,
    `result_hash=${rec.result_hash}`,
    `verdict=${rec.verdict}`,
    `area_um2=${m.area_um2}`,
    `delay_ns=${m.delay_ns}`,
    `energy_j=${m.energy_j}`,
    `n_bits=${m.n_bits}`,
    `submitted_at=${rec.submitted_at}`,
  ].join("\n");
}

const HEX64 = /^0x[0-9a-fA-F]{64}$/;
const ADDR  = /^0x[0-9a-fA-F]{40}$/;
const SIG   = /^0x[0-9a-fA-F]{130}$/;
const MEAS  = ["area_um2", "delay_ns", "energy_j", "n_bits"];

/** Structural validation (not signature). Returns a list of problems; empty = ok. */
export function validateRecord(rec) {
  const e = [];
  if (rec.schema !== SCHEMA) e.push(`schema must be ${SCHEMA}`);
  if (!rec.interface) e.push("missing interface");
  if (!rec.tier) e.push("missing tier");
  if (!HEX64.test(rec.fingerprint ?? "")) e.push("fingerprint must be 0x + 64 hex (sha256)");
  if (!HEX64.test(rec.result_hash ?? "")) e.push("result_hash must be 0x + 64 hex (sha256)");
  if (!["pass", "fail"].includes(rec.verdict)) e.push("verdict must be pass|fail");
  if (!ADDR.test(rec.wallet ?? "")) e.push("wallet must be 0x + 40 hex");
  if (!SIG.test(rec.wallet_sig ?? "")) e.push("wallet_sig must be 0x + 130 hex");
  if (!rec.submitted_at) e.push("missing submitted_at");
  const m = rec.measure ?? {};
  for (const k of MEAS) if (typeof m[k] !== "number" || !(m[k] >= 0)) e.push(`measure.${k} must be a non-negative number`);
  if (!(m.n_bits > 0)) e.push("measure.n_bits must be > 0");
  return e;
}
