"""The Workbench page of the web app: every step of the guide as a button."""
from __future__ import annotations

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Strategy Workbench</title>
<style>
:root { color-scheme: light; --bg:#f4f3f0; --surface:#fcfcfb; --border:#e3e2dd; --field:#fff; --text:#0b0b0b; --text-2:#52514e; --text-3:#7a7974;
  --accent:#2a78d6; --accent-ink:#fff; --accent-soft:rgba(42,120,214,.10); --good:#006300; --good-soft:rgba(12,163,12,.12); --bad:#a32222; --bad-soft:rgba(208,59,59,.10); --warn:#8a5a00; --warn-soft:rgba(237,161,0,.14); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark; --bg:#121211; --surface:#1a1a19; --border:#2e2e2c; --field:#222221; --text:#f0efec; --text-2:#c3c2b7; --text-3:#8f8e86;
  --accent:#3987e5; --accent-soft:rgba(57,135,229,.16); --good:#4cc94c; --good-soft:rgba(12,163,12,.18); --bad:#f07a7a; --bad-soft:rgba(208,59,59,.16); --warn:#e8b14a; --warn-soft:rgba(237,161,0,.18); } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
main { max-width:1120px; margin:0 auto; padding:28px 16px 64px; }
nav { display:flex; gap:18px; align-items:baseline; margin-bottom:6px; font-size:14px; } nav a { color:var(--accent); text-decoration:none; font-weight:600; } nav a.cur { color:var(--text); }
header h1 { font-size:28px; margin:0 0 4px; letter-spacing:-0.01em; } header p { margin:0; color:var(--text-2); }
.layout { display:grid; grid-template-columns:minmax(0,1.3fr) minmax(0,1fr); gap:18px; margin-top:20px; align-items:start; }
@media (max-width:900px) { .layout { grid-template-columns:1fr; } }
.card { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:20px 22px; }
.card + .card { margin-top:18px; }
.step { display:flex; align-items:center; gap:10px; margin:0 0 6px; }
.step .n { width:26px; height:26px; border-radius:50%; background:var(--accent-soft); color:var(--accent); font-weight:700; font-size:13px; display:grid; place-items:center; flex:none; }
.step h2 { margin:0; font-size:17px; }
.card p { margin:4px 0 12px; color:var(--text-2); font-size:14.5px; }
.row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
.btn { font:inherit; font-weight:650; border:0; border-radius:10px; padding:10px 14px; cursor:pointer; background:var(--accent); color:var(--accent-ink); font-size:14.5px; }
.btn.ghost { background:var(--bg); color:var(--text); border:1px solid var(--border); font-weight:600; }
.btn:disabled { opacity:.55; cursor:not-allowed; }
select, input[type=text], input[type=number] { font:inherit; color:var(--text); background:var(--field); border:1px solid var(--border); border-radius:9px; padding:8px 10px; }
.status { font-size:14px; color:var(--text-2); display:grid; grid-template-columns:auto 1fr; gap:4px 14px; }
.status b { font-weight:600; color:var(--text); }
.pill { display:inline-block; padding:2px 9px; border-radius:999px; font-size:12.5px; font-weight:700; }
.pill.ok { background:var(--good-soft); color:var(--good); } .pill.bad { background:var(--bad-soft); color:var(--bad); } .pill.warn { background:var(--warn-soft); color:var(--warn); } .pill.run { background:var(--accent-soft); color:var(--accent); }
ul.jobs { list-style:none; padding:0; margin:0; } ul.jobs li { border-top:1px solid var(--border); padding:10px 0; }
ul.jobs .t { display:flex; justify-content:space-between; gap:10px; align-items:center; font-weight:600; font-size:15px; }
ul.jobs .meta { color:var(--text-3); font-size:13px; margin:2px 0 6px; }
pre.log { white-space:pre-wrap; font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; background:var(--bg); border-radius:9px; padding:8px 10px; margin:6px 0; max-height:170px; overflow:auto; color:var(--text-2); }
.links a { margin-right:12px; color:var(--accent); font-weight:600; font-size:14px; }
.hint { color:var(--text-3); font-size:13px; }
.empty { color:var(--text-3); font-size:14px; }
.spin { display:inline-block; width:12px; height:12px; border:2px solid var(--accent); border-right-color:transparent; border-radius:50%; animation:spin .8s linear infinite; vertical-align:-1px; margin-right:6px; }
@keyframes spin { to { transform:rotate(360deg); } }
.msg { margin-top:10px; font-size:14px; border-radius:9px; padding:9px 12px; display:none; } .msg.err { display:block; background:var(--bad-soft); color:var(--bad); }
.info { position:relative; width:18px; height:18px; border-radius:50%; border:1.5px solid var(--text-3); color:var(--text-3); font-size:11.5px; font-weight:700; display:grid; place-items:center; cursor:help; flex:none; font-family:Georgia,serif; font-style:italic; }
.info::before { content:"i"; }
.info .tip { display:none; text-align:left; position:absolute; left:50%; top:26px; transform:translateX(-50%); width:300px; background:var(--text); color:var(--bg); font:400 13.5px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; font-style:normal; padding:10px 12px; border-radius:9px; box-shadow:0 6px 20px rgba(0,0,0,.18); z-index:5; }
.info:hover .tip, .info:focus .tip { display:block; }
.howto { margin-top:14px; background:var(--accent-soft); border:1px solid var(--border); border-radius:12px; padding:10px 16px; font-size:14.5px; }
.howto summary { cursor:pointer; font-weight:650; } .howto ol { margin:8px 0 6px; padding-left:22px; } .howto li { margin:3px 0; } .howto p { margin:6px 0 2px; color:var(--text-2); }
.readme { font-size:14px; color:var(--text-2); } .readme table { border-collapse:collapse; width:100%; } .readme th, .readme td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--border); vertical-align:top; } .readme th { color:var(--text); font-weight:600; white-space:nowrap; }
</style>
</head>
<body>
<main>
<nav><a href="/workbench" class="cur">Workbench</a><a href="/">Planner</a></nav>
<header><h1>Strategy Workbench</h1><p>Every step of the guide as a button. Long steps run in the background; their progress shows on the right.</p></header>

