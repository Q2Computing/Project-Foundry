// Build leaderboard.json + site/leaderboard.html from the verified submissions.
//
// Ranking = information-entropy-normalized efficiency against the primary physical
// resources: energy vs the Landauer floor (absolute), and space x time (area*delay)
// vs the per-interface area-time frontier (Thompson). Information (n_bits) is the
// normalizer that puts all three "per useful bit". Index = sqrt(eta_E * eta_AT).
//
//   node tools/leaderboard.mjs
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
import { landauerFloorJ } from "./witness-lib.mjs";

const subs = readdirSync("submissions")
  .filter((f) => f.endsWith(".json"))
  .map((f) => JSON.parse(readFileSync(`submissions/${f}`, "utf8")));

const floorPerBit = landauerFloorJ(1); // kT ln2 at 300 K ~ 2.87e-21 J

const entries = subs.map((r) => {
  const { area_um2, delay_ns, energy_j, n_bits } = r.measure;
  const energy_per_bit = energy_j / n_bits;          // J / bit
  const at_per_bit = (area_um2 * delay_ns) / n_bits; // um^2 * ns / bit
  const eta_E = floorPerBit / energy_per_bit;        // fraction of the Landauer floor
  return {
    interface: r.interface, tier: r.tier, wallet: r.wallet, verdict: r.verdict,
    fingerprint: r.fingerprint, submitted_at: r.submitted_at, status: "witnessed",
    area_um2, delay_ns, energy_j, n_bits, energy_per_bit, at_per_bit, eta_E,
  };
});

// eta_AT is frontier-relative per interface (best area-time per bit on that
// interface scores 1); there is no universal closed-form AT floor.
const bestAT = {};
for (const e of entries) bestAT[e.interface] = Math.min(bestAT[e.interface] ?? Infinity, e.at_per_bit);
for (const e of entries) {
  e.eta_AT = bestAT[e.interface] / e.at_per_bit;
  e.index = Math.sqrt(Math.max(0, e.eta_E) * Math.max(0, e.eta_AT));
}

const passing = entries.filter((e) => e.verdict === "pass");
const ranked = [...passing].sort((a, b) => b.index - a.index);

// Per-interface Pareto frontier: non-dominated on (energy_per_bit, at_per_bit),
// both lower-is-better. "A frontier, not a winner."
const frontiers = {};
const byIface = {};
for (const e of passing) (byIface[e.interface] ??= []).push(e);
for (const [iface, list] of Object.entries(byIface)) {
  frontiers[iface] = list
    .filter((e) => !list.some((o) => o !== e
      && o.energy_per_bit <= e.energy_per_bit && o.at_per_bit <= e.at_per_bit
      && (o.energy_per_bit < e.energy_per_bit || o.at_per_bit < e.at_per_bit)))
    .map((e) => e.fingerprint);
}

const out = {
  schema: "q2.leaderboard.v1",
  generated_at: new Date().toISOString(),
  note: "Interim off-chain witness board during the Arbitrum Stylus activation pause. Entries are wallet-witnessed CLAIMS (status: witnessed): a wallet signed the hash of a design + result, never the design. Verified when the owner reveals and the measurement is re-run against the open PDK; settled on-chain when activation returns.",
  metric: "information-entropy-normalized efficiency. eta_E = (kT ln2) / (energy per bit) vs Landauer; eta_AT = best(area*delay/bit) / (area*delay/bit) vs the per-interface area-time frontier (Thompson); index = sqrt(eta_E * eta_AT).",
  count: ranked.length,
  ranked,
  frontiers,
};

writeFileSync("leaderboard.json", JSON.stringify(out, null, 2) + "\n");

// --- render a self-contained dark page ---
const pct = (x) => (x > 0 && isFinite(x) ? (x * 100).toPrecision(3) + "%" : "-");
const sci = (x) => (isFinite(x) ? x.toExponential(2) : "-");
const rows = ranked.map((e, i) => `      <tr>
        <td class="rank">${i + 1}</td>
        <td><code>${e.interface}</code><div class="tier">${e.tier}</div></td>
        <td class="num">${pct(e.index)}</td>
        <td class="num">${pct(e.eta_E)}</td>
        <td class="num">${pct(e.eta_AT)}</td>
        <td class="num">${sci(e.energy_per_bit)}</td>
        <td class="num">${sci(e.at_per_bit)}</td>
        <td><code class="w">${e.wallet.slice(0, 10)}…</code></td>
        <td><span class="badge">witnessed</span></td>
      </tr>`).join("\n");

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Witness Leaderboard</title>
<style>
  :root{--bg:#0d0d0f;--panel:#141417;--line:#26262b;--ink:#e6e6ea;--dim:#8a8a93;--accent:#5eb0ef;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
  body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,sans-serif}
  .wrap{max-width:1000px;margin:0 auto;padding:28px 16px}
  h1{font-size:22px;margin:0 0 4px} .eyebrow{text-transform:uppercase;letter-spacing:.06em;color:var(--dim);font-size:11px;font-weight:600}
  .note{color:var(--dim);font-size:12px;max-width:72ch;margin:12px 0}
  .metric{color:var(--dim);font-size:11px;font-family:var(--mono);background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:12px 0;white-space:pre-wrap}
  table{width:100%;border-collapse:collapse;margin-top:14px;font-size:13px}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
  .num{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono)}
  .rank{color:var(--accent);font-weight:700}
  code{font-family:var(--mono);font-size:12px} .w{color:var(--dim)} .tier{color:var(--dim);font-size:11px}
  .badge{font-size:10px;border:1px solid var(--line);border-radius:999px;padding:1px 8px;color:var(--dim)}
  .empty{color:var(--dim);padding:20px 0}
</style></head>
<body><div class="wrap">
  <div class="eyebrow">Q2 Computing / Project Foundry / interim rail</div>
  <h1>Witness Leaderboard</h1>
  <p class="note">${out.note}</p>
  <div class="metric">${out.metric}</div>
  ${ranked.length === 0 ? `<p class="empty">No verified submissions yet. Post one: see <code>tools/attest.mjs</code> and open a PR adding your <code>submissions/*.json</code>.</p>` : `<table>
    <thead><tr><th>#</th><th>Interface</th><th>Index</th><th>&eta;<sub>E</sub> (Landauer)</th><th>&eta;<sub>AT</sub> (frontier)</th><th>J / bit</th><th>&micro;m&sup2;&middot;ns / bit</th><th>Wallet</th><th>Status</th></tr></thead>
    <tbody>
${rows}
    </tbody></table>`}
  <p class="note" style="margin-top:20px">Generated ${out.generated_at}. Index = &radic;(&eta;<sub>E</sub> &middot; &eta;<sub>AT</sub>), fraction of the physical ideal per useful bit. Claims are wallet-witnessed; reveal to verify, settle on-chain when activation returns.</p>
</div></body></html>
`;
mkdirSync("site", { recursive: true });
writeFileSync("site/leaderboard.html", html);
console.log(`leaderboard: ${ranked.length} ranked, ${Object.keys(frontiers).length} interface frontier(s)`);
