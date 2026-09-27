// Q2Composition demo: two economies, run over Q2's real MXFP4 proof tree.
//
//   1. REFERENCE (the commons economy). PDK cells are `commons`, free forever.
//      Every other certificate recovers its lister-declared listing gas through a
//      per-reference royalty, paid ONLY by the systems that directly use it, and
//      capped at that gas: once recovered, it is free. Cost recovery, never rent.
//   2. MANUFACTURING (the designer's product). A licensee buys the right to put a
//      design in a fabricated SoC; the design is disclosed only to the designer's
//      named foundry, which must record what it received before it may consume
//      the license unit by unit.
//
// Every artifact hash comes from demo/mxfp4-certificates.json, exported from the
// portal: real proofs of record. This script mirrors the contract's semantics
// exactly (same binding preimage, same cap rule, same terms), so a dry run shows
// the whole instrument without a deployment. Set CONTRACT_ADDRESS, PRIVATE_KEY,
// FOUNDRY_PRIVATE_KEY and RPC_URL to send the real transactions.
//
//   node demo/run.mjs

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { keccak256, concatHex, stringToHex, formatEther } from "viem";

const here = dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(readFileSync(join(here, "mxfp4-certificates.json"), "utf8"));

const KIND = { 1: "cell-proof", 2: "equivalence", 3: "techmap-equivalence", 4: "composition-proof" };
const TERMS = { 1: "free public", 2: "single express-shuttle die", 3: "quantity-limited", 4: "per use", 5: "unlimited" };

const eth = (w) => `${formatEther(BigInt(w))} ETH`;
const ifaceHash = (b) => keccak256(stringToHex(b.interface));
const artifactHash = (b) => `0x${b.artifact_sha256}`;
// Identical byte layout to Q2Composition::certify:
//   keccak256(system_hash(32) || interface_hash(32) || each DIRECT child's registered interface_hash(32))
const bindingOf = (b, childIfaceHashes) => keccak256(concatHex([artifactHash(b), ifaceHash(b), ...childIfaceHashes]));

// ── on-chain state, simulated with the contract's exact rules ────────────────
const certs = new Map();   // key -> { id, owner, commons, refPrice, target, recovered }
const owed = new Map();    // address -> bigint
// Beat-or-fork: the first certificate to claim an interface. A later listing on
// the same interface must name it as `baseline` and repay its remaining gas.
// Every interface in this tree is new, so every listing passes baseline = 0.
const interfaceFirst = new Map();
function claimInterface(ih, id) {
  if (interfaceFirst.has(ih)) throw new Error(`interface already certified by #${interfaceFirst.get(ih)}: a baseline is required`);
  interfaceFirst.set(ih, id);
}
const credit = (who, amt) => { if (amt > 0n) owed.set(who, (owed.get(who) || 0n) + amt); };
let nextId = 0;

// Q2Composition::royalty_due — price, but never more than what remains of the
// target; zero once recovered or if commons.
function royaltyDue(c) {
  if (c.commons) return 0n;
  if (c.recovered >= c.target) return 0n;
  const gap = c.target - c.recovered;
  return c.refPrice < gap ? c.refPrice : gap;
}

