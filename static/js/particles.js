/* TokenWave — background wave field.
   A single continuous particle surface: rows of tokens flowing as
   layered waves in perspective, lit by the brand current (blue→violet).
   No shape-morphing, no gimmicks — one calm signature in motion.

   Public API (used by transition.js):
     window.freezeParticles()  — stop loop, pin a snapshot before full nav
     window.resumeParticles()  — undo freeze (bfcache restore)
     PageTransition.onParticlesReady() is called after the first frame. */
(function () {
  'use strict';

  var BG = '#0A0D13';

  /* ── 1. Canvas under everything ─────────────────────────── */
  var canvas = document.createElement('canvas');
  Object.assign(canvas.style, {
    position: 'fixed',
    top: '0',
    left: '0',
    width: '100%',
    height: '100%',
    zIndex: '0',
    pointerEvents: 'none',
    opacity: '0',
  });
  document.body.insertBefore(canvas, document.body.firstChild);

  /* Snapshot restore: show last frame of previous page immediately */
  try {
    var _snap = sessionStorage.getItem('tokenwave_bg_snapshot');
    if (_snap) {
      var _snapImg = document.createElement('img');
      Object.assign(_snapImg.style, {
        position: 'fixed', top: '0', left: '0', width: '100%', height: '100%',
        zIndex: '0', pointerEvents: 'none', objectFit: 'cover',
        opacity: '1', transition: 'opacity 0.5s ease',
      });
      _snapImg.src = _snap;
      document.body.insertBefore(_snapImg, canvas.nextSibling);
      sessionStorage.removeItem('tokenwave_bg_snapshot');
      window._particleSnapshot = _snapImg;
    }
  } catch (e) {}

  /* Lift content above the canvas. The header is NOT touched: it is
     sticky with z-index 10 in the stylesheet, and an inline z-index:1
     here would flatten it under <main> — killing the nav dropdown. */
  ['main', 'footer'].forEach(function (sel) {
    var el = document.querySelector(sel);
    if (el) {
      el.style.position = 'relative';
      if (!el.style.zIndex) el.style.zIndex = '1';
    }
  });

  var REDUCED = false;
  try {
    REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) {}

  /* ── 2. Scene ───────────────────────────────────────────── */
  function boot() {
    var W = window.innerWidth;
    var H = window.innerHeight;

    var scene  = new THREE.Scene();
    scene.fog  = new THREE.FogExp2(0x0A0D13, 0.0052);

    var camera = new THREE.PerspectiveCamera(58, W / H, 0.1, 600);
    camera.position.set(0, 22, 92);

    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: canvas, alpha: true, antialias: false, preserveDrawingBuffer: true,
      });
    } catch (e) {
      /* No WebGL: the page stands on its own — just reveal it. */
      if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      if (window.PageTransition) window.PageTransition.onParticlesReady();
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);

    /* The surface: COLS × ROWS tokens on an x/z plane, y = wave height.
       Rows recede into depth; color and size fall off with distance. */
    var COLS = 160, ROWS = 64;
    var N = COLS * ROWS;
    var SPAN_X = 340;         /* world width of the sheet */
    var SPAN_Z = 260;         /* world depth */

    var pos = new Float32Array(N * 3);
    var col = new Float32Array(N * 3);
    var gx  = new Float32Array(N);   /* grid x in [-0.5, 0.5] */
    var gz  = new Float32Array(N);   /* grid z in [0, 1], 0 = near row */

    /* Brand current sampled along depth: near = blue, far = violet.
       Only decorative — the field never encodes data. */
    function lerp(a, b, t) { return a + (b - a) * t; }
    var NEAR = [0.55, 0.75, 1.0];      /* bright sky */
    var MID  = [0.545, 0.361, 0.965];  /* #8B5CF6 */
    var FAR  = [0.290, 0.270, 0.500];  /* dim violet-slate */

    var i3, i, cX, cZ, t, c0, c1, m;
    for (var r = 0; r < ROWS; r++) {
      for (var q = 0; q < COLS; q++) {
        i  = r * COLS + q;
        i3 = i * 3;
        cX = q / (COLS - 1) - 0.5;
        cZ = r / (ROWS - 1);
        gx[i] = cX;
        gz[i] = cZ;

        pos[i3]     = cX * SPAN_X;
        pos[i3 + 1] = 0;
        pos[i3 + 2] = -cZ * SPAN_Z - 26;

        /* piecewise blue→violet→dim, with mild per-token variance */
        if (cZ < 0.45) { t = cZ / 0.45;       c0 = NEAR; c1 = MID; }
        else           { t = (cZ - 0.45) / 0.55; c0 = MID;  c1 = FAR; }
        m = 0.92 + Math.random() * 0.16;
        col[i3]     = lerp(c0[0], c1[0], t) * m;
        col[i3 + 1] = lerp(c0[1], c1[1], t) * m;
        col[i3 + 2] = lerp(c0[2], c1[2], t) * m;
      }
    }

    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3));

    /* Soft round glow sprite — square points read as noise */
    var spriteCanvas = document.createElement('canvas');
    spriteCanvas.width = spriteCanvas.height = 64;
    var sctx = spriteCanvas.getContext('2d');
    var grad = sctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, 'rgba(255,255,255,1)');
    grad.addColorStop(0.28, 'rgba(255,255,255,0.9)');
    grad.addColorStop(0.55, 'rgba(255,255,255,0.28)');
    grad.addColorStop(1, 'rgba(255,255,255,0)');
    sctx.fillStyle = grad;
    sctx.fillRect(0, 0, 64, 64);
    var sprite = new THREE.CanvasTexture(spriteCanvas);

    var mat = new THREE.PointsMaterial({
      size: 2.1,
      map: sprite,
      vertexColors: true,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.62,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    var points = new THREE.Points(geo, mat);
    points.position.y = -26;      /* keep the sheet below the type */
    scene.add(points);

    /* ── 3. Wave program ───────────────────────────────────── */
    /* Three travelling components — a long swell, a cross chop, and a
       slow breathing term. Tuned to read as one coherent body of water. */
    function heightAt(x, z, tm) {
      return (
        Math.sin(x * 3.1 + tm * 0.42 + z * 1.6) * 5.2 * (0.55 + z * 0.8) +
        Math.sin(x * 8.3 - tm * 0.31 + z * 4.1) * 1.7 +
        Math.sin(z * 5.2 + tm * 0.23) * 3.4 +
        Math.cos(x * 1.3 - tm * 0.19) * 2.2
      );
    }

    var time = Math.random() * 100;   /* start mid-flow, never at zero-phase */

    var RIP_R2 = 34 * 34;   /* ripple radius² in world units */
    function step(dt) {
      time += dt;
      /* ease the ripple center so it glides, never jumps */
      rippleX += (rippleTX - rippleX) * Math.min(1, dt * 6);
      rippleZ += (rippleTZ - rippleZ) * Math.min(1, dt * 6);
      var breathe = 0.65 + 0.35 * Math.sin(time * 2.1);
      for (var i = 0; i < N; i++) {
        var h = heightAt(gx[i] * 6.4, gz[i] * 6.4, time);
        var dx = gx[i] * SPAN_X - rippleX;
        var dz = (-gz[i] * SPAN_Z - 26) - rippleZ;
        var r2 = dx * dx + dz * dz;
        if (r2 < RIP_R2 * 4) {
          h += Math.exp(-r2 / RIP_R2) * 8.5 * breathe;
        }
        pos[i * 3 + 1] = h;
      }
      geo.attributes.position.needsUpdate = true;
    }

    /* ── 4. Pointer parallax + surface ripple ──────────────── */
    var mx = 0, my = 0;
    var _ray = new THREE.Raycaster();
    var _ndc = new THREE.Vector2();
    var _plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 26); /* y = -26 */
    var _hit = new THREE.Vector3();
    var rippleX = 9999, rippleZ = 9999;      /* eased toward target */
    var rippleTX = 9999, rippleTZ = 9999;    /* raycast target */
    window.addEventListener('mousemove', function (e) {
      mx = (e.clientX / window.innerWidth - 0.5) * 2;
      my = (e.clientY / window.innerHeight - 0.5) * 2;
      _ndc.set(mx, -my);
      _ray.setFromCamera(_ndc, camera);
      if (_ray.ray.intersectPlane(_plane, _hit)) {
        rippleTX = _hit.x;
        rippleTZ = _hit.z;
      }
    });

    /* ── 5. Scroll fade ────────────────────────────────────── */
    /* Landing page carries the full signature; content pages keep a
       quiet ambience that never competes with reading. */
    var IS_HOME = !!document.querySelector('.hero');
    var BASE_OPACITY = IS_HOME ? 0.8 : 0.3;
    mat.opacity = BASE_OPACITY;
    window.addEventListener('scroll', function () {
      var sy = window.scrollY;
      var frac = Math.max(0, Math.min(1, (sy - 120) / 380));
      mat.opacity = BASE_OPACITY * (1 - frac * 0.94);
    });

    /* ── 6. Freeze / resume (page transitions) ─────────────── */
    var _snapW = Math.round(W * 0.3), _snapH = Math.round(H * 0.3);
    var _snapCanvas = document.createElement('canvas');
    _snapCanvas.width = _snapW; _snapCanvas.height = _snapH;
    var _snapCtx = _snapCanvas.getContext('2d');

    var _frozen = false;
    var _freezePin = null;

    window.freezeParticles = function () {
      if (_frozen) return;
      _frozen = true;
      try {
        _snapCtx.fillStyle = BG;
        _snapCtx.fillRect(0, 0, _snapW, _snapH);
        _snapCtx.drawImage(canvas, 0, 0, _snapW, _snapH);
        var snapshot = _snapCanvas.toDataURL('image/jpeg', 0.8);
        sessionStorage.setItem('tokenwave_bg_snapshot', snapshot);
        var pin = document.createElement('img');
        Object.assign(pin.style, {
          position: 'fixed', top: '0', left: '0', width: '100%', height: '100%',
          zIndex: '0', pointerEvents: 'none', objectFit: 'cover',
        });
        pin.src = snapshot;
        document.body.insertBefore(pin, canvas.nextSibling);
        _freezePin = pin;
      } catch (e) {}
    };

    window.resumeParticles = function () {
      if (_freezePin && _freezePin.parentNode) {
        _freezePin.parentNode.removeChild(_freezePin);
        _freezePin = null;
      }
      canvas.style.transition = 'opacity 0.4s ease';
      canvas.style.opacity = '1';
      if (_frozen) { _frozen = false; if (!REDUCED) animate(); }
    };

    /* ── 7. Loop ───────────────────────────────────────────── */
    var clock = new THREE.Clock();
    var _canvasFadedIn = false;
    var _snapDismissed = false;

    function dismissSnapshot() {
      if (_snapDismissed || !window._particleSnapshot) return;
      _snapDismissed = true;
      var snap = window._particleSnapshot;
      window._particleSnapshot = null;
      snap.style.opacity = '0';
      setTimeout(function () {
        if (snap.parentNode) snap.parentNode.removeChild(snap);
      }, 550);
    }

    function frame() {
      camera.position.x += (mx * 7 - camera.position.x) * 0.04;
      camera.position.y += (22 - my * 4 - camera.position.y) * 0.04;
      camera.lookAt(0, 2, -80);
      renderer.render(scene, camera);
      dismissSnapshot();
      if (!_canvasFadedIn) {
        _canvasFadedIn = true;
        canvas.style.transition = 'opacity 0.9s ease';
        canvas.style.opacity = '1';
        if (window.PageTransition) window.PageTransition.onParticlesReady();
      }
    }

    function animate() {
      if (_frozen) return;
      requestAnimationFrame(animate);
      var dt = Math.min(clock.getDelta(), 0.05);
      step(dt);
      frame();
    }

    if (REDUCED) {
      /* Render one still frame — the composition without the motion. */
      step(0);
      frame();
    } else {
      animate();
    }

    /* ── 8. Resize ─────────────────────────────────────────── */
    window.addEventListener('resize', function () {
      var w = window.innerWidth, h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      _snapW = Math.round(w * 0.3);
      _snapH = Math.round(h * 0.3);
      _snapCanvas.width = _snapW;
      _snapCanvas.height = _snapH;
      if (REDUCED) frame();
    });
  }

  boot();
})();
