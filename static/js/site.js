/* TokenWave — shared page behaviors.
   Everything here is progressive enhancement: with JS disabled the
   pages render complete and static.

   transition.js swaps <main> in place on soft navigations and then
   fires "tw:swap"; everything page-scoped lives in initPage() and is
   re-armed on that event. One-time wiring (header dropdown, spotlight
   delegation, scroll progress) stays outside. */
(function () {
  'use strict';

  document.documentElement.classList.add('js');

  var REDUCED = false;
  try {
    REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) {}

  /* ════ One-time wiring (survives <main> swaps) ════════════ */

  /* Scroll progress hairline */
  if (!REDUCED) {
    var prog = document.createElement('div');
    prog.id = 'scroll-progress';
    document.body.appendChild(prog);
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var max = document.documentElement.scrollHeight - window.innerHeight;
        prog.style.width = (max > 0 ? (window.scrollY / max) * 100 : 0) + '%';
        ticking = false;
      });
    }, { passive: true });
  }

  /* Cursor spotlight on cards (delegated — new nodes just work) */
  var SPOT_SEL = '.bench-chip, .list .card, .rc-card, .report-panel, .cx-row, .stat-tile, .ev-card, .dir-card';
  document.addEventListener('pointermove', function (e) {
    if (e.pointerType === 'touch') return;
    var el = e.target.closest && e.target.closest(SPOT_SEL);
    if (!el) return;
    var r = el.getBoundingClientRect();
    el.style.setProperty('--sx', (e.clientX - r.left) + 'px');
    el.style.setProperty('--sy', (e.clientY - r.top) + 'px');
  }, { passive: true });

  /* ════ Page-scoped enhancements (re-armed on tw:swap) ═════ */

  var pageObservers = [];

  function watch(observer) {
    pageObservers.push(observer);
    return observer;
  }

  /* Observe a set of elements; run fn once per element on intersect.
     Falls back to running immediately (no IO / reduced motion). */
  function onVisible(els, fn, opts, force) {
    els = Array.prototype.slice.call(els);
    if (!els.length) return;
    if ((REDUCED && !force) || !('IntersectionObserver' in window)) {
      els.forEach(fn);
      return;
    }
    var io = watch(new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          fn(en.target);
          io.unobserve(en.target);
        }
      });
    }, opts || { threshold: 0.35 }));
    els.forEach(function (el) { io.observe(el); });
  }

  var revealWatchdog = null;

  function initPage() {
    pageObservers.forEach(function (o) { o.disconnect(); });
    pageObservers = [];

    /* Failsafe: staged reveals are decoration, never a gate. Whatever
       hasn't revealed within 2.5s becomes visible unconditionally. */
    clearTimeout(revealWatchdog);
    revealWatchdog = setTimeout(function () {
      document.querySelectorAll('.rv:not(.in)').forEach(function (el) {
        el.classList.add('in');
      });
    }, 2500);

    /* Side rail scrollspy (careers) */
    var rail = document.querySelector('.rail');
    if (rail && 'IntersectionObserver' in window) {
      var links = {};
      rail.querySelectorAll('a[href^="#"]').forEach(function (a) {
        links[a.getAttribute('href').slice(1)] = a;
      });
      var ro2 = watch(new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          Object.keys(links).forEach(function (k) { links[k].classList.remove('on'); });
          var l = links[en.target.id];
          if (l) l.classList.add('on');
        });
      }, { rootMargin: '-20% 0px -55% 0px' }));
      Object.keys(links).forEach(function (k) {
        var el = document.getElementById(k);
        if (el) ro2.observe(el);
      });
      var first = rail.querySelector('a');
      if (first) first.classList.add('on');
    }

    /* Scroll reveals */
    var rvs = document.querySelectorAll('.rv:not(.in)');
    if (REDUCED || !('IntersectionObserver' in window)) {
      rvs.forEach(function (el) { el.classList.add('in'); });
    } else {
      onVisible(rvs, function (el) { el.classList.add('in'); },
                { rootMargin: '0px 0px -8% 0px', threshold: 0.08 }, true);
    }

    /* Count-up numerals */
    onVisible(document.querySelectorAll('[data-count]'), function (el) {
      var target = parseFloat(el.getAttribute('data-count'));
      var suffix = el.getAttribute('data-suffix') || '';
      if (!isFinite(target)) return;
      if (REDUCED) { el.textContent = target + suffix; return; }
      var t0 = null, DUR = 1300;
      (function tick(ts) {
        if (ts == null) { requestAnimationFrame(tick); return; }
        if (!t0) t0 = ts;
        var p = Math.min(1, (ts - t0) / DUR);
        var e = 1 - Math.pow(1 - p, 4);
        el.textContent = Math.round(target * e) + suffix;
        if (p < 1) requestAnimationFrame(tick);
      })(null);
    }, { threshold: 0.5 });

    /* Meters (careers readiness) */
    onVisible(document.querySelectorAll('.meter span[data-w]'), function (el) {
      el.style.width = el.getAttribute('data-w') + '%';
    }, { threshold: 0.6 });

    /* Leaderboard score bars */
    onVisible(document.querySelectorAll('.lb-bar[data-w]'), function (el) {
      el.style.width = el.getAttribute('data-w') + '%';
    }, { rootMargin: '0px 0px -5% 0px', threshold: 0.4 });

    /* Frontier chart (home) */
    var frontier = document.getElementById('frontier');
    if (frontier && window.TW_FRONTIER && window.TW_FRONTIER.rows.length &&
        !frontier.querySelector('.fr-row')) {
      var F = window.TW_FRONTIER;
      var top = document.getElementById('frontier-top');
      if (top && F.rows[0]) {
        top.innerHTML = F.rows[0].s + '<span class="u">%</span>';
      }
      var max = F.rows.reduce(function (a, r) { return Math.max(a, r.s); }, 0);
      var html = '';
      F.rows.forEach(function (r, idx) {
        var w = max > 0 ? (r.s / max) * 100 : 0;
        html +=
          '<div class="fr-row' + (idx === 0 ? ' fr-lead' : '') + '">' +
            '<span class="fr-m">' + r.m + '</span>' +
            '<span class="fr-track"><span class="fr-bar" data-w="' + w.toFixed(1) + '"></span></span>' +
            '<span class="fr-v">' + r.s + '</span>' +
          '</div>';
      });
      frontier.innerHTML = html;
      onVisible([frontier], function () {
        frontier.querySelectorAll('.fr-bar').forEach(function (b) {
          b.style.width = b.getAttribute('data-w') + '%';
        });
      }, { threshold: 0.35 });
    }

    /* Careers readiness index (home) */
    var cidx = document.getElementById('career-index');
    if (cidx && window.TW_CAREERS && window.TW_CAREERS.length &&
        !cidx.querySelector('.cx-row')) {
      var STATUS = { certifying: 'Certifying now', next: 'Next in line' };
      var chtml = '';
      window.TW_CAREERS.forEach(function (c, i) {
        chtml +=
          '<a class="cx-row" href="careers.html#' + c.id + '">' +
            '<span class="cx-i">' + (i < 9 ? '0' : '') + (i + 1) + '</span>' +
            '<span class="cx-n">' + c.name + '</span>' +
            '<span class="cx-st career-status st-' + c.status + '">' + (STATUS[c.status] || '') + '</span>' +
            '<span class="cx-meter meter"><span data-w="' + (c.pct || 0) + '"></span></span>' +
            '<span class="cx-v">' + (c.pct != null ? c.pct + '%' : '–') + '</span>' +
            '<span class="cx-c">' + c.n + ' benchmarks</span>' +
          '</a>';
      });
      cidx.innerHTML = chtml;
      onVisible(cidx.querySelectorAll('.meter span[data-w]'), function (el) {
        el.style.width = el.getAttribute('data-w') + '%';
      }, { threshold: 0.6 });
    }

    /* Live board marquee (home) */
    var board = document.getElementById('board-track');
    if (board && window.TW_BOARD && window.TW_BOARD.length && !board.childElementCount) {
      var frag = document.createDocumentFragment();
      for (var loop = 0; loop < 2; loop++) {
        window.TW_BOARD.forEach(function (row) {
          var a = document.createElement('a');
          a.className = 'board-item';
          a.href = row.h;
          if (loop === 1) a.setAttribute('aria-hidden', 'true');
          var b = document.createElement('span');
          b.className = 'b';
          b.textContent = row.n;
          var m = document.createElement('span');
          m.className = 'm';
          m.textContent = row.m;
          var s = document.createElement('span');
          s.className = 's';
          s.textContent = row.s;
          a.appendChild(b); a.appendChild(m); a.appendChild(s);
          frag.appendChild(a);
        });
      }
      board.appendChild(frag);
    }

    /* Certification report: live simulation (home) */
    var panel = document.getElementById('report-sim');
    if (panel && !REDUCED && !panel.dataset.sim) {
      panel.dataset.sim = '1';
      var UNITS = [
        {
          id: 'WORK UNIT · WF-0338',
          rows: [
            ['sop', 'Monthly close — reconciliation workflow', false],
            ['certification set', 'PASS · hidden 40/40', true],
            ['pass@3 stability', '3 / 3 runs converged', false],
            ['final artifact', 'verifier check ✓', true],
            ['human handoff', '0 interventions', false],
            ['unit cost', 'within SLA envelope', false]
          ]
        },
        {
          id: 'WORK UNIT · SE-1204',
          rows: [
            ['sop', 'Dependency upgrade — CI back to green', false],
            ['certification set', 'PASS · hidden 36/36', true],
            ['pass@3 stability', '3 / 3 runs converged', false],
            ['final artifact', 'test suite ✓ · build ✓', true],
            ['human handoff', '1 approval gate', false],
            ['unit cost', 'within SLA envelope', false]
          ]
        },
        {
          id: 'WORK UNIT · EV-0771',
          rows: [
            ['sop', 'Release gate — regression review', false],
            ['certification set', 'PASS · hidden 52/52', true],
            ['pass@3 stability', '3 / 3 runs converged', false],
            ['final artifact', 'scored report ✓', true],
            ['human handoff', '0 interventions', false],
            ['unit cost', 'within SLA envelope', false]
          ]
        }
      ];
      var title = panel.querySelector('.rp-title');
      var badge = panel.querySelector('.rp-badge');
      var rowEls = Array.prototype.slice.call(panel.querySelectorAll('.rp-row'));
      rowEls.forEach(function (r) { r.classList.add('sim', 'on'); });
      var unitIdx = 0;

      function playUnit(u) {
        if (!document.contains(panel)) return;   /* main was swapped away */
        title.textContent = u.id;
        badge.textContent = 'RUNNING';
        badge.classList.add('running');
        rowEls.forEach(function (r) { r.classList.remove('on'); });
        u.rows.forEach(function (data, i) {
          var el = rowEls[i];
          if (!el) return;
          setTimeout(function () {
            el.querySelector('.k').textContent = data[0];
            var v = el.querySelector('.v');
            v.textContent = data[1];
            v.classList.toggle('ok', data[2]);
            el.classList.add('on');
          }, 380 + i * 300);
        });
        setTimeout(function () {
          badge.textContent = 'VERIFIED';
          badge.classList.remove('running');
        }, 380 + u.rows.length * 300 + 250);
        setTimeout(function () {
          unitIdx = (unitIdx + 1) % UNITS.length;
          playUnit(UNITS[unitIdx]);
        }, 380 + u.rows.length * 300 + 4600);
      }

      onVisible([panel], function () { playUnit(UNITS[0]); }, { threshold: 0.4 });
    }
  }

  initPage();
  window.addEventListener('tw:swap', initPage);
})();
