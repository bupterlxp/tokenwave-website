/* TokenWave page transitions.
 *
 * Two navigation modes:
 *   soft — between top-level pages: fetch the target, swap <main> in place,
 *          keep the particle canvas alive (no reload, no flicker).
 *   full — entering/leaving a detail page (benchmarks/, research/): fade the
 *          whole document, snapshot the particle field, restore on arrival.
 *
 * Contract with particles.js: window.PageTransition.onParticlesReady() is
 * called after the first rendered frame; freezeParticles()/resumeParticles()
 * are used around full navigations and bfcache restores.
 */
(function () {
  'use strict';

  var mainEl = document.querySelector('main');
  var TOP_LEVEL = ['/', '/index.html', '/careers.html', '/research.html', '/joinus.html'];

  var SOFT_OUT = 320;   // ms: main fade-out before fetch swap
  var SOFT_IN  = 360;   // ms: settle time before cards may rise
  var FULL_OUT = 420;   // ms: whole-page fade before hard nav

  function tail(path) {
    var base = path.split('/').pop();
    return base === '' ? '/' : '/' + base;
  }
  function isTopLevel(path) { return TOP_LEVEL.indexOf(tail(path)) !== -1; }

  var arrival = null;
  try {
    arrival = sessionStorage.getItem('tokenwave_transition');
    sessionStorage.removeItem('tokenwave_transition');
  } catch (e) {}

  var revealFallback = null;

  var PT = window.PageTransition = {
    state: 'idle',

    init: function () {
      if (arrival === 'full') {
        // Document was pre-hidden by the inline <head> guard
        PT.state = 'entering';
        if (mainEl) { mainEl.style.transition = 'none'; mainEl.style.opacity = '1'; }
        revealFallback = setTimeout(PT._reveal, 1400);
      } else if (arrival === 'soft' && isTopLevel(window.location.pathname)) {
        PT.state = 'entering';
        revealFallback = setTimeout(PT._reveal, 1400);
      } else {
        // Direct entry: show immediately
        if (mainEl) {
          mainEl.style.transition = 'none';
          mainEl.style.opacity = '1';
          mainEl.classList.add('page-visible');
          mainEl.classList.add('cards-ready');
        }
      }
    },

    onParticlesReady: function () {
      if (PT.state === 'entering') PT._reveal();
    },

    _reveal: function () {
      if (PT.state !== 'entering') return;
      if (revealFallback) { clearTimeout(revealFallback); revealFallback = null; }

      if (arrival === 'full') {
        var html = document.documentElement;
        html.style.transition = 'opacity 0.38s ease';
        setTimeout(function () {
          html.style.opacity = '1';
          if (mainEl) mainEl.classList.add('page-visible');
          setTimeout(function () {
            if (mainEl) mainEl.classList.add('cards-ready');
            PT.state = 'idle';
          }, 400);
        }, 120);
      } else {
        setTimeout(function () {
          if (mainEl) mainEl.classList.add('page-visible');
          setTimeout(function () {
            if (mainEl) mainEl.classList.add('cards-ready');
            PT.state = 'idle';
          }, SOFT_IN);
        }, 160);
      }
    },

    /* Replace <main> with the fetched document's, sync title + nav state,
       and re-execute scripts inside main (inline AND external src). */
    _swap: function (html, path) {
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var newMain = doc.querySelector('main');
      var newTitle = doc.querySelector('title');
      if (newMain) mainEl.innerHTML = newMain.innerHTML;
      if (newTitle) document.title = newTitle.textContent;

      document.querySelectorAll('nav a').forEach(function (a) {
        if (tail(a.pathname) === tail(path)) a.classList.add('active');
        else a.classList.remove('active');
      });

      mainEl.querySelectorAll('script').forEach(function (old) {
        var s = document.createElement('script');
        if (old.src) s.src = old.getAttribute('src');
        else s.textContent = old.textContent;
        old.parentNode.replaceChild(s, old);
      });

      // Re-arm site.js enhancements (reveals, charts, marquee, …) on the
      // freshly injected <main> — they were wired to the old DOM.
      window.dispatchEvent(new Event('tw:swap'));
    },

    navigate: function (mode, href) {
      if (PT.state === 'leaving') return;
      PT.state = 'leaving';

      if (mode === 'full') {
        try { sessionStorage.setItem('tokenwave_transition', 'full'); } catch (e) {}
        if (typeof window.freezeParticles === 'function') window.freezeParticles();
        document.body.style.transition = 'opacity 0.38s ease';
        document.body.style.opacity = '0';
        setTimeout(function () { window.location.href = href; }, FULL_OUT);
      } else {
        mainEl.classList.remove('cards-ready');
        mainEl.classList.remove('page-visible');
        setTimeout(function () {
          fetch(href).then(function (r) { return r.text(); }).then(function (html) {
            PT._swap(html, href);
            history.pushState({ path: href }, '', href);
            window.scrollTo(0, 0);
            mainEl.classList.add('page-visible');
            setTimeout(function () {
              mainEl.classList.add('cards-ready');
              PT.state = 'idle';
            }, SOFT_IN);
          }).catch(function () { window.location.href = href; });
        }, SOFT_OUT);
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { PT.init(); });
  } else {
    PT.init();
  }

  /* bfcache restore: undo any fade state and resume the particle loop */
  window.addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    document.body.style.opacity = '1';
    document.body.style.transition = '';
    document.documentElement.style.opacity = '1';
    document.documentElement.style.transition = '';
    if (mainEl) {
      mainEl.style.opacity = '1';
      mainEl.classList.add('page-visible');
      mainEl.classList.add('cards-ready');
    }
    if (typeof window.resumeParticles === 'function') window.resumeParticles();
    PT.state = 'idle';
    arrival = null;
  });

  /* Back/forward between top-level pages stays soft; anything else reloads */
  window.addEventListener('popstate', function () {
    var path = window.location.pathname;
    if (!isTopLevel(path)) { window.location.reload(); return; }
    mainEl.classList.remove('cards-ready');
    mainEl.classList.remove('page-visible');
    fetch(path).then(function (r) { return r.text(); }).then(function (html) {
      PT._swap(html, path);
      mainEl.classList.add('page-visible');
      setTimeout(function () { mainEl.classList.add('cards-ready'); }, SOFT_IN);
    }).catch(function () { window.location.reload(); });
  });

  /* Intercept same-site link clicks */
  document.addEventListener('click', function (e) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    var anchor = e.target.closest('a');
    if (!anchor) return;
    var href = anchor.getAttribute('href');
    if (!href) return;
    if ((anchor.hostname && anchor.hostname !== window.location.hostname) ||
        href.indexOf('#') !== -1 ||
        href.indexOf('mailto:') === 0 ||
        (anchor.target && anchor.target !== '_self')) return;
    e.preventDefault();
    var mode = (isTopLevel(window.location.pathname) && isTopLevel(anchor.pathname)) ? 'soft' : 'full';
    PT.navigate(mode, href);
  });
})();
