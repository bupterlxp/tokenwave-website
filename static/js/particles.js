(function () {
  'use strict';

  /* ─────────────────────────────────────────────────────────────
     1.  Create the background canvas and ensure content is above it
  ───────────────────────────────────────────────────────────── */
  var canvas = document.createElement('canvas');
  Object.assign(canvas.style, {
    position: 'fixed',
    top: '0',
    left: '0',
    width: '100%',
    height: '100%',
    zIndex: '0',
    pointerEvents: 'none',
    opacity: '0',          // start hidden; faded in after first render frame
  });
  document.body.insertBefore(canvas, document.body.firstChild);

  /* ── Snapshot restore: show last frame of previous page immediately ── */
  try {
    var _snap = sessionStorage.getItem('tokenwave_bg_snapshot');
    if (_snap) {
      var _snapImg = document.createElement('img');
      Object.assign(_snapImg.style, {
        position:       'fixed',
        top:            '0',
        left:           '0',
        width:          '100%',
        height:         '100%',
        zIndex:         '0',
        pointerEvents:  'none',
        objectFit:      'cover',
        opacity:        '1',
        transition:     'opacity 0.5s ease',
      });
      _snapImg.src = _snap;
      document.body.insertBefore(_snapImg, canvas.nextSibling);
      sessionStorage.removeItem('tokenwave_bg_snapshot');
      window._particleSnapshot = _snapImg;
    }
  } catch (e) {}

  // Lift interactive layers above the canvas
  ['header', 'main', 'footer'].forEach(function (sel) {
    var el = document.querySelector(sel);
    if (el) {
      el.style.position = 'relative';
      if (!el.style.zIndex) el.style.zIndex = '1';
    }
  });

  /* ─────────────────────────────────────────────────────────────
     2.  Boot – Three.js is loaded as a separate script before this file
  ───────────────────────────────────────────────────────────── */
  function boot() {
    var W = window.innerWidth;
    var H = window.innerHeight;

    /* ── Scene / Camera / Renderer ── */
    var scene    = new THREE.Scene();
    var camera   = new THREE.PerspectiveCamera(55, W / H, 0.1, 1000);
    camera.position.z = 130;

    var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);

    /* ── Particle buffers ── */
    var N   = 4000;               // particle count
    var pos  = new Float32Array(N * 3);  // rendered positions (base + repulsion)
    var base = new Float32Array(N * 3);  // pure shape/float positions (no repulsion)
    var src  = new Float32Array(N * 3);  // lerp start (snapped from base, never from pos)
    var dst  = new Float32Array(N * 3);  // lerp target
    var del  = new Float32Array(N);      // per-particle delay offset [0, MAX_DEL]
    var col  = new Float32Array(N * 3);  // RGB colours
    var MAX_DEL = 0.38;                  // max stagger window (fraction of TRANS_DUR)

    // Per-particle repulsion displacement and velocity (additive on top of base)
    var repX  = new Float32Array(N);
    var repY  = new Float32Array(N);
    var repVX = new Float32Array(N);
    var repVY = new Float32Array(N);

    // Colour palette – grayscale (luminance-matched)
    var PALETTE = [
      [0.80, 0.80, 0.80],
      [0.63, 0.63, 0.63],
      [0.73, 0.73, 0.73],
      [0.67, 0.67, 0.67],
      [0.57, 0.57, 0.57],
      [0.71, 0.71, 0.71],
    ];

    // Initialise positions and per-particle properties
    for (var i = 0; i < N; i++) {
      var x = (Math.random() - 0.5) * 300;
      var y = (Math.random() - 0.5) * 200;
      var z = (Math.random() - 0.5) * 100;
      pos[i*3]=x;  pos[i*3+1]=y;  pos[i*3+2]=z;
      base[i*3]=x; base[i*3+1]=y; base[i*3+2]=z;
      dst[i*3]=x;  dst[i*3+1]=y;  dst[i*3+2]=z;

      // Random stagger: particle starts moving at del[i] fraction into the transition
      del[i] = Math.random() * MAX_DEL;

      var c = PALETTE[Math.floor(Math.random() * PALETTE.length)];
      col[i*3]=c[0]; col[i*3+1]=c[1]; col[i*3+2]=c[2];
    }

    /* ─────────────────────────────────────────────────────────
       3b. Serialisation helpers (Float32Array ⇔ Base64)
    ───────────────────────────────────────────────────── */
    function f32ToB64(arr) {
      var bytes = new Uint8Array(arr.buffer, arr.byteOffset, arr.byteLength);
      var bin = '';
      for (var k = 0; k < bytes.byteLength; k++) bin += String.fromCharCode(bytes[k]);
      return btoa(bin);
    }
    function b64ToF32(str, len) {
      var bin  = atob(str);
      var out  = new Float32Array(len);
      var view = new Uint8Array(out.buffer);
      for (var k = 0; k < bin.length; k++) view[k] = bin.charCodeAt(k);
      return out;
    }

    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(col, 3));

    var mat = new THREE.PointsMaterial({
      size: 1.4,
      vertexColors: true,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.70,
    });

    var points = new THREE.Points(geo, mat);
    scene.add(points);

    /* ─────────────────────────────────────────────────────────
       4.  Shape samplers
    ───────────────────────────────────────────────────────── */

    /**
     * Render text on an offscreen canvas and return pixel coords
     * as [ [x, y], … ] normalised to roughly [-110..110, -40..40]
     */
    function sampleText(text, fontSize) {
      var ow = 640, oh = 240;
      var oc  = document.createElement('canvas');
      oc.width = ow; oc.height = oh;
      var ctx = oc.getContext('2d');
      ctx.clearRect(0, 0, ow, oh);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold ' + fontSize + 'px "Space Mono", monospace';
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, ow / 2, oh / 2);

      var data = ctx.getImageData(0, 0, ow, oh).data;
      var out  = [];
      var step = 4;
      for (var py = 0; py < oh; py += step) {
        for (var px = 0; px < ow; px += step) {
          if (data[((py * ow + px) * 4) + 3] > 128) {
            out.push([
              (px / ow - 0.5) * 240,
              -(py / oh - 0.5) * 85,
            ]);
          }
        }
      }
      return out;
    }

    /**
     * Draw an image aspect-fit on an offscreen canvas and return
     * dark pixel coords (the TokenWave logo is a wide wordmark on a
     * white background, so we keep its aspect ratio and pick
     * non-white pixels).
     */
    function sampleImage(img) {
      var ow = 384, oh = 384;
      var oc  = document.createElement('canvas');
      oc.width = ow; oc.height = oh;
      var ctx = oc.getContext('2d');
      ctx.clearRect(0, 0, ow, oh);

      var scale = Math.min(ow / img.width, oh / img.height);
      var dw = img.width * scale, dh = img.height * scale;
      var dx = (ow - dw) / 2,     dy = (oh - dh) / 2;
      ctx.drawImage(img, dx, dy, dw, dh);

      var data = ctx.getImageData(0, 0, ow, oh).data;
      var darkPts  = [];
      var alphaPts = [];
      var step     = 3;
      for (var py = 0; py < oh; py += step) {
        for (var px = 0; px < ow; px += step) {
          var idx = (py * ow + px) * 4;
          var r = data[idx], g = data[idx+1], b = data[idx+2], a = data[idx+3];
          var coord = [(px/ow - 0.5) * 200, -(py/oh - 0.5) * 200];
          if (a > 100) {
            alphaPts.push(coord);
            if ((r + g + b) / 3 < 200) darkPts.push(coord);
          }
        }
      }
      // Prefer dark pixels (wordmark + wave on white); fall back to all opaque
      return darkPts.length > alphaPts.length * 0.08 ? darkPts : alphaPts;
    }

    /* ─────────────────────────────────────────────────────────
       5.  Distribute a point list across all N particles → dst[]
    ───────────────────────────────────────────────────────── */
    function pointsToDst(pts) {
      if (!pts || pts.length === 0) {
        // Scatter state
        for (var i = 0; i < N; i++) {
          dst[i*3]   = (Math.random() - 0.5) * 300;
          dst[i*3+1] = (Math.random() - 0.5) * 200;
          dst[i*3+2] = (Math.random() - 0.5) * 100;
        }
        return;
      }
      // Shuffle the point list for variety
      var shuffled = pts.slice().sort(function () { return Math.random() - 0.5; });
      for (var i = 0; i < N; i++) {
        var p = shuffled[i % shuffled.length];
        dst[i*3]   = p[0] + (Math.random() - 0.5) * 2.0;
        dst[i*3+1] = p[1] + (Math.random() - 0.5) * 2.0;
        dst[i*3+2] = (Math.random() - 0.5) * 10;
      }
    }

    /* ─────────────────────────────────────────────────────────
       6.  State machine
           State indices:   0=scatter  1=TokenWave  2=scatter
                            3=logo     4=scatter    5=AI
           Repeating every 6 states.
    ───────────────────────────────────────────────────────── */
    var stateSeq   = getStateSeq();
    var HOLD_TIMES = getHoldTimes();
    var TRANS_DUR  = 3.2;  // transition duration in seconds

    function isMobile() {
      return window.innerWidth < 600 || /Mobi|Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
    }
    function getStateSeq() {
      // 0:scatter, 1:TokenWave, 2:scatter, 3:logo, 4:scatter, 5:AI (desktop)
      // 0:scatter, 1:logo,      2:scatter, 3:AI   (mobile)
      return isMobile() ? [0,3,0,5] : [0,1,0,3,0,5];
    }
    function getHoldTimes() {
      return isMobile() ? [3.5, 8.0, 3.0, 8.0] : [3.5, 8.0, 3.0, 8.0, 3.0, 8.0];
    }

    var stateIdx     = 0;
    var stateTimer   = 0.0;
    var transitioning= false;
    var lerpT        = 0.0;
    var floatBlend   = 1.0;  // 0→1 fade-in of idle float after transition ends
    var FLOAT_FADE_DUR = 0.6; // seconds to blend float back in
    var time         = 0;    // continuous clock used for idle float phase

    /* ─────────────────────────────────────────────────────────
       6b. Restore particle state from previous page (if saved)
    ───────────────────────────────────────────────────── */
    try {
      var _raw = sessionStorage.getItem('tokenwave_px');
      if (_raw) {
        var _s = JSON.parse(_raw);
        var seq = getStateSeq();
        if (_s.N === N && _s.si < seq.length) {
          stateIdx      = _s.si  || 0;
          stateTimer    = _s.st  || 0;
          transitioning = _s.tr  || false;
          lerpT         = _s.lt  || 0;
          floatBlend    = (_s.fb != null) ? _s.fb : 1.0;
          time          = _s.t   || 0;
          base.set(b64ToF32(_s.base,  N * 3));
          pos.set(base);
          dst.set(b64ToF32(_s.dst,   N * 3));
          del.set(b64ToF32(_s.del,   N));
          repX.set(b64ToF32(_s.repX, N));
          repY.set(b64ToF32(_s.repY, N));
          repVX.set(b64ToF32(_s.repVX, N));
          repVY.set(b64ToF32(_s.repVY, N));
          if (transitioning && _s.src) src.set(b64ToF32(_s.src, N * 3));
        }
        sessionStorage.removeItem('tokenwave_px');  // consume once, never re-apply
      }
    } catch (e) { /* sessionStorage unavailable or data corrupted – start fresh */ }

    // Cached shape point arrays (loaded async)
    var wordmarkPts = null;
    var logoPts     = null;
    var aiPts       = null;

    // Sample text shapes once fonts are ready
    document.fonts.ready.then(function () {
      wordmarkPts = sampleText('TokenWave', 100);
      aiPts       = sampleText('AI',        160);
    });

    // Load the company logo (path works from both root and subfolder pages)
    var logoImg       = new Image();
    logoImg.crossOrigin = 'anonymous';
    logoImg.src       = (window.location.pathname.indexOf('/benchmarks/') !== -1 ? '../' : '') + 'static/images/logo.jpg';
    logoImg.onload    = function () {
      logoPts = sampleImage(logoImg);
    };

    function shapeForState(s) {
      var code = stateSeq[s % stateSeq.length];
      switch (code) {
        case 1: return wordmarkPts;
        case 3: return logoPts;
        case 5: return aiPts;
        default: return null;   // scatter
      }
    }

    function beginTransition() {
      stateIdx = (stateIdx + 1) % stateSeq.length;
      // Snapshot pure shape positions – NOT pos, which contains repulsion baked in
      src.set(base);
      pointsToDst(shapeForState(stateIdx));
      lerpT        = 0.0;
      transitioning= true;
      stateTimer   = 0.0;
    }

    // Track device category changes; handled inside the single resize listener below
    var lastMobile = isMobile();

    /* ─────────────────────────────────────────────────────────
       7.  Mouse interaction (parallax + repulsion)
    ───────────────────────────────────────────────────── */
    var mouseNX = 0, mouseNY = 0;      // normalised [-1,+1] for camera parallax
    var mouseRawX = 0, mouseRawY = 0;  // raw client pixels for raycaster

    var _ray      = new THREE.Raycaster();
    var _plane    = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
    var _mWorld   = new THREE.Vector3();
    var _ndcMouse = new THREE.Vector2();

    window.addEventListener('mousemove', function (e) {
      mouseNX   = (e.clientX / window.innerWidth  - 0.5) * 2;
      mouseNY   = (e.clientY / window.innerHeight - 0.5) * 2;
      mouseRawX = e.clientX;
      mouseRawY = e.clientY;
    });

    // Repulsion constants
    var REP_RADIUS = 55;   // hover radius (world units)
    var REP_FORCE  = 90;   // max push acceleration (world units / s²)
    var SPRING_K   = 10;   // spring stiffness pulling rep back to 0
    var DAMP_C     = 8;    // linear damping coefficient

    /* ─────────────────────────────────────────────────────────
       8.  Scroll fade
    ───────────────────────────────────────────────────────── */
    var BASE_OPACITY = 0.70;
    window.addEventListener('scroll', function () {
      var sy     = window.scrollY;
      var fadeSt = 150, fadeEn = 500;
      var frac   = Math.max(0, Math.min(1, (sy - fadeSt) / (fadeEn - fadeSt)));
      mat.opacity = BASE_OPACITY * (1 - frac * 0.8);
    });

    // Off-screen canvas for snapshot capture (used only in freezeParticles, not every frame)
    var _snapW   = Math.round(window.innerWidth  * 0.3);
    var _snapH   = Math.round(window.innerHeight * 0.3);
    var _snapCanvas = document.createElement('canvas');
    _snapCanvas.width  = _snapW;
    _snapCanvas.height = _snapH;
    var _snapCtx = _snapCanvas.getContext('2d');

    window.addEventListener('beforeunload', function () {
      try {
        var payload = {
          N:    N,
          si:   stateIdx,
          st:   stateTimer,
          tr:   transitioning,
          lt:   lerpT,
          fb:   floatBlend,
          t:    time,
          base: f32ToB64(base),
          dst:  f32ToB64(dst),
          del:  f32ToB64(del),
          repX: f32ToB64(repX),
          repY: f32ToB64(repY),
          repVX:f32ToB64(repVX),
          repVY:f32ToB64(repVY),
        };
        if (transitioning) payload.src = f32ToB64(src);
        sessionStorage.setItem('tokenwave_px', JSON.stringify(payload));
      } catch (e) {}
    });

    /* ─────────────────────────────────────────────────────────
       9.  Animation loop
    ───────────────────────────────────────────────────────── */
    var clock = new THREE.Clock();

    // Quintic ease-in-out – much smoother than quadratic, near-zero velocity at both ends
    function easeQuintic(t) {
      return t < 0.5 ? 16*t*t*t*t*t : 1 - Math.pow(-2*t + 2, 5) / 2;
    }

    // Fade out the snapshot overlay after the first rendered frame
    var _snapDismissed  = false;
    var _canvasFadedIn  = false;  // canvas starts at opacity:0; faded in after first frame
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

    var _frozen = false;
    var _freezePin = null;

    // Stop animation, capture snapshot, pin static overlay (called before full-page nav)
    window.freezeParticles = function () {
      if (_frozen) return;
      _frozen = true;
      try {
        _snapCtx.fillStyle = '#ffffff';
        _snapCtx.fillRect(0, 0, _snapW, _snapH);
        _snapCtx.drawImage(canvas, 0, 0, _snapW, _snapH);
        var snapshot = _snapCanvas.toDataURL('image/jpeg', 0.80);
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

    // Restore particles (bfcache recovery or re-entering page)
    window.resumeParticles = function () {
      if (_freezePin && _freezePin.parentNode) {
        _freezePin.parentNode.removeChild(_freezePin);
        _freezePin = null;
      }
      canvas.style.transition = 'opacity 0.4s ease';
      canvas.style.opacity = '1';
      if (_frozen) { _frozen = false; animate(); }
    };

    function animate() {
      if (_frozen) return;  // stop loop when navigating away
      requestAnimationFrame(animate);
      var dt = Math.min(clock.getDelta(), 0.05);
      time       += dt;
      stateTimer += dt;

      var holdDur = HOLD_TIMES[stateIdx % stateSeq.length];

      // Trigger next transition when hold time expires
      if (!transitioning && stateTimer > holdDur) {
        beginTransition();
      }

      if (transitioning) {
        lerpT += dt / TRANS_DUR;
        var done = lerpT >= 1.0;
        if (done) {
          lerpT = 1.0;
          transitioning = false;
          // Reset float blend so idle float fades in from 0, preventing a jump
          floatBlend = 0.0;
        }

        for (var i = 0; i < N; i++) {
          var range  = 1.0 - del[i];
          var localT = Math.max(0, Math.min(1, (lerpT - del[i]) / range));
          var e      = easeQuintic(localT);
          // Write pure lerp into base (no repulsion here)
          base[i*3]   = src[i*3]   + (dst[i*3]   - src[i*3])   * e;
          base[i*3+1] = src[i*3+1] + (dst[i*3+1] - src[i*3+1]) * e;
          base[i*3+2] = src[i*3+2] + (dst[i*3+2] - src[i*3+2]) * e;
        }

      } else {
        // Fade float amplitude in from 0 after a transition ends
        floatBlend = Math.min(1.0, floatBlend + dt / FLOAT_FADE_DUR);

        var isScatter = (stateIdx % 2 === 0);
        for (var i = 0; i < N; i++) {
          var phase = i * 0.05;
          if (isScatter) {
            base[i*3]   = dst[i*3]   + Math.sin(time * 0.18 + phase)       * 1.8 * floatBlend;
            base[i*3+1] = dst[i*3+1] + Math.cos(time * 0.14 + phase * 1.3) * 1.8 * floatBlend;
            base[i*3+2] = dst[i*3+2] + Math.sin(time * 0.30 + phase * 0.7) * 8.0 * floatBlend;
          } else {
            base[i*3]   = dst[i*3]   + Math.sin(time * 0.50 + phase) * 0.30 * floatBlend;
            base[i*3+1] = dst[i*3+1] + Math.cos(time * 0.40 + phase) * 0.30 * floatBlend;
            base[i*3+2] = dst[i*3+2] + Math.sin(time * 0.60 + phase) * 1.2  * floatBlend;
          }
        }
      }

      /* ── Repulsion physics (operates on base positions, writes into pos) ─────── */
      _ndcMouse.set(
        (mouseRawX / window.innerWidth)  * 2 - 1,
       -(mouseRawY / window.innerHeight) * 2 + 1
      );
      _ray.setFromCamera(_ndcMouse, camera);
      _ray.ray.intersectPlane(_plane, _mWorld);
      var mwx = _mWorld.x, mwy = _mWorld.y;

      for (var i = 0; i < N; i++) {
        // Distance is measured from base position (pure shape, no repulsion feedback loop)
        var bx = base[i*3], by = base[i*3+1];
        var dx = bx - mwx, dy = by - mwy;
        var d2 = dx*dx + dy*dy;
        if (d2 < REP_RADIUS * REP_RADIUS && d2 > 0.001) {
          var d    = Math.sqrt(d2);
          var fall = 1.0 - d / REP_RADIUS;   // 1 at cursor, 0 at edge
          repVX[i] += (dx / d) * fall * fall * REP_FORCE * dt;
          repVY[i] += (dy / d) * fall * fall * REP_FORCE * dt;
        }

        // Spring-damper: pulls repulsion displacement back to (0,0)
        repVX[i] += (-SPRING_K * repX[i] - DAMP_C * repVX[i]) * dt;
        repVY[i] += (-SPRING_K * repY[i] - DAMP_C * repVY[i]) * dt;
        repX[i]  += repVX[i] * dt;
        repY[i]  += repVY[i] * dt;

        // Final rendered position = pure base + repulsion (additive, never baked into base)
        pos[i*3]   = base[i*3]   + repX[i];
        pos[i*3+1] = base[i*3+1] + repY[i];
        pos[i*3+2] = base[i*3+2];
      }

      geo.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
      dismissSnapshot();  // remove snapshot overlay after first real frame

      // Fade canvas in on the very first rendered frame
      if (!_canvasFadedIn) {
        _canvasFadedIn = true;
        canvas.style.transition = 'opacity 0.6s ease';
        canvas.style.opacity    = '1';
        if (window.PageTransition) window.PageTransition.onParticlesReady();
      }

      camera.position.x += (mouseNX *  8 - camera.position.x) * 0.04;
      camera.position.y += (-mouseNY * 5 - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);
    }

    animate();

    /* ─────────────────────────────────────────────────────────
       10.  Resize handler
    ───────────────────────────────────────────────────────── */
    window.addEventListener('resize', function () {
      // Update state machine when crossing desktop/mobile breakpoint
      var nowMobile = isMobile();
      if (nowMobile !== lastMobile) {
        stateIdx = 0;
        stateSeq = getStateSeq();
        HOLD_TIMES = getHoldTimes();
        beginTransition();
      } else {
        HOLD_TIMES = getHoldTimes();
      }
      lastMobile = nowMobile;

      var W = window.innerWidth, H = window.innerHeight;
      camera.aspect = W / H;
      camera.updateProjectionMatrix();
      renderer.setSize(W, H);
      // Keep snapshot canvas in sync with viewport
      _snapW = Math.round(W * 0.3);
      _snapH = Math.round(H * 0.3);
      _snapCanvas.width  = _snapW;
      _snapCanvas.height = _snapH;
    });

  } // end boot()

  // Three.js is loaded via a separate <script defer> tag before this file.
  // Both scripts use defer, so THREE is guaranteed to be defined here.
  boot();

})();