<details class="howto" open>
  <summary>How to use</summary>
  <ol>
    <li><b>First time:</b> step 1, <i>Download all price data</i> (1–2 min). Later just <i>Add the latest trading days</i>.</li>
    <li><b>Your own rules:</b> step 2 opens the Planner. Write the rules down first, then test them once; don't tweak until it looks good.</li>
    <li><b>See results:</b> step 3, pick a plan → <i>Report for this plan</i>, or <i>Compare all plans with SPY</i>.</li>
    <li><b>Check it holds up:</b> step 4 <i>Quick</i> stress test on the plan; step 5 only if you want the computer to search for rules.</li>
  </ol>
  <p>Results appear under <b>Jobs</b> on the right: click <i>Open report</i>. Read the <b>test period</b> and the <b>verdict</b> first; all 7 checks must pass before paper trading. Close this tab any time; jobs keep running while the launcher window is open.</p>
</details>

<div class="layout">
<div>
  <div class="card">
    <div class="step"><span class="n">1</span><h2>Price data</h2><span class="info" tabindex="0" aria-label="What this step is for"><span class="tip">The raw material: daily open/high/low/close for every stock that was in the S&amp;P 500 since 2016, plus SPY. Do this once, then only add the latest days. Nothing else works without it.</span></span></div>
    <p>About 14 years of daily prices for every stock that was in the S&amp;P 500 since 2016, plus SPY. First download takes 1–2 minutes. Backtests only buy a stock while it was in the index.</p>
    <div class="status" id="dataStatus"><span>Data</span><b>checking…</b></div>
    <div class="row" style="margin-top:12px">
      <button class="btn" data-job="fetch">Download all price data</button>
      <button class="btn ghost" data-job="update">Add the latest days</button>
      <button class="btn ghost" data-job="membership">Check history coverage</button>
      <button class="btn ghost" data-job="tests">Self-test</button>
    </div>
  </div>

  <div class="card">
    <div class="step"><span class="n">2</span><h2>Build your own plan</h2><span class="info" tabindex="0" aria-label="What this step is for"><span class="tip">Turn a trading idea into exact rules: what to buy, when, when to sell, how many positions. Saved as a plan file you can report and stress-test. Write the rules down before you see any result.</span></span></div>
    <p>Describe the rules in the <a href="/">Planner</a>, save, run. Write the rules down before you look at any result.</p>
    <div class="row"><a class="btn" href="/">Open the Planner</a></div>
  </div>

  <div class="card">
    <div class="step"><span class="n">3</span><h2>Reports</h2><span class="info" tabindex="0" aria-label="What this step is for"><span class="tip">What a plan did in the past: verdict, return per year, worst drop, growth of $10,000 against SPY, year by year. Compare puts all plans on one page.</span></span></div>
    <p>A one-page report for one rule set (verdict first), or all saved rule sets on one page against SPY.</p>
    <div class="row">
      <select id="planSel"></select>
      <button class="btn" data-job="report">Report for this plan</button>
      <button class="btn ghost" data-job="compare">Compare all plans with SPY</button>
    </div>
  </div>

  <div class="card">
    <div class="step"><span class="n">4</span><h2>Stress-test a plan</h2><span class="info" tabindex="0" aria-label="What this step is for"><span class="tip">Should you believe the report? Checks whether the result could be luck, whether small changes to the settings break it, whether it survives double costs, and whether random entries do just as well.</span></span></div>
    <p>Quick = verdict and luck checks (about a minute). Full = plus neighbouring settings, costs, random-entry test (about five minutes). The result is a text report.</p>
    <div class="row">
      <select id="planSel2"></select>
      <label class="hint">Variants tried before: <input type="number" id="trials" value="1" min="1" style="width:70px"></label>
      <button class="btn" data-job="analyze" data-quick="1">Quick</button>
      <button class="btn ghost" data-job="analyze" data-quick="0">Full</button>
    </div>
  </div>

  <div class="card">
    <div class="step"><span class="n">5</span><h2>Search many rule sets</h2><span class="info" tabindex="0" aria-label="What this step is for"><span class="tip">Let the computer try hundreds of rule combinations and keep what holds up in walk-forward tests. Use it for ideas, then treat the best set with suspicion: the more you search, the more luck you find.<br><br><b>Rank by</b> decides what "best" means: <b>Calmar</b> = return per unit of worst drop (smooth equity, the default), <b>Sharpe</b> = return per unit of daily wobble, <b>return</b> = highest growth regardless of drops (picks wild sets).</span></span></div>
    <p>Tries many settings with walk-forward validation (rules picked on 3 years, traded the next). 5–15 minutes. Judge the result by “Stitched OOS” against the SPY lines, not by the best in-sample score; the more you search, the more the best result is luck.</p>
    <div class="row">
      <select id="space"><option value="default">Oversold indicators (default)</option><option value="momentum">Momentum / breakouts</option><option value="indicators">More indicators</option><option value="breadth">Broad pullbacks</option><option value="exits">Exit variants</option></select>
      <select id="niter"><option value="200">200 rule sets</option><option value="400" selected>400 rule sets</option><option value="800">800 rule sets</option></select>
      <select id="metric" title="What counts as best: Calmar = return per unit of worst drop (smooth), Sharpe = return per unit of daily wobble, return = growth regardless of drops"><option value="calmar" selected>rank by Calmar</option><option value="sharpe">rank by Sharpe</option><option value="cagr">rank by return</option></select>
      <button class="btn" data-job="tune">Start search</button>
    </div>
  </div>

  <div class="card">
    <div class="step"><span class="n">6</span><h2>Options: SPY call spreads</h2><span class="info" tabindex="0" aria-label="What this step is for"><span class="tip">Backtests a bull call spread routine on SPY without option quotes: each spread is priced with Black-Scholes using the VIX of the day, the payoff at expiry is exact. Enter the debit you really pay and the model is scaled to it. Tune tries 720 variants (strikes, width, expiry, close rule, stop, cadence, trend filter).</span></span></div>
    <p>Buy a call, sell a higher call, same expiry. Needs SPY and VIX history once (<i>Download SPY + VIX</i>). <i>Save as a plan</i> puts the setup into the plan list, so step 3 reports and compares it like any other plan.</p>
    <div class="row" style="margin-bottom:8px">
      <select id="spStrike"><option value="debit" selected>strikes that cost the debit that day</option><option value="offset">long strike at a fixed distance</option></select>
      <label class="hint" id="spOffsetWrap" style="display:none">long strike <input type="number" id="spOffset" value="1.7" step="0.1" style="width:60px">% from price</label>
      <label class="hint">width $<input type="number" id="spWidth" value="10" step="1" style="width:55px"></label>
      <label class="hint">expiry <input type="number" id="spDte" value="60" step="1" style="width:55px"> days</label>
      <label class="hint">close at <input type="number" id="spTarget" value="99" step="1" style="width:55px">% of width</label>
    </div>
    <div class="row" style="margin-bottom:8px">
      <label class="hint">debit you pay $<input type="number" id="spDebit" value="4.95" step="0.05" style="width:65px"></label>
      <select id="spCadence"><option value="expiry" selected>every third Friday (monthly expiration)</option><option value="monthly">first trading day of the month</option><option value="weekly">new spread weekly</option><option value="next">one at a time</option></select>
      <select id="spTrend"><option value="200" selected>only above 200-day average</option><option value="0">always</option></select>
      <label class="hint">stop at <input type="number" id="spStop" value="0" step="10" style="width:50px">% loss</label>
    </div>
    <div class="row">
      <button class="btn" data-job="spreads">Backtest this setup</button>
      <button class="btn ghost" data-job="spreads_save">Save as a plan</button>
      <input type="text" id="spName" placeholder="plan name" value="SPY call spread 4.95" style="width:170px">
      <button class="btn ghost" data-job="spreads_tune">Tune (5–10 min)</button>
      <button class="btn ghost" data-job="spreads_fetch">Download SPY + VIX</button>
    </div>
  </div>

  <div class="card readme">
    <div class="step"><span class="n">?</span><h2>How to read a result</h2><span class="info" tabindex="0" aria-label="What this step is for"><span class="tip">The honest numbers are the test period and the verdict. Everything else can look good by chance.</span></span></div>
    <table>
      <tr><th>Verdict</th><td>7 checks agreed on before testing. All must pass before paper trading.</td></tr>
      <tr><th>Test period</th><td>2025 to today: the rules never saw this data. These are the honest numbers.</td></tr>
      <tr><th>SPY timing</th><td>Hold SPY only above its 200-day average. If a strategy can't beat this, its stock picking adds nothing.</td></tr>
      <tr><th>Unlikely to be luck</th><td>Below 90% means chance alone produces results like this. Each variant you tried raises the bar.</td></tr>
      <tr><th>Stitched OOS</th><td>In a search: rules re-picked each year and traded the next. Compare with the SPY lines below it.</td></tr>
    </table>
    <p style="margin-top:10px">Settings for all steps: backtest from <input type="text" id="start" value="2016-01-01" style="width:110px"> · test period from <input type="text" id="holdout" value="2025-01-01" style="width:110px"></p>
  </div>
