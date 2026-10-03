// Verify every witness submission: schema + wallet signature over the committed
// fields (ecrecover, EIP-191). No design content is read — only the posted hashes,
// measured cost, and signature. Exits non-zero on any failure (the red-X protocol).
//
//   npm i ethers@6
//   node tools/verify-submission.mjs [submissions-dir]
import { readFileSync, readdirSync } from "node:fs";
import { ethers } from "ethers";
import { canonicalMessage, validateRecord } from "./witness-lib.mjs";

const dir = process.argv[2] ?? "submissions";
const files = readdirSync(dir).filter((f) => f.endsWith(".json"));

if (files.length === 0) { console.log("no submissions to verify"); process.exit(0); }

let failed = 0;
for (const f of files) {
  let rec;
  try { rec = JSON.parse(readFileSync(`${dir}/${f}`, "utf8")); }
  catch (e) { console.error(`FAIL ${f}: not valid JSON (${e.message})`); failed++; continue; }

  const errs = validateRecord(rec);
  if (errs.length) { console.error(`FAIL ${f}: ${errs.join("; ")}`); failed++; continue; }

  let signer;
  try { signer = ethers.verifyMessage(canonicalMessage(rec), rec.wallet_sig); }
  catch (e) { console.error(`FAIL ${f}: signature does not recover (${e.message})`); failed++; continue; }

  if (signer.toLowerCase() !== rec.wallet.toLowerCase()) {
    console.error(`FAIL ${f}: signature recovers to ${signer}, not the claimed wallet ${rec.wallet} — the wallet did not sign these exact fields (the "ask questions" case)`);
    failed++; continue;
  }

  console.log(`ok   ${f}: witnessed by ${rec.wallet} — ${rec.interface} (${rec.tier}, ${rec.verdict})`);
}

if (failed) { console.error(`\n${failed} of ${files.length} submission(s) FAILED verification`); process.exit(1); }
console.log(`\nall ${files.length} submission(s) verified`);
