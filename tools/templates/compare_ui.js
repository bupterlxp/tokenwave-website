/* Compare page UI. Prepended at build time with `window.TW_COMPARE = {...};`
 * so there is exactly one script, no load-order race, and no fetch().
 * Re-executes safely after soft page transitions: all state lives in this
 * closure and the DOM is rebuilt from scratch under #cmp-root each run.
 *
 * Features: collapsed model list (top-coverage first, expandable), search
 * over the full model set, 5-model cap, shareable URL state (?m=id,id),
 * per-row score bars, and a domain-profile grouped bar chart.
 */
(function () {
  'use strict';

  var DATA = window.TW_COMPARE;
  var root = document.getElementById('cmp-root');
  if (!root || !DATA) return;

  var MAX = 5;
  var VISIBLE = 24;   // chips shown before "Show all"

  // Validated categorical series palette (dataviz reference instance, light).
  // Assigned per model at selection time and held until deselected —
  // color follows the entity, not its column position.
  var SERIES = ['#2a78d6', '#008300', '#e87ba4', '#eda100', '#1baf7a'];

  var DOMAINS = [
    { id: 'agent', label: 'Agent' },
    { id: 'multimodal', label: 'MLLM' },
    { id: 'aigc', label: 'AIGC' },
    { id: 'llm', label: 'LLM' },
  ];

  // Null-prototype maps + own-property checks: model ids come from the URL,
  // so "constructor"/"__proto__" must not resolve to inherited properties.
  function has(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }

  var byId = Object.create(null);
  DATA.models.forEach(function (m) { byId[m.id] = m; });

  var selected = [];                   // model ids in selection order
  var slotOf = Object.create(null);    // model id -> series slot index
  var expanded = false;
  var query = '';

  function assignSlot(id) {
    var used = {};
    Object.keys(slotOf).forEach(function (k) { used[slotOf[k]] = true; });
    for (var i = 0; i < SERIES.length; i++) {
      if (!used[i]) { slotOf[id] = i; return; }
    }
    slotOf[id] = 0;
  }
  function colorOf(id) { return SERIES[slotOf[id] || 0]; }

  /* ── URL state: compare.html?m=id1,id2 ── */
  try {
    var mparam = new URLSearchParams(window.location.search).get('m');
    if (mparam) {
      mparam.split(',').forEach(function (id) {
        if (has(byId, id) && selected.length < MAX && selected.indexOf(id) === -1) {
          selected.push(id);
          assignSlot(id);
        }
      });
    }
  } catch (e) {}

  function syncURL() {
    try {
      var url = window.location.pathname +
                (selected.length ? '?m=' + selected.join(',') : '') +
                window.location.hash;
      history.replaceState(history.state, '', url);
    } catch (e) {}
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function fmt(v) { return (typeof v === 'number') ? String(v) : '–'; }

  root.innerHTML =
    '<div class="cmp-toolbar">' +
      '<input class="cmp-search" type="search" placeholder="Search all ' + DATA.models.length + ' models or orgs…" aria-label="Search models">' +
      '<span class="cmp-status"></span>' +
      '<button class="cmp-copy" type="button" hidden>Copy link</button>' +
      '<button class="cmp-clear" type="button">Clear all</button>' +
    '</div>' +
    '<div class="cmp-models" role="group" aria-label="Select up to 5 models"></div>' +
    '<div class="cmp-more"></div>' +
    '<div class="cmp-chart"></div>' +
    '<div class="cmp-result" aria-live="polite"></div>' +
    '<div class="cmp-tip" hidden></div>';

  var searchEl = root.querySelector('.cmp-search');
  var statusEl = root.querySelector('.cmp-status');
  var copyEl = root.querySelector('.cmp-copy');
  var modelsEl = root.querySelector('.cmp-models');
  var moreEl = root.querySelector('.cmp-more');
  var chartEl = root.querySelector('.cmp-chart');
  var resultEl = root.querySelector('.cmp-result');
  var tipEl = root.querySelector('.cmp-tip');

  function renderStatus() {
    statusEl.innerHTML = '<b>' + selected.length + '</b> / ' + MAX + ' models selected';
    copyEl.hidden = selected.length === 0;
  }

  /* ── model chips: selected pinned first, then top coverage; collapsed by default ── */
  function renderModels() {
    var q = query.toLowerCase();
    var full = selected.length >= MAX;

    var pinned = selected.map(function (id) { return byId[id]; }).filter(Boolean);
    var rest = DATA.models.filter(function (m) { return selected.indexOf(m.id) === -1; });

    if (q) {
      var match = function (m) { return (m.name + ' ' + m.org).toLowerCase().indexOf(q) !== -1; };
      pinned = pinned.filter(match);
      rest = rest.filter(match);
    } else if (!expanded) {
      rest = rest.slice(0, Math.max(0, VISIBLE - pinned.length));
    }

    var html = '';
    pinned.concat(rest).forEach(function (m) {
      var on = selected.indexOf(m.id) !== -1;
      var dot = on ? colorOf(m.id) : (m.color || '#94a3b8');
      html += '<button type="button" class="model-chip" data-id="' + esc(m.id) + '"' +
              ' aria-pressed="' + on + '"' +
              (!on && full ? ' disabled' : '') +
              ' style="--dot:' + esc(dot) + '"' +
              ' title="' + esc(m.org) + '">' +
              '<span class="dot"></span>' +
              '<span class="nm">' + esc(m.name) + '</span>' +
              '<span class="cov">' + m.coverage + ' bm</span>' +
              '</button>';
    });
    modelsEl.innerHTML = html ||
      '<p class="muted" style="margin:6px 2px;">No models match “' + esc(query) + '”.</p>';

    if (q) {
      moreEl.innerHTML = '';
    } else {
      var hidden = DATA.models.length - Math.min(DATA.models.length, VISIBLE);
      moreEl.innerHTML = expanded
        ? '<button type="button" class="cmp-toggle">Show fewer models ↑</button>'
        : '<button type="button" class="cmp-toggle">Show all ' + DATA.models.length + ' models ↓ <span class="muted">(' + hidden + ' hidden, sorted by coverage)</span></button>';
    }
  }

  /* ── domain profile: mean share of metric range, higher-is-better only ── */
  function domainProfile() {
    var out = DOMAINS.map(function (dom) {
      return {
        domain: dom,
        bars: selected.map(function (id) {
          var vals = [];
          DATA.benchmarks.forEach(function (b) {
            if (b.domain !== dom.id) return;
            if (b.dir === 'lower') return;
            var v = b.scores[id];
            if (typeof v === 'number') {
              vals.push(Math.max(0, Math.min(100, v / (b.rmax || 100) * 100)));
            }
          });
          var avg = vals.length ? vals.reduce(function (a, x) { return a + x; }, 0) / vals.length : null;
          return { id: id, avg: avg, n: vals.length };
        }),
      };
    });
    return { groups: out };
  }

  function renderChart() {
    if (selected.length === 0) { chartEl.innerHTML = ''; return; }

    var prof = domainProfile();
    var any = prof.groups.some(function (g) {
      return g.bars.some(function (b) { return b.avg !== null; });
    });
    if (!any) { chartEl.innerHTML = ''; return; }

    var W = 720, H = 236, L = 36, R = 6, T = 12, B = 28;
    var plotW = W - L - R, plotH = H - T - B;
    var y = function (v) { return T + (1 - v / 100) * plotH; };

    var svg = [];
    [0, 25, 50, 75, 100].forEach(function (g) {
      svg.push('<line x1="' + L + '" y1="' + y(g) + '" x2="' + (W - R) + '" y2="' + y(g) +
               '" stroke="' + (g === 0 ? '#cbd5e1' : '#eef2f7') + '" stroke-width="1"/>');
      svg.push('<text x="' + (L - 6) + '" y="' + (y(g) + 3) + '" text-anchor="end" ' +
               'font-family="Plex Mono,monospace" font-size="9.5" fill="#94a3b8">' + g + '</text>');
    });

    var groupW = plotW / prof.groups.length;
    prof.groups.forEach(function (g, gi) {
      var bars = g.bars.filter(function (b) { return b.avg !== null; });
      var n = bars.length;
      var gx = L + gi * groupW;
      svg.push('<text x="' + (gx + groupW / 2) + '" y="' + (H - 8) + '" text-anchor="middle" ' +
               'font-family="Plex Mono,monospace" font-size="11" fill="#64748b">' + g.domain.label + '</text>');
      if (!n) return;
      var barW = Math.min(26, Math.max(10, (groupW - 44) / n - 2));
      var slot = barW + 2;                       // 2px surface gap between bars
      var startX = gx + (groupW - (n * slot - 2)) / 2;
      bars.forEach(function (b, bi) {
        var bx = startX + bi * slot;
        var by = y(b.avg);
        var r = Math.min(3, barW / 2);
        var bh = (T + plotH) - by;
        var c = colorOf(b.id);
        var path = bh <= r
          ? '<rect x="' + bx + '" y="' + by + '" width="' + barW + '" height="' + Math.max(1, bh) + '" fill="' + c + '"/>'
          : '<path d="M' + bx + ' ' + (T + plotH) + ' V' + (by + r) + ' Q' + bx + ' ' + by + ' ' + (bx + r) + ' ' + by +
            ' H' + (bx + barW - r) + ' Q' + (bx + barW) + ' ' + by + ' ' + (bx + barW) + ' ' + (by + r) +
            ' V' + (T + plotH) + ' Z" fill="' + c + '"/>';
        svg.push('<g class="cmp-bar" data-tip="' + esc(byId[b.id].name + ' — ' + g.domain.label + ': ' +
                 b.avg.toFixed(1) + ' avg share of range · ' + b.n + ' benchmark' + (b.n > 1 ? 's' : '')) + '">' +
                 path +
                 '<rect x="' + (bx - 2) + '" y="' + T + '" width="' + (barW + 4) + '" height="' + plotH + '" fill="transparent"/>' +
                 '</g>');
      });
    });

    var legend = selected.map(function (id) {
      return '<span class="lg"><span class="dot" style="background:' + colorOf(id) + '"></span>' +
             esc(byId[id].name) + '</span>';
    }).join('');

    chartEl.innerHTML =
      '<div class="cmp-legend">' + legend + '</div>' +
      '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Domain profile: average share of metric range per domain for the selected models">' +
      svg.join('') + '</svg>' +
      '<p class="cmp-caveat">Domain profile = unweighted mean of scores as a share of each metric’s range (0-floor assumed), over the higher-is-better benchmarks where that model is scored. Different models may be averaged over different benchmark subsets — hover a bar for its count. AIGC currently holds a single benchmark. Benchmarks are not calibrated against each other; this is a sketch, not a ranking. Exact numbers are in the table below.</p>';
  }

  /* ── comparison table with per-row score bars ── */
  function renderTable() {
    if (selected.length === 0) {
      resultEl.innerHTML =
        '<div class="cmp-empty"><p style="margin:0 0 6px;"><b>Select up to ' + MAX + ' models</b> for cross-benchmark comparison.</p>' +
        '<p style="margin:0;">Every benchmark where at least one selected model has a score will appear here — with a shareable link.</p></div>';
      return;
    }

    var head = '<tr><th>Benchmark</th>';
    selected.forEach(function (id) {
      head += '<th><span class="thdot" style="background:' + colorOf(id) + '"></span>' + esc(byId[id].name) + '</th>';
    });
    head += '</tr>';

    var body = '';
    DATA.benchmarks.forEach(function (b) {
      var vals = selected.map(function (id) { return b.scores[id]; });
      var nums = vals.filter(function (v) { return typeof v === 'number'; });
      if (!nums.length) return;

      var best = (b.dir === 'lower') ? Math.min.apply(null, nums) : Math.max.apply(null, nums);
      // Bar length always means "better" — for lower-is-better metrics the bar
      // shows distance from the range ceiling, so the best model stays longest.
      var goodness = function (v) { return (b.dir === 'lower') ? Math.max(0, (b.rmax || 100) - v) : v; };
      var barMax = Math.max.apply(null, nums.map(goodness)) || 1;

      body += '<tr><td class="bench-cell">' +
              '<a class="bn" href="benchmarks/' + esc(b.file) + '.html">' + esc(b.name) + '</a>' +
              '<span class="bm">' + esc(b.domain_label) + ' · ' + esc(b.metric || 'score') +
              (b.dir === 'lower' ? ' ↓' : '') + '</span>' +
              '</td>';
      vals.forEach(function (v, i) {
        if (typeof v !== 'number') { body += '<td class="na">–</td>'; return; }
        var pct = Math.max(2, goodness(v) / barMax * 100);
        var cls = 'num' + (v === best ? ' best' : '');
        body += '<td class="' + cls + '">' + fmt(v) +
                '<span class="cellbar"><span style="width:' + pct.toFixed(1) + '%;background:' + colorOf(selected[i]) + '"></span></span>' +
                '</td>';
      });
      body += '</tr>';
    });

    resultEl.innerHTML =
      '<div class="table-scroll"><table class="data-table cmp-table">' +
      '<thead>' + head + '</thead><tbody>' + body + '</tbody></table></div>';
  }

  function renderAll() {
    renderStatus();
    renderModels();
    renderChart();
    renderTable();
    syncURL();
  }

  /* ── events ── */
  root.addEventListener('click', function (e) {
    var chip = e.target.closest('.model-chip');
    if (chip && !chip.disabled) {
      var id = chip.getAttribute('data-id');
      if (!has(byId, id)) return;
      var at = selected.indexOf(id);
      if (at === -1) {
        if (selected.length >= MAX) return;
        selected.push(id);
        assignSlot(id);
      } else {
        selected.splice(at, 1);
        delete slotOf[id];
      }
      renderAll();
      return;
    }
    if (e.target.closest('.cmp-toggle')) {
      expanded = !expanded;
      renderModels();
      return;
    }
    if (e.target.closest('.cmp-clear')) {
      selected = [];
      slotOf = Object.create(null);
      renderAll();
      searchEl.focus();
      return;
    }
    if (e.target.closest('.cmp-copy')) {
      var url = window.location.href;
      var done = function () {
        copyEl.textContent = 'Copied ✓';
        setTimeout(function () { copyEl.textContent = 'Copy link'; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, function () { window.prompt('Copy this link:', url); });
      } else {
        window.prompt('Copy this link:', url);
      }
    }
  });

  searchEl.addEventListener('input', function () {
    query = searchEl.value.trim();
    renderModels();
  });

  /* chart tooltip */
  chartEl.addEventListener('mousemove', function (e) {
    var bar = e.target.closest('.cmp-bar');
    if (!bar) { tipEl.hidden = true; return; }
    tipEl.textContent = bar.getAttribute('data-tip');
    tipEl.hidden = false;
    var r = root.getBoundingClientRect();
    tipEl.style.left = Math.max(0, Math.min(e.clientX - r.left + 14, r.width - 240)) + 'px';
    tipEl.style.top = (e.clientY - r.top - 34) + 'px';
  });
  chartEl.addEventListener('mouseleave', function () { tipEl.hidden = true; });

  renderAll();
})();