</div>

<div>
  <div class="card">
    <h2 style="font-size:17px;margin:0 0 8px">Jobs</h2>
    <div class="msg" id="msg"></div>
    <ul class="jobs" id="jobs"><li class="empty">Nothing running yet. Start with “Download all price data” if you haven't.</li></ul>
  </div>
  <div class="card">
    <h2 style="font-size:17px;margin:0 0 8px">Recent reports</h2>
    <ul class="jobs" id="reports"></ul>
  </div>
</div>
</div>
</main>
<script>
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function msg(t) { const m = $('msg'); m.className = 'msg' + (t ? ' err' : ''); m.textContent = t || ''; }

async function status() {
  const s = await (await fetch('/api/status')).json();
  const d = $('dataStatus');
  if (!s.has_data) { d.innerHTML = '<span>Data</span><b><span class="pill bad">missing</span> click “Download all price data”</b>'; return; }
  d.innerHTML = `<span>Data</span><b><span class="pill ok">ready</span> ${s.tickers} stocks, ${esc(s.first)} – ${esc(s.last)}</b>` +
    `<span>Index history</span><b>${s.membership ? 'point-in-time members on' : '<span class="pill warn">today\'s members only</span>'}` +
    (s.coverage != null ? `, ${s.coverage}% of member-days have prices` : '') + `</b>`;
  const opt = x => `<option value="${esc(x.file)}">${esc(x.name)}</option>`;
  const fill = (id, list) => { const sel = $(id), cur = sel.value; sel.innerHTML = list.map(opt).join(''); if (cur) sel.value = cur; };
  fill('planSel', s.strategies); fill('planSel2', s.strategies.filter(x => x.type !== 'spreads'));
  const reps = $('reports'); reps.innerHTML = s.reports.length ? '' : '<li class="empty">No reports yet.</li>';
  s.reports.forEach(r => { const li = document.createElement('li'); li.innerHTML = `<a href="/reports/${encodeURIComponent(r.file)}">${esc(r.label)}</a>`; reps.appendChild(li); });
}

