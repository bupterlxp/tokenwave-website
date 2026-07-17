/* Page transition state machine (main-page soft swaps + full-page fades) */
(function () {
  var mainEl = document.querySelector('main');
  var MAIN_PAGES = ['/', '/index.html', '/blog.html', '/benchmarks.html', '/joinus.html'];
  function normalize(p) {
    // Treat the site root and index.html as the same page
    var base = p.split('/').pop();
    return base === '' ? '/' : '/' + base;
  }
  function isMainPage(p) { return MAIN_PAGES.indexOf(normalize(p)) !== -1; }

  var _fallback = null;
  var _type = null;
  try { _type = sessionStorage.getItem('tokenwave_transition'); sessionStorage.removeItem('tokenwave_transition'); } catch (e) {}

  var PT = window.PageTransition = {
    state: 'idle',

    init: function () {
      if (_type === 'full') {
        PT.state = 'fading-in';
        if (mainEl) { mainEl.style.transition = 'none'; mainEl.style.opacity = '1'; }
        _fallback = setTimeout(function () { PT._reveal(); }, 1500);
      } else if (_type === 'main' && isMainPage(window.location.pathname)) {
        PT.state = 'fading-in';
        _fallback = setTimeout(function () { PT._reveal(); }, 1500);
      } else {
        if (mainEl) { mainEl.style.transition = 'none'; mainEl.style.opacity = '1'; mainEl.classList.add('cards-ready'); }
      }
    },

    onParticlesReady: function () {
      if (PT.state !== 'fading-in') return;
      PT._reveal();
    },

    _reveal: function () {
      if (PT.state !== 'fading-in') return;
      if (_fallback) { clearTimeout(_fallback); _fallback = null; }

      if (_type === 'full') {
        var html = document.documentElement;
        html.style.transition = 'opacity 0.4s ease';
        setTimeout(function () {
          html.style.opacity = '1';
          setTimeout(function () {
            if (mainEl) mainEl.classList.add('cards-ready');
            PT.state = 'idle';
          }, 420);
        }, 150);
      } else {
        setTimeout(function () {
          if (mainEl) mainEl.classList.add('page-visible');
          setTimeout(function () {
            if (mainEl) mainEl.classList.add('cards-ready');
            PT.state = 'idle';
          }, 380);
        }, 200);
      }
    },

    _swapContent: function (html, path) {
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var newMain = doc.querySelector('main');
      var newTitle = doc.querySelector('title');
      if (newMain) mainEl.innerHTML = newMain.innerHTML;
      if (newTitle) document.title = newTitle.textContent;
      document.querySelectorAll('nav a').forEach(function (a) {
        if (normalize(a.pathname) === normalize(path)) a.classList.add('active');
        else a.classList.remove('active');
      });
      // Re-init inline scripts (e.g. typewriter on landing page)
      mainEl.querySelectorAll('script').forEach(function (old) {
        var s = document.createElement('script');
        s.textContent = old.textContent;
        old.parentNode.replaceChild(s, old);
      });
    },

    navigate: function (type, href) {
      if (PT.state === 'fading-out') return;
      PT.state = 'fading-out';

      if (type === 'full') {
        try { sessionStorage.setItem('tokenwave_transition', type); } catch (e) {}
        if (typeof window.freezeParticles === 'function') window.freezeParticles();
        document.body.style.transition = 'opacity 0.4s ease';
        document.body.style.opacity = '0';
        setTimeout(function () { window.location.href = href; }, 420);
      } else {
        mainEl.classList.remove('cards-ready');
        mainEl.classList.remove('page-visible');
        setTimeout(function () {
          fetch(href).then(function (r) { return r.text(); }).then(function (html) {
            PT._swapContent(html, href);
            history.pushState({ path: href }, '', href);
            mainEl.classList.add('page-visible');
            setTimeout(function () { mainEl.classList.add('cards-ready'); PT.state = 'idle'; }, 380);
          }).catch(function () { window.location.href = href; });
        }, 350);
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { PT.init(); });
  } else {
    PT.init();
  }

  window.addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    document.body.style.opacity = '1';
    document.body.style.transition = '';
    document.documentElement.style.opacity = '1';
    document.documentElement.style.transition = '';
    if (mainEl) { mainEl.style.opacity = '1'; mainEl.classList.add('page-visible'); mainEl.classList.add('cards-ready'); }
    if (typeof window.resumeParticles === 'function') window.resumeParticles();
    PT.state = 'idle';
    _type = null;
  });

  window.addEventListener('popstate', function () {
    var path = window.location.pathname;
    if (!isMainPage(path)) { window.location.reload(); return; }
    mainEl.classList.remove('cards-ready');
    mainEl.classList.remove('page-visible');
    fetch(path).then(function (r) { return r.text(); }).then(function (html) {
      PT._swapContent(html, path);
      mainEl.classList.add('page-visible');
      setTimeout(function () { mainEl.classList.add('cards-ready'); }, 380);
    }).catch(function () { window.location.reload(); });
  });

  document.addEventListener('click', function (e) {
    var anchor = e.target.closest('a');
    if (!anchor) return;
    var href = anchor.getAttribute('href');
    if (!href) return;
    if ((anchor.hostname && anchor.hostname !== window.location.hostname) || href.charAt(0) === '#' || href.indexOf('mailto:') === 0 || (anchor.target && anchor.target !== '_self')) return;
    e.preventDefault();
    var type = (isMainPage(window.location.pathname) && isMainPage(anchor.pathname)) ? 'main' : 'full';
    PT.navigate(type, href);
  });
})();
