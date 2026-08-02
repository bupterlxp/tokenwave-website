/* TokenWave — shared page behaviors.
   Everything here is progressive enhancement: with JS disabled the
   pages render complete and static. */
(function () {
  'use strict';

  document.documentElement.classList.add('js');

  /* ── Header dropdown: managed open state ─────────────────
     Pure :hover thrashes when the pointer crosses the trigger→menu
     boundary; a class plus a close timer is deterministic. */
  document.querySelectorAll('.site-header .nav-item').forEach(function (item) {
    var closeTimer = null;
    item.addEventListener('pointerenter', function (e) {
      if (e.pointerType === 'touch') return;
      clearTimeout(closeTimer);
      item.classList.add('open');
    });
    item.addEventListener('pointerleave', function () {
      clearTimeout(closeTimer);
      closeTimer = setTimeout(function () { item.classList.remove('open'); }, 350);
    });
    /* Esc closes; keyboard users get :focus-within for free */
    item.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') item.classList.remove('open');
    });
  });

  var REDUCED = false;
  try {
    REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) {}

  /* ── Scroll reveals (.rv → .rv.in) ──────────────────────── */
  var revealEls = document.querySelectorAll('.rv');
  if (revealEls.length && 'IntersectionObserver' in window && !REDUCED) {
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('in');
          ro.unobserve(en.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { ro.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ── Count-up numerals ([data-count]) ───────────────────── */
  var counters = document.querySelectorAll('[data-count]');
  function runCount(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var suffix = el.getAttribute('data-suffix') || '';
    if (!isFinite(target)) return;
    if (REDUCED) { el.textContent = target + suffix; return; }
    var t0 = null, DUR = 1300;
    function tick(ts) {
      if (!t0) t0 = ts;
      var p = Math.min(1, (ts - t0) / DUR);
      var e = 1 - Math.pow(1 - p, 4);           /* quartic ease-out */
      el.textContent = Math.round(target * e) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  if (counters.length && 'IntersectionObserver' in window) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          runCount(en.target);
          co.unobserve(en.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { co.observe(el); });
  } else {
    counters.forEach(runCount);
  }

  /* ── Readiness meters (.meter span[data-w]) ─────────────── */
  var meters = document.querySelectorAll('.meter span[data-w]');
  function fillMeter(el) { el.style.width = el.getAttribute('data-w') + '%'; }
  if (meters.length && 'IntersectionObserver' in window && !REDUCED) {
    var mo = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          fillMeter(en.target);
          mo.unobserve(en.target);
        }
      });
    }, { threshold: 0.6 });
    meters.forEach(function (el) { mo.observe(el); });
  } else {
    meters.forEach(fillMeter);
  }

  /* ── Frontier chart (home): giant stat + single-hue bars ── */
  var frontier = document.getElementById('frontier');
  if (frontier && window.TW_FRONTIER && window.TW_FRONTIER.rows.length) {
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
    var bars = frontier.querySelectorAll('.fr-bar');
    function fillBars() { bars.forEach(function (b) { b.style.width = b.getAttribute('data-w') + '%'; }); }
    if ('IntersectionObserver' in window && !REDUCED) {
      var fo = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { fillBars(); fo.disconnect(); }
        });
      }, { threshold: 0.35 });
      fo.observe(frontier);
    } else {
      fillBars();
    }
  }

  /* ── Careers readiness index (home) ─────────────────────── */
  var cidx = document.getElementById('career-index');
  if (cidx && window.TW_CAREERS && window.TW_CAREERS.length) {
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
    /* meters inside get picked up by the meter observer below only if it
       runs after this — query again to be safe */
    cidx.querySelectorAll('.meter span[data-w]').forEach(function (el) {
      if (REDUCED || !('IntersectionObserver' in window)) {
        el.style.width = el.getAttribute('data-w') + '%';
      } else {
        var o = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (en.isIntersecting) {
              en.target.style.width = en.target.getAttribute('data-w') + '%';
              o.unobserve(en.target);
            }
          });
        }, { threshold: 0.6 });
        o.observe(el);
      }
    });
  }

  /* ── Live board marquee (home) ──────────────────────────── */
  var board = document.getElementById('board-track');
  if (board && window.TW_BOARD && window.TW_BOARD.length) {
    var frag = document.createDocumentFragment();
    /* two copies → seamless -50% translate loop */
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
})();