function jobOpts(btn) {
  const kind = btn.dataset.job, o = {start: $('start').value, holdout_start: $('holdout').value};
  if (kind === 'report') o.file = $('planSel').value;
  if (kind === 'analyze') { o.file = $('planSel2').value; o.quick = btn.dataset.quick === '1'; o.trials = $('trials').value; }
  if (kind === 'tune') { o.space = $('space').value; o.n_iter = $('niter').value; o.metric = $('metric').value; }
  if (kind === 'spreads' || kind === 'spreads_tune') {
    o.offset = $('spOffset').value; o.width = $('spWidth').value; o.dte = $('spDte').value; o.target = $('spTarget').value;
    o.debit = $('spDebit').value; o.cadence = $('spCadence').value; o.trend_ma = $('spTrend').value; o.stop = $('spStop').value; o.metric = $('metric').value;
    o.strike_mode = $('spStrike').value; o.name = $('spName').value;
  }
  if (kind === 'spreads_save') { o.name = $('spName').value; }
  return {kind, opts: o};
}
$('spStrike').addEventListener('change', () => { $('spOffsetWrap').style.display = $('spStrike').value === 'offset' ? '' : 'none'; });
document.querySelectorAll('[data-job]').forEach(b => b.addEventListener('click', async () => {
  msg('');
  try { const r = await fetch('/api/jobs', {method: 'POST', body: JSON.stringify(jobOpts(b))}); const j = await r.json();
    if (!r.ok) throw new Error(j.error); pollSoon(); } catch (e) { msg(e.message); }
}));