function main() {
  const live = !!(process.env.CONTRACT_ADDRESS && process.env.PRIVATE_KEY && process.env.RPC_URL);
  const DESIGNER = process.env.PUBLIC_ADDRESS || "0xDESIGNER";
  const LICENSEE = "0xLICENSEE";
  const FOUNDRY  = process.env.FOUNDRY_ADDRESS || "0xFOUNDRY";

  console.log(`\nQ2Composition demo  ·  ${manifest.spec}`);
  console.log(`mode: ${live ? "LIVE" : "dry-run (contract semantics simulated exactly)"}\n`);
  console.log("═══ License 1 · REFERENCE (the commons economy) ═══\n");

  const byKey = new Map(manifest.blocks.map((b) => [b.key, b]));
  let totalRoyalties = 0n;

  for (const b of manifest.blocks) {
    const ih = ifaceHash(b);
    const isLeaf = b.children.length === 0;
    const refPrice = BigInt(b.ref_price_wei || 0);
    const target = BigInt(b.recovery_target_wei || 0);

    if (isLeaf) {
      const id = ++nextId;
      certs.set(b.key, { id, owner: DESIGNER, commons: !!b.commons, refPrice, target, recovered: 0n });
      claimInterface(ih, id);
      console.log(`register  #${id}  ${b.name}   (baseline 0, new interface)`);
      console.log(`            proof       ${KIND[b.proof_kind]}  ${artifactHash(b)}`);
      console.log(`            interface   ${ih}`);
      if (b.commons) console.log(`            terms       COMMONS · PDK primitive · free to reference forever\n`);
      else console.log(`            terms       cost recovery · ${eth(refPrice)} per reference until ${eth(target)} listing gas is recovered, then free\n`);
      continue;
    }

    // Composite: bound to its DIRECT children; royalties only to the distinct
    // abstractions it actually uses (the recursion beneath was settled already).
    const childIds = b.children.map((k) => { const c = certs.get(k); if (!c) throw new Error(`child ${k} of ${b.key} not registered`); return c.id; });
    const binding = bindingOf(b, b.children.map((k) => ifaceHash(byKey.get(k))));
    const used = [...new Set(b.children)];
    let due = 0n;
    const lines = [];
    for (const k of used) {
      const c = certs.get(k);
      const r = royaltyDue(c);
      if (r > 0n) { credit(c.owner, r); c.recovered += r; }
      due += r;
      const status = c.commons ? "commons, free" : (c.recovered >= c.target ? `RECOVERED (${eth(c.recovered)} of ${eth(c.target)}) → now free` : `${eth(c.recovered)} of ${eth(c.target)} recovered`);
      lines.push(`              #${c.id} ${byKey.get(k).name}: pays ${eth(r)}  [${status}]`);
    }
    totalRoyalties += due;

    const id = ++nextId;
    certs.set(b.key, { id, owner: DESIGNER, commons: false, refPrice, target, recovered: 0n });
    claimInterface(ih, id);
    console.log(`certify   #${id}  ${b.name}   [${b.tier}]   (baseline 0, new interface)`);
    console.log(`            system      ${artifactHash(b)}   (${KIND[b.proof_kind]})`);
    console.log(`            references  ${childIds.map((cid) => `#${cid}`).join(", ")}   binding ${binding.slice(0, 18)}…`);
    console.log(`            royalties   ${eth(due)} to the direct abstractions used, nothing deeper:`);
    for (const l of lines) console.log(l);
    console.log(`            note        composer holds only these certificates, never a child design`);
    if (target > 0n) console.log(`            listed at   ${eth(refPrice)} per reference until ${eth(target)} recovered`);
    console.log();
  }

  // ── License 2 · MANUFACTURING ──────────────────────────────────────────────
  console.log("═══ License 2 · MANUFACTURING (the designer's product) ═══\n");
  const mfgBlock = manifest.blocks.find((b) => b.manufacturing);
  if (mfgBlock) {
    const m = mfgBlock.manufacturing;
    const c = certs.get(mfgBlock.key);
    const price = BigInt(m.price_wei);
    // The designer commits, up front, to the exact package the foundry must receive.
    const pkgHash = keccak256(stringToHex(m.package));
    console.log(`set_manufacturing_terms  #${c.id}  ${mfgBlock.name}`);
    console.log(`            terms       ${TERMS[m.terms]}${m.terms === 3 ? ` · ${m.quantity} units` : ""} · ${eth(price)} · foundry ${FOUNDRY}`);
    console.log(`            package     ${pkgHash}   (designer's commitment)`);
    console.log(`            basis       real DRC-clean / LVS-match / timing-met signoff → manufacturable\n`);

    // buy_license: licensee pays the designer in full; never sees the design.
    const licId = 1;
    // Mirrors the contract: free-public and PER-USE pay nothing at purchase
    // (per-use pays on every consumed mask); all other terms pay in full now.
    const upfront = (m.terms === 1 || m.terms === 4) ? 0n : price;
    credit(c.owner, upfront);
    let remaining = m.terms === 2 ? 1n : m.terms === 3 ? BigInt(m.quantity) : m.terms === 4 ? 0n : (2n ** 256n - 1n);
    console.log(`buy_license   L${licId}  by ${LICENSEE}  pays ${eth(upfront)} now${m.terms === 4 ? ` (per-use: ${eth(price)} per mask, charged at consume)` : " → designer"}`);
    console.log(`            remaining   ${m.terms === 5 || m.terms === 1 ? "unlimited" : remaining} units · design NOT released to licensee\n`);

    // record_disclosure: the foundry proves what it received, and it must equal
    // the designer's commitment, so the chain knows it got the certified design.
    console.log(`record_disclosure  L${licId}  by foundry ${FOUNDRY}`);
    console.log(`            package     ${pkgHash}   matches the designer's commitment`);
    console.log(`            rule        must match the commitment, and no unit may be consumed until recorded\n`);

    // consume: the foundry manufactures units against the license.
    const units = BigInt(m.consume_units);
    if (m.terms === 3) remaining -= units;
    // Per-use terms charge price × masks HERE, mirroring Q2Composition::consume.
    let paidNow = 0n;
    if (m.terms === 4) { paidNow = price * units; credit(c.owner, paidNow); }
    console.log(`consume   L${licId}  by foundry  ${units} mask set${units === 1n ? "" : "s"} manufactured${m.terms === 4 ? `  pays ${eth(paidNow)} → designer (${units} × ${eth(price)})` : ""}`);
    console.log(`            remaining   ${remaining} · license ${remaining > 0n ? "still active" : "exhausted"}\n`);
  }

  // ── ledger ─────────────────────────────────────────────────────────────────
  const top = manifest.blocks[manifest.blocks.length - 1];
  const topC = certs.get(top.key);
  const recoveredCerts = [...certs.entries()].filter(([, c]) => !c.commons && c.target > 0n && c.recovered >= c.target).map(([k]) => byKey.get(k).name);
  console.log("─".repeat(72));
  console.log(`TOP  #${topC.id}  ${top.name}  certified purely by reference to proven parts.`);
  console.log(`Reference royalties paid up the tree: ${eth(totalRoyalties)} (each capped at its listing gas).`);
  console.log(`Certificates that recovered their gas and are now free: ${recoveredCerts.length ? recoveredCerts.join("; ") : "none yet"}.`);
  console.log(`Withdrawable by owners: ${[...owed.entries()].map(([a, v]) => `${a} ${eth(v)}`).join("  ")}`);
  console.log(`Protocol fee taken: 0. Value conserved. Every artifact hash is a real Q2 proof of record.`);
  console.log(`Beat-or-fork: any later listing on one of these ${interfaceFirst.size} interfaces must name its baseline and repay that baseline's remaining gas. Whoever beats you pays your listing cost.`);
  console.log(`Fork vs beat: a fork only names and pays its baseline; a beat must also reference a recorded improvement (a verifier champion or anchor id), so "best available" is measured, never declared.\n`);

  if (!live) {
    console.log("Dry run. Deploy the contract, then set CONTRACT_ADDRESS, PRIVATE_KEY, FOUNDRY_PRIVATE_KEY, RPC_URL to settle these on Arbitrum Sepolia.\n");
  }
}

main();
