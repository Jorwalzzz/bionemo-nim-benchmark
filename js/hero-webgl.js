/**
 * NVIDIA BioNeMo & NIM Inference Benchmark — 100vh "Time Collapsing" WebGL Hero Canvas (v4.0.0)
 * Visualizes CPU Ember Crawl (#FF8A4C, 32.4s) collapsing into NIM Bioluminescent Shockwave (#76F5A2, 0.55s).
 * Pure zero-dependency WebGL GLSL shader particle ribbon. Auto-scales 45k (desktop) -> 15k (mobile).
 */

(function () {
  'use strict';

  function initHeroWebGL() {
    const canvas = document.getElementById('heroWebGLCanvas');
    if (!canvas) return;

    // Check reduced motion
    const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      renderStaticFallback(canvas);
      return;
    }

    const gl = canvas.getContext('webgl', { alpha: true, antialias: true, powerPreference: 'high-performance' }) ||
               canvas.getContext('experimental-webgl', { alpha: true, antialias: true });

    if (!gl) {
      renderStaticFallback(canvas);
      return;
    }

    // -------------------------------------------------------------------------
    // 1. GLSL SHADER SOURCES
    // -------------------------------------------------------------------------
    const vsSource = `
      precision mediump float;
      attribute vec3 aPosition;
      attribute vec2 aRibbonCoord; // x: along length (0..1), y: across width (-1..1)

      uniform mat4 uProjection;
      uniform float uTime;
      uniform vec2 uParallax;
      uniform float uCollapseProgress; // 0.0 (slow CPU ember) -> 1.0 (NIM shockwave collapsed)

      varying vec2 vRibbonCoord;
      varying float vEmberFactor;

      void main() {
        vRibbonCoord = aRibbonCoord;

        // Wave dynamics
        float waveSpeed = mix(0.8, 3.2, uCollapseProgress);
        float waveFreq = mix(2.5, 5.0, uCollapseProgress);
        float amp = mix(0.45, 0.18, uCollapseProgress);

        float zWave = sin(aRibbonCoord.x * waveFreq - uTime * waveSpeed) * amp;
        float yWave = cos(aRibbonCoord.x * 3.0 + uTime * (waveSpeed * 0.7)) * (amp * 0.6);

        // Ribbon twist
        float twistAngle = aRibbonCoord.x * 3.14159 * 1.5 + uTime * 0.3;
        vec3 pos = aPosition;
        pos.y += yWave + aRibbonCoord.y * cos(twistAngle) * mix(0.35, 0.15, uCollapseProgress);
        pos.z += zWave + aRibbonCoord.y * sin(twistAngle) * mix(0.35, 0.15, uCollapseProgress);

        // Cursor parallax
        pos.x += uParallax.x * 0.25;
        pos.y += uParallax.y * 0.25;

        // Ember sweep calculation
        float emberTrace = clamp((aRibbonCoord.x - (uTime * 0.15)) * 4.0, 0.0, 1.0);
        vEmberFactor = mix(emberTrace, 0.0, clamp(uCollapseProgress * 1.5, 0.0, 1.0));

        gl_Position = uProjection * vec4(pos, 1.0);
        gl_PointSize = mix(2.2, 3.2, uCollapseProgress);
      }
    `;

    const fsSource = `
      precision mediump float;

      varying vec2 vRibbonCoord;
      varying float vEmberFactor;
      uniform float uCollapseProgress;

      void main() {
        // Soft round particle disc
        vec2 coord = gl_PointCoord - vec2(0.5);
        if (length(coord) > 0.5) {
          discard;
        }

        // Palette definitions
        vec3 emberColor = vec3(1.0, 0.54, 0.30);      // #FF8A4C CPU Ember
        vec3 signalGreen = vec3(0.46, 0.96, 0.64);     // #76F5A2 NIM Flash
        vec3 coldCyan = vec3(0.36, 0.88, 1.0);         // #5CE1FF Molecular Cyan

        // Color transition
        vec3 baseColor = mix(signalGreen, coldCyan, sin(vRibbonCoord.x * 6.28) * 0.5 + 0.5);
        vec3 finalColor = mix(baseColor, emberColor, vEmberFactor * (1.0 - uCollapseProgress));

        float alpha = mix(0.45, 0.85, uCollapseProgress) * (1.0 - abs(vRibbonCoord.y));
        gl_FragColor = vec4(finalColor, alpha);
      }
    `;

    // -------------------------------------------------------------------------
    // 2. SHADER COMPILATION & PROGRAM LINK
    // -------------------------------------------------------------------------
    function compileShader(src, type) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.warn('Shader compile failed:', gl.getShaderInfoLog(s));
        gl.deleteShader(s);
        return null;
      }
      return s;
    }

    const vs = compileShader(vsSource, gl.VERTEX_SHADER);
    const fs = compileShader(fsSource, gl.FRAGMENT_SHADER);
    if (!vs || !fs) {
      renderStaticFallback(canvas);
      return;
    }

    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.warn('Program link failed:', gl.getProgramInfoLog(program));
      renderStaticFallback(canvas);
      return;
    }

    // -------------------------------------------------------------------------
    // 3. BUFFER GEOMETRY: 45K PARTICLES (DESKTOP) / 15K (MOBILE)
    // -------------------------------------------------------------------------
    const isMobile = window.innerWidth < 768;
    const numSteps = isMobile ? 180 : 360;
    const numAcross = isMobile ? 80 : 125;
    const totalParticles = numSteps * numAcross;

    const positions = new Float32Array(totalParticles * 3);
    const ribbonCoords = new Float32Array(totalParticles * 2);

    let ptrPos = 0;
    let ptrCoord = 0;

    for (let i = 0; i < numSteps; i++) {
      const u = i / (numSteps - 1); // 0..1
      const x = (u - 0.5) * 4.6;   // -2.3 .. +2.3

      for (let j = 0; j < numAcross; j++) {
        const v = (j / (numAcross - 1)) * 2.0 - 1.0; // -1..1
        const y = v * 0.45;
        const z = (Math.random() - 0.5) * 0.2;

        positions[ptrPos++] = x + (Math.random() - 0.5) * 0.04;
        positions[ptrPos++] = y;
        positions[ptrPos++] = z;

        ribbonCoords[ptrCoord++] = u;
        ribbonCoords[ptrCoord++] = v;
      }
    }

    const posBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

    const coordBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, coordBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, ribbonCoords, gl.STATIC_DRAW);

    // Attribute & Uniform locations
    const aPosition = gl.getAttribLocation(program, 'aPosition');
    const aRibbonCoord = gl.getAttribLocation(program, 'aRibbonCoord');

    const uProjection = gl.getUniformLocation(program, 'uProjection');
    const uTime = gl.getUniformLocation(program, 'uTime');
    const uParallax = gl.getUniformLocation(program, 'uParallax');
    const uCollapseProgress = gl.getUniformLocation(program, 'uCollapseProgress');

    // Simple Perspective Projection Matrix (4x4)
    function createPerspectiveMatrix(fov, aspect, near, far) {
      const f = 1.0 / Math.tan(fov / 2.0);
      const nf = 1.0 / (near - far);
      return new Float32Array([
        f / aspect, 0, 0, 0,
        0, f, 0, 0,
        0, 0, (far + near) * nf, -1,
        0, 0, (2.0 * far * near) * nf, 0
      ]);
    }

    // -------------------------------------------------------------------------
    // 4. ANIMATION & PARALLAX LOOP
    // -------------------------------------------------------------------------
    let currentParallaxX = 0;
    let currentParallaxY = 0;
    let targetParallaxX = 0;
    let targetParallaxY = 0;

    window.addEventListener('mousemove', (e) => {
      targetParallaxX = (e.clientX / window.innerWidth) * 2.0 - 1.0;
      targetParallaxY = -((e.clientY / window.innerHeight) * 2.0 - 1.0);
    }, { passive: true });

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
    }
    window.addEventListener('resize', resize, { passive: true });
    resize();

    // Enable Blending for luminous particle glow
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.disable(gl.DEPTH_TEST);

    const startTime = performance.now();
    let isVisible = true;

    // Viewport Visibility: pause when hero is scrolled out of view
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          isVisible = entry.isIntersecting;
        });
      }, { threshold: 0.05 });
      observer.observe(canvas);
    }

    function render(now) {
      if (!isVisible) {
        requestAnimationFrame(render);
        return;
      }

      resize();

      const elapsed = (now - startTime) * 0.001; // seconds

      // Collapse animation sequence:
      // 0..1.2s: Ember crawl -> 1.2..2.4s: Shockwave collapse -> 2.4s+: Resonant bioluminescent NIM ribbon
      const collapseProgress = Math.min(1.0, Math.max(0.0, (elapsed - 0.6) / 1.8));

      // Parallax smooth interpolation
      currentParallaxX += (targetParallaxX - currentParallaxX) * 0.05;
      currentParallaxY += (targetParallaxY - currentParallaxY) * 0.05;

      gl.clearColor(0.0, 0.0, 0.0, 0.0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(program);

      // Camera Matrix setup (View translated back 2.8 units)
      const aspect = canvas.width / canvas.height;
      const proj = createPerspectiveMatrix(Math.PI / 3.5, aspect, 0.1, 100.0);
      // Translate in Z
      proj[14] -= 2.6;

      gl.uniformMatrix4fv(uProjection, false, proj);
      gl.uniform1f(uTime, elapsed);
      gl.uniform2f(uParallax, currentParallaxX, currentParallaxY);
      gl.uniform1f(uCollapseProgress, collapseProgress);

      gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
      gl.enableVertexAttribArray(aPosition);
      gl.vertexAttribPointer(aPosition, 3, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, coordBuffer);
      gl.enableVertexAttribArray(aRibbonCoord);
      gl.vertexAttribPointer(aRibbonCoord, 2, gl.FLOAT, false, 0, 0);

      gl.drawArrays(gl.POINTS, 0, totalParticles);

      requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
  }

  // Static Fallback for reduced motion or non-WebGL environments
  function renderStaticFallback(canvas) {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const w = canvas.width = canvas.clientWidth;
    const h = canvas.height = canvas.clientHeight;
    const grad = ctx.createRadialGradient(w / 2, h / 2, 40, w / 2, h / 2, Math.max(w, h) * 0.6);
    grad.addColorStop(0, 'rgba(118, 245, 162, 0.18)');
    grad.addColorStop(0.4, 'rgba(92, 225, 255, 0.08)');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
  }

  // Defer initialization to idle callback to guarantee LCP < 1.0s
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(initHeroWebGL, { timeout: 120 });
  } else {
    setTimeout(initHeroWebGL, 40);
  }
})();
