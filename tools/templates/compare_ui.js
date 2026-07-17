/* Compare page UI. Prepended at build time with `window.TW_COMPARE = {...};`
 * so there is exactly one script, no load-order race, and no fetch()
 * (works over file:// and survives soft page transitions).
 * Re-executes safely: all state lives inside this closure and the DOM
 * is rebuilt from scratch under #cmp-root each run.
 */
(function () {
  'use strict';

  var DATA = window.TW_COMPARE;
  var root = document.getElementById('cmp-root');
  if (!root || !DATA) return;

  var MAX = 5;
  var selected = [];   // model ids, in selection order
  var query = '';

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function fmt(v) {
    return (typeof v === 'number') ? String(v) : '–';
  }

  root.innerHTML =
    '<div class="cmp-toolbar">' +
      '<input class="cmp-search" type="search" placeholder="Filter models or orgs…" aria-label="Filter models">' +
      '<span class="cmp-status"></span>' +
      '<button class="cmp-clear" type="button">Clear all</button>' +
    '</div>' +
    '<div class="cmp-models" role="group" aria-label="Select up to 5 models"></div>' +
    '<div class="cmp-result" aria-live="polite"></div>';

  var searchEl = root.querySelector('.cmp-search');
  var statusEl = root.querySelector('.cmp-status');
  var modelsEl = root.querySelector('.cmp-models');
  var resultEl = root.querySelector('.cmp-result');

  function renderStatus() {
    statusEl.innerHTML = '<b>' + selected.length + '</b> / ' + MAX + ' models selected';
  }

  function renderModels() {
    var q = query.toLowerCase();
    var full = selected.length >= MAX;
    var html = '';
    DATA.models.forEach(function (m) {
      if (q && (m.name + ' ' + m.org).toLowerCase().indexOf(q) === -1) return;
      var on = selected.indexOf(m.id) !== -1;
      html += '<button type="button" class="model-chip" data-id="' + esc(m.id) + '"' +
              ' aria-pressed="' + on + '"' +
              (!on && full ? ' disabled' : '') +
              ' style="--dot:' + esc(m.color || '#94a3b8') + '"' +
              ' title="' + esc(m.org) + '">' +
              '<span class="dot"></span>' +
              '<span class="nm">' + esc(m.name) + '</span>' +
              '<span class="cov">' + m.coverage + ' bm</span>' +
              '</button>';
    });
    modelsEl.innerHTML = html || '<p class="muted" style="margin:6px 2px;">No models match “' + esc(query) + '”.</p>';
  }

  function renderTable() {
    if (selected.length === 0) {
      resultEl.innerHTML =
        '<div class="cmp-empty"><p style="margin:0 0 6px;"><b>Select up to ' + MAX + ' models</b> for cross-benchmark comparison.</p>' +
        '<p style="margin:0;">Every benchmark where at least one selected model has a score will appear here.</p></div>';
      return;
    }

    var cols = selected.map(function (id) {
      for (var i = 0; i < DATA.models.length; i++) {
        if (DATA.models[i].id === id) return DATA.models[i];
      }
      return { id: id, name: id };
    });

    var head = '<tr><th>Benchmark</th>';
    cols.forEach(function (m) { head += '<th>' + esc(m.name) + '</th>'; });
    head += '</tr>';

    var body = '';
    DATA.benchmarks.forEach(function (b) {
      var vals = selected.map(function (id) { return b.scores[id]; });
      var any = vals.some(function (v) { return typeof v === 'number'; });
      if (!any) return;

      var nums = vals.filter(function (v) { return typeof v === 'number'; });
      var best = (b.dir === 'lower') ? Math.min.apply(null, nums) : Math.max.apply(null, nums);

      body += '<tr><td class="bench-cell">' +
              '<a class="bn" href="benchmarks/' + esc(b.file) + '.html">' + esc(b.name) + '</a>' +
              '<span class="bm">' + esc(b.domain_label) + ' · ' + esc(b.metric || 'score') + '</span>' +
              '</td>';
      vals.forEach(function (v) {
        if (typeof v !== 'number') { body += '<td class="na">–</td>'; return; }
        var cls = 'num' + (nums.length > 0 && v === best ? ' best' : '');
        body += '<td class="' + cls + '">' + fmt(v) + '</td>';
      });
      body += '</tr>';
    });

    if (!body) {
      resultEl.innerHTML = '<div class="cmp-empty"><p style="margin:0;">None of the selected models have scores yet.</p></div>';
      return;
    }

    resultEl.innerHTML =
      '<div class="table-scroll"><table class="data-table cmp-table">' +
      '<thead>' + head + '</thead><tbody>' + body + '</tbody></table></div>';
  }

  function renderAll() { renderStatus(); renderModels(); renderTable(); }

  modelsEl.addEventListener('click', function (e) {
    var chip = e.target.closest('.model-chip');
    if (!chip || chip.disabled) return;
    var id = chip.getAttribute('data-id');
    var at = selected.indexOf(id);
    if (at === -1) {
      if (selected.length >= MAX) return;
      selected.push(id);
    } else {
      selected.splice(at, 1);
    }
    renderAll();
  });

  searchEl.addEventListener('input', function () {
    query = searchEl.value.trim();
    renderModels();
  });

  root.querySelector('.cmp-clear').addEventListener('click', function () {
    selected = [];
    renderAll();
    searchEl.focus();
  });

  renderAll();
})();
