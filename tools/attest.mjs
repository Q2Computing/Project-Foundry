// Local helper to build a witness submission WITHOUT revealing your design.
// It hashes your files locally, prints the exact message for your wallet to sign,
// and (once you paste the signature) writes submissions/<id>.json. It never asks
// for or handles a private key — you sign in your own wallet (MetaMask, cast, etc.).
//
// Step 1 — compute hashes and print the message to sign:
//   node tools/attest.mjs \
//     --interface sky130_fd_sc_hd__inv_1 --tier standard-cell --verdict pass \
//     --signature-file inv_1.sig.v --testbench-file tb_inv_1.v \
//     --area 1.0 --delay 0.10 --energy 3.8e-16 --nbits 1 --wallet 0xYourAddr
//
// Step 2 — sign that message in your wallet, then re-run adding --sig 0x...:
//   ... (same args) ... --sig 0xSIGNATURE
//
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { canonicalMessage, validateRecord, sha256Hex, SCHEMA } from "./witness-lib.mjs";

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : def;
}
function hashOf(file, explicit) {
  if (explicit) return explicit;
  if (!file) throw new Error(`provide --${file === undefined ? "fingerprint/result-hash or the matching --*-file" : "file"}`);
  return sha256Hex(readFileSync(file));
}

const rec = {
  schema: SCHEMA,
  interface: arg("interface"),
  tier: arg("tier"),
  fingerprint: hashOf(arg("signature-file"), arg("fingerprint")),
  result_hash: hashOf(arg("testbench-file"), arg("result-hash")),
  verdict: arg("verdict", "pass"),
  measure: {
    area_um2: Number(arg("area")),
    delay_ns: Number(arg("delay")),
    energy_j: Number(arg("energy")),
    n_bits: Number(arg("nbits", "1")),
  },
  wallet: (arg("wallet") ?? "").toLowerCase(),
  wallet_sig: arg("sig", ""),
  submitted_at: arg("at", new Date().toISOString()),
};

const msg = canonicalMessage(rec);

if (!rec.wallet_sig) {
  // Step 1: print the message to sign. The design never leaves this machine —
  // only its sha256 fingerprint is in the message.
  console.log("Sign this exact message in your wallet (EIP-191 personal_sign):\n");
  console.log("--------8<--------");
  console.log(msg);
  console.log("-------->8--------\n");
  console.log("Then re-run this command with  --sig 0x<signature>  to write the submission.");
  process.exit(0);
}

// Step 2: validate structure and write the file (signature is checked by the
// witness workflow with ecrecover; verify locally too if ethers is installed).
const errs = validateRecord(rec);
if (errs.length) { console.error("invalid submission:\n - " + errs.join("\n - ")); process.exit(1); }

try {
  const { ethers } = await import("ethers");
  const signer = ethers.verifyMessage(msg, rec.wallet_sig);
  if (signer.toLowerCase() !== rec.wallet) {
    console.error(`signature recovers to ${signer}, not ${rec.wallet} — re-sign the exact message above`);
    process.exit(1);
  }
  console.log(`local check ok: signed by ${signer}`);
} catch { console.log("(ethers not installed; skipping local signature check — the workflow will verify)"); }

mkdirSync("submissions", { recursive: true });
const id = `${rec.interface}-${rec.fingerprint.slice(2, 14)}`;
const path = `submissions/${id}.json`;
writeFileSync(path, JSON.stringify(rec, null, 2) + "\n");
console.log(`wrote ${path} — open a PR adding it to post your witness.`);
