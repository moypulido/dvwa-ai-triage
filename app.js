// dvwa-ai-triage dashboard. Reads metrics.json (aggregates only) and draws the page.
// Names in metrics.json (modules, tools) come from file paths a PR author controls, so
// everything goes through textContent: nothing from the JSON is ever parsed as HTML.
(function () {
  'use strict';

  const app = document.getElementById('app');
  const meta = document.getElementById('meta');
  const tip = document.getElementById('tip');

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  };
  const num = (v) => { const n = Number(v); return Number.isFinite(n) ? n : 0; };
  const pc = (r) => (r === null || r === undefined ? 'n/a' : `${Math.round(num(r) * 1000) / 10}%`);
  const dur = (h) => (h === null || h === undefined ? 'n/a' : num(h) < 1 ? `${Math.round(num(h) * 60)} min` : `${num(h)} h`);
  const when = (iso) => (iso ? `${String(iso).slice(0, 16).replace('T', ' ')} UTC` : 'n/a');
  const entries = (o) => Object.entries(o && typeof o === 'object' ? o : {}).map(([name, v]) => ({ name, value: num(v) }));
  const ordered = (o, order) => {
    const all = entries(o);
    const known = order.map((name) => all.find((e) => e.name === name) || { name, value: 0 });
    return known.concat(all.filter((e) => !order.includes(e.name)));
  };

  // Hover and keyboard focus show the same text.
  const showTip = (target, text) => {
    const show = (x, y) => {
      tip.textContent = text;
      tip.hidden = false;
      const w = tip.offsetWidth;
      tip.style.left = `${Math.max(8, Math.min(x + 12, window.innerWidth - w - 8))}px`;
      tip.style.top = `${Math.max(8, y - 34)}px`;
    };
    target.addEventListener('mousemove', (e) => show(e.clientX, e.clientY));
    target.addEventListener('mouseleave', () => { tip.hidden = true; });
    target.addEventListener('focus', () => { const r = target.getBoundingClientRect(); show(r.left, r.top); });
    target.addEventListener('blur', () => { tip.hidden = true; });
    target.tabIndex = 0;
    target.setAttribute('aria-label', text);
  };

  const section = (title) => { app.appendChild(el('h2', '', title)); };
  const card = (title, sub) => {
    const c = el('section', 'card');
    if (title) c.appendChild(el('h3', '', title));
    if (sub) c.appendChild(el('p', 'sub', sub));
    return c;
  };
  const grid = (cls, cards) => {
    const g = el('div', `grid ${cls}`);
    cards.forEach((c) => g.appendChild(c));
    app.appendChild(g);
    return g;
  };
  const tile = (label, value, hint) => {
    const c = el('section', 'card tile');
    c.appendChild(el('p', 'label', label));
    c.appendChild(el('p', 'value', value));
    if (hint) c.appendChild(el('p', 'hint', hint));
    return c;
  };

  // One-hue horizontal bars on a shared baseline. Width is set through the CSSOM (allowed by the CSP).
  const barList = (rows, opts) => {
    const o = opts || {};
    const max = o.max || Math.max(1, ...rows.map((r) => r.value));
    const total = rows.reduce((t, r) => t + r.value, 0);
    const ul = el('ul', o.meter ? 'bars meter' : 'bars');
    if (!rows.length) { ul.appendChild(el('li', '', 'No data yet.')); return ul; }
    rows.forEach((r) => {
      const li = el('li');
      li.appendChild(el('span', 'name', r.name));
      const plot = el('span', 'plot');
      const bar = el('span', r.value > 0 ? 'bar' : 'bar zero');
      bar.style.display = 'block';
      bar.style.width = `${Math.max(0, Math.min(100, (r.value / max) * 100))}%`;
      plot.appendChild(bar);
      li.appendChild(plot);
      li.appendChild(el('span', 'val', r.label !== undefined ? r.label : r.value));
      showTip(li, r.tip || `${r.name}: ${r.value}${o.share && total ? ` (${pc(r.value / total)} of ${total})` : ''}`);
      ul.appendChild(li);
    });
    return ul;
  };

  // Colour follows the entity, never its rank: each known name keeps its slot.
  const segmented = (rows, colors) => {
    const total = rows.reduce((t, r) => t + r.value, 0);
    const wrap = el('div');
    const bar = el('div', 'seg');
    bar.setAttribute('role', 'img');
    bar.setAttribute('aria-label', rows.map((r) => `${r.name} ${r.value}`).join(', ') || 'No data');
    const legend = el('ul', 'legend');
    rows.forEach((r) => {
      const cls = colors[r.name] || 'c-other';
      if (r.value > 0) {
        const s = el('span', cls);
        s.style.flex = `${r.value} 1 0`;
        bar.appendChild(s);
      }
      const li = el('li');
      li.appendChild(el('span', `sw ${cls}`));
      li.appendChild(el('span', 'name', r.name));
      li.appendChild(el('span', 'val', r.value));
      li.appendChild(el('span', 'share', total ? pc(r.value / total) : 'n/a'));
      showTip(li, `${r.name}: ${r.value}${total ? ` (${pc(r.value / total)} of ${total})` : ''}`);
      legend.appendChild(li);
    });
    if (!total) bar.appendChild(el('span', 'c-other')).style.flex = '1 1 0';
    wrap.appendChild(bar);
    wrap.appendChild(legend);
    return wrap;
  };

  const matrix = (head, rows) => {
    const t = el('table', 'matrix');
    const hr = el('tr');
    head.forEach((h) => hr.appendChild(el('th', '', h)));
    t.appendChild(hr);
    rows.forEach((r) => {
      const tr = el('tr');
      r.forEach((c, i) => tr.appendChild(el(i === 0 ? 'th' : 'td', '', c)));
      t.appendChild(tr);
    });
    return t;
  };

  function render(m) {
    const v = m.volume || {}, d = m.dedup || {}, dec = m.decisions || {}, t = m.time_to_decision || {};
    const ai = m.ai || {}, ag = m.agreement || {}, pg = m.proof_gaps || {}, dist = m.distributions || {};
    const win = m.window || {}, dq = m.data_quality || {};

    meta.textContent = `Data from ${when(win.first_run)} to ${when(win.last_run)} · generated ${when(m.generated_at)} · schema ${m.schema_version || '?'}`;

    if (dq.occurrences_match_sightings === false) {
      const b = el('div', 'banner');
      b.setAttribute('role', 'status');
      b.appendChild(el('span', 'icon', '!'));
      b.appendChild(el('p', '', 'Warning: these metrics were computed while a scan was still being recorded. Totals may be off until the next update.'));
      app.appendChild(b);
    }

    // Headline: what the pipeline saves.
    section('Value signal');
    const hero = el('section', 'card hero');
    hero.appendChild(el('div', 'figure', pc(d.saved_rate)));
    const ht = el('div');
    ht.appendChild(el('p', 'label', 'of reviews avoided by deduplication'));
    ht.appendChild(el('p', 'sub', `${num(d.reviews_saved)} of ${num(d.reviews_without_dedup)} scanner records needed no new human decision: `
      + `${num(d.repeat_sightings)} were findings already seen in an earlier run and ${num(d.duplicates_within_runs)} were duplicates inside a run. `
      + `${num(v.emails_sent)} emails went out for ${num(v.runs)} runs; runs with nothing new to decide stay silent.`));
    hero.appendChild(ht);
    app.appendChild(hero);

    const decided = num(dec.decided), open = num(dec.open);
    grid('tiles', [
      tile('Scan runs', num(v.runs), `${num(v.prs)} pull requests`),
      tile('Unique findings', num(v.unique_findings), `${num(v.review_locations)} code locations`),
      tile('Decided by a human', `${decided} of ${decided + open}`, `${open} open`),
      tile('Actionable rate', pc(dec.actionable_rate), 'accepted ÷ decided'),
      tile('False positives', pc(dec.false_positive_rate), `${num((dec.by_disposition || {}).false_positive)} findings`),
      tile('Time to decision', dur(t.median_h), `median · p90 ${dur(t.p90_h)}`),
    ]).style.marginTop = '12px';

    section('From scanner output to decisions');
    const funnel = card('Pipeline volume', 'Each step is smaller because repeats are recognised and grouped.');
    funnel.appendChild(barList([
      { name: 'Scanner records', value: num(v.raw_records) },
      { name: 'Unique findings', value: num(v.unique_findings) },
      { name: 'Code locations', value: num(v.review_locations) },
      { name: 'Emails sent', value: num(v.emails_sent) },
    ]));
    const disp = card('Human decisions', 'Latest disposition of each decided finding.');
    disp.appendChild(segmented(ordered(dec.by_disposition, ['accepted', 'false_positive', 'suppressed']).filter((r) => r.value > 0 || ['accepted', 'false_positive', 'suppressed'].includes(r.name)),
      { accepted: 'c-s1', false_positive: 'c-s2', suppressed: 'c-s3', needs_evidence: 'c-s4', escalated: 'c-s5' }));
    const sev = card('Final severity', 'Set by the reviewer, most severe first.');
    sev.appendChild(barList(ordered(dist.final_severity, ['critical', 'high', 'medium', 'low', 'info']), { share: true }));
    grid('three', [funnel, disp, sev]);

    section('AI suggestions and the human');
    const agree = card('AI vs human', `Compared on ${num(ag.verdict_compared)} findings where both gave a verdict.`);
    agree.appendChild(barList([
      { name: 'Same verdict', value: num(ag.verdict_agreement_rate), label: pc(ag.verdict_agreement_rate), tip: `Same verdict: ${pc(ag.verdict_agreement_rate)} of ${num(ag.verdict_compared)}` },
      { name: 'Same severity', value: num(ag.severity_exact_rate), label: pc(ag.severity_exact_rate), tip: `Same severity: ${pc(ag.severity_exact_rate)} of ${num(ag.severity_compared)}` },
      { name: 'Within one level', value: num(ag.severity_within_one_rate), label: pc(ag.severity_within_one_rate), tip: `Severity within one level: ${pc(ag.severity_within_one_rate)} of ${num(ag.severity_compared)}` },
    ], { meter: true, max: 1 }));
    agree.appendChild(el('p', 'note', `The reviewer raised the AI's severity ${num(ag.human_raised_severity)} times and lowered it ${num(ag.human_lowered_severity)} times. Agreement is not accuracy.`));

    const conf = card('Verdicts side by side', 'Rows: what the AI suggested. Columns: what the human decided.');
    conf.appendChild(matrix(['', 'Human: real', 'Human: false positive'], [
      ['AI: real', num(ag.ai_real_human_real), num(ag.ai_real_human_false_positive)],
      ['AI: likely false positive', num(ag.ai_false_positive_human_real), num(ag.ai_false_positive_human_false_positive)],
    ]));
    conf.appendChild(el('p', 'note', `The AI abstained (needs evidence) on ${num(ag.ai_abstained_needs_evidence)} findings.`));

    const prov = card('AI reliability', `${num(ai.eligible)} findings eligible; ${num(ai.not_sent_secrets)} secrets are never sent to an AI.`);
    prov.appendChild(segmented(ordered(ai.by_provider, ['gemini', 'groq', 'none']), { gemini: 'c-s1', groq: 'c-s2', none: 'c-other' }));
    prov.appendChild(el('p', 'note', `Fallback used on ${pc(ai.fallback_rate)}. No suggestion on ${pc(ai.failure_rate)}. Suspected prompt injections: ${num(ai.injection_suspected)}.`));
    grid('three', [agree, conf, prov]);

    section('Review quality signals');
    grid('tiles', [
      tile('Short rationales', pc(dec.short_rationale_rate), `${num(dec.short_rationales)} of ${decided} decisions under 20 characters`),
      tile('Impossible-level findings', num(dec.findings_in_impossible_level), `${num(dec.false_positives_in_impossible_level)} marked false positive`),
      tile('Decided more than once', num(dec.findings_decided_more_than_once), `${num(dec.log_entries)} audit log entries`),
      tile('Open proof gaps', num(pg.open_gaps), `${ai.avg_proof_gaps === null || ai.avg_proof_gaps === undefined ? 'n/a' : ai.avg_proof_gaps} listed per finding on average`),
    ]);
    app.appendChild(el('p', 'note', 'These numbers describe the review, not the code. A high share of short rationales, or validated code never marked as a false positive, means the decisions leaned on the AI and should be re-checked.'));

    section('Where the findings are');
    const mk = (title, sub, rows) => { const c = card(title, sub); c.appendChild(barList(rows, { share: true })); return c; };
    grid('three', [
      mk('By tool', 'semgrep (code), trivy (Dockerfile), gitleaks (secrets).', entries(dist.tool)),
      mk('By module', 'DVWA module of the file; (none) is outside a module.', entries(dist.module)),
      mk('By DVWA level', 'Impossible is the hardened version of each module.', ordered(dist.dvwa_level, ['low', 'medium', 'high', 'impossible'])),
      mk('By scanner severity', 'As reported by the tool, before any review.', ordered(dist.scanner_severity, ['error', 'warning', 'note'])),
      mk('By origin', 'pr: on lines the pull request changed. preexisting: already in the code.', ordered(dist.origin, ['pr', 'preexisting'])),
    ]);
  }

  fetch('metrics.json', { cache: 'no-store' })
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then((m) => { if (!m || typeof m !== 'object' || !m.volume) throw new Error('unexpected format'); render(m); })
    .catch((e) => {
      meta.textContent = '';
      const c = card('No metrics yet', `metrics.json could not be loaded (${e.message}).`);
      app.appendChild(c);
    });
}());