function render(jobs) {
  const ul = $('jobs');
  if (!jobs.length) return;
  ul.innerHTML = '';
  jobs.forEach(j => {
    const li = document.createElement('li');
    const pill = j.status === 'running' ? '<span class="pill run"><span class="spin"></span>running</span>' :
      j.status === 'done' ? '<span class="pill ok">done</span>' : j.status === 'cancelled' ? '<span class="pill warn">cancelled</span>' : '<span class="pill bad">failed</span>';
    let links = '';
    if (j.result) {
      if (j.result.url) links += `<a href="${j.result.url}">Open report</a>`;
      if (j.result.report) links += `<a href="${j.result.report}" target="_blank">Open text report</a>`;
      if (j.result.best_params) links += `<a href="#" data-open="${esc(j.result.best_params)}">Report of the best set</a><a href="#" data-adopt="${esc(j.result.best_params)}">Save best set as a plan</a>`;
      if (j.result.type === 'log' || j.status !== 'done') links += `<a href="${esc(j.log_url)}" target="_blank">Full log</a>`;
    } else if (j.status !== 'running') links += `<a href="${esc(j.log_url)}" target="_blank">Full log</a>`;
    const cancel = j.status === 'running' ? `<button class="btn ghost" data-cancel="${j.id}" style="padding:4px 10px;font-size:13px">Stop</button>` : '';
    const mins = Math.floor(j.elapsed / 60), secs = j.elapsed % 60;
    li.innerHTML = `<div class="t"><span>${esc(j.label)}</span><span>${pill} ${cancel}</span></div>
      <div class="meta">${mins ? mins + ' min ' : ''}${secs} s</div>
      ${j.status === 'running' || !j.result || j.result.type === 'log' ? `<pre class="log">${esc(j.tail.join('\n'))}</pre>` : ''}
      <div class="links">${links}</div>`;
    ul.appendChild(li);
  });
  ul.querySelectorAll('[data-cancel]').forEach(b => b.onclick = async () => { await fetch('/api/jobs/' + b.dataset.cancel + '/cancel', {method: 'POST'}); pollSoon(); });
  ul.querySelectorAll('[data-open]').forEach(a => a.onclick = async e => { e.preventDefault(); msg('');
    try { const r = await fetch('/api/run', {method: 'POST', body: JSON.stringify({file: a.dataset.open, start: $('start').value, holdout_start: $('holdout').value})});
      const j = await r.json(); if (!r.ok) throw new Error(j.error); window.location.href = j.url; } catch (err) { msg(err.message); } });
  ul.querySelectorAll('[data-adopt]').forEach(a => a.onclick = async e => { e.preventDefault();
    const name = prompt('Name for the new plan:', 'Best of search'); if (!name) return;
    try { const r = await fetch('/api/adopt', {method: 'POST', body: JSON.stringify({file: a.dataset.adopt, name})});
      const j = await r.json(); if (!r.ok) throw new Error(j.error); msg(''); alert('Saved as strategies/' + j.file); status(); } catch (err) { msg(err.message); } });
}
let timer = null, running = false;
async function poll() {
  try { const jobs = await (await fetch('/api/jobs')).json(); render(jobs);
    const wasRunning = running; running = jobs.some(j => j.status === 'running');
    if (wasRunning && !running) status();
  } catch (e) {}
  clearTimeout(timer); timer = setTimeout(poll, running ? 2000 : 8000);
}
function pollSoon() { clearTimeout(timer); timer = setTimeout(poll, 300); }
status(); poll();
</script>
</body>
</html>
"""
