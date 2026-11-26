/**
 * NVIDIA BioNeMo & NIM Inference Benchmark — 100vh "Time Collapsing" WebGL Hero Canvas
 * Stops RAF cleanly when hidden or scrolled out of view; handles context loss cleanly.
 */

(function () {
  'use strict';

  function renderStaticFallback(canvas) {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const w = (canvas.width = canvas.clientWidth || 1);
    const h = (canvas.height = canvas.clientHeight || 1);
    const grad = ctx.createRadialGradient(w / 2, h / 2, 40, w / 2, h / 2, Math.max(w, h) * 0.6);
    grad.addColorStop(0, 'rgba(118, 245, 162, 0.18)');
    grad.addColorStop(0.4, 'rgba(92, 225, 255, 0.08)');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
  }

  function initHeroWebGL() {
    const canvas = document.getElementById('heroWebGLCanvas');
    if (!canvas) return;

    const prefersReducedMotion =
      window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      renderStaticFallback(canvas);
      return;
    }

    const gl =
      canvas.getContext('webgl', { alpha: true, antialias: true, powerPreference: 'high-performance' }) ||
      canvas.getContext('experimental-webgl', { alpha: true, antialias: true });

    if (!gl) {
      renderStaticFallback(canvas);
      return;
    }

    const vsSource = `
      precision mediump float;
      attribute vec3 aPosition;
      attribute vec2 aRibbonCoord;
      uniform float uTime;
      uniform float uCollapseProgress;
      uniform vec2 uParallax;
      uniform mat4 uProjection;
      varying float vProgress;
      varying float vCollapse;
      varying float vDepth;
      void main() {
        float t = aRibbonCoord.x;
        float w = aRibbonCoord.y;
        float phase = t * 14.0 - uTime * 1.4;
        float helixA = sin(phase) * 0.42;
        float helixB = cos(phase) * 0.42;
        float collapse = uCollapseProgress;
        float spreadX = (t - 0.5) * 6.5;
        float spreadY = helixA + w * (1.1 - collapse * 0.65);
        float spreadZ = helixB + sin(t * 20.0 + uTime * 0.8) * (0.35 - collapse * 0.25);
        float beamY = helixA * 0.35 + w * 0.12 * sin(t * 10.0 + uTime * 2.0);
        float beamZ = helixB * 0.35;
        vec3 pos = vec3(
          spreadX,
          mix(spreadY, beamY, collapse),
          mix(spreadZ, beamZ, collapse)
        );
        pos.x += uParallax.x * 0.35 * (1.0 - abs(t - 0.5));
        pos.y += uParallax.y * 0.25 * (1.0 - abs(t - 0.5));
        gl_Position = uProjection * vec4(pos, 1.0);
        float pulseSize = 2.4 + 1.8 * sin(t * 25.0 - uTime * 4.5);
        gl_PointSize = clamp(pulseSize * (1.2 + collapse * 0.4), 1.5, 5.5);
        vProgress = t;
        vCollapse = collapse;
        vDepth = pos.z;
      }
    `;

    const fsSource = `
      precision mediump float;
      varying float vProgress;
      varying float vCollapse;
      varying float vDepth;
      void main() {
        vec2 coord = gl_PointCoord - vec2(0.5);
        float dist = length(coord);
        if (dist > 0.5) discard;
        float alpha = smoothstep(0.5, 0.05, dist) * 0.82;
        vec3 ember = vec3(1.0, 0.54, 0.29);
        vec3 nimGreen = vec3(0.46, 0.96, 0.64);
        vec3 cyan = vec3(0.36, 0.88, 1.0);
        vec3 baseColor = mix(ember, mix(nimGreen, cyan, sin(vProgress * 3.14159)), vCollapse);
        float depthFade = clamp(0.55 + 0.45 * (vDepth + 0.5), 0.25, 1.0);
        gl_FragColor = vec4(baseColor, alpha * depthFade);
      }
    `;

    function compileShader(type, source) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    }

    const vs = compileShader(gl.VERTEX_SHADER, vsSource);
    const fs = compileShader(gl.FRAGMENT_SHADER, fsSource);
    if (!vs || !fs) {
      renderStaticFallback(canvas);
      return;
    }

    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      renderStaticFallback(canvas);
      return;
    }

    const isMobile = window.innerWidth < 768 || (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
    const totalParticles = isMobile ? 15000 : 45000;
    const positions = new Float32Array(totalParticles * 3);
    const ribbonCoords = new Float32Array(totalParticles * 2);

    for (let i = 0; i < totalParticles; i++) {
      const t = i / totalParticles;
      const w = Math.random() * 2.0 - 1.0;
      positions[i * 3] = (t - 0.5) * 6.0;
      positions[i * 3 + 1] = w * 0.5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 0.5;
      ribbonCoords[i * 2] = t;
      ribbonCoords[i * 2 + 1] = w;
    }

    const posBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

    const coordBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, coordBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, ribbonCoords, gl.STATIC_DRAW);

    const aPosition = gl.getAttribLocation(program, 'aPosition');
    const aRibbonCoord = gl.getAttribLocation(program, 'aRibbonCoord');
    const uTime = gl.getUniformLocation(program, 'uTime');
    const uCollapseProgress = gl.getUniformLocation(program, 'uCollapseProgress');
    const uParallax = gl.getUniformLocation(program, 'uParallax');
    const uProjection = gl.getUniformLocation(program, 'uProjection');

    function createPerspectiveMatrix(fovRadians, aspect, near, far) {
      const f = 1.0 / Math.tan(fovRadians / 2);
      const nf = 1 / (near - far);
      return new Float32Array([
        f / aspect, 0, 0, 0,
        0, f, 0, 0,
        0, 0, (far + near) * nf, -1,
        0, 0, (2 * far * near) * nf, 0
      ]);
    }

    let targetParallaxX = 0;
    let targetParallaxY = 0;
    let currentParallaxX = 0;
    let currentParallaxY = 0;

    if (!isMobile) {
      window.addEventListener('mousemove', (e) => {
        targetParallaxX = (e.clientX / window.innerWidth) * 2 - 1;
        targetParallaxY = -(e.clientY / window.innerHeight) * 2 + 1;
      }, { passive: true });
    }

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, canvas.clientWidth);
      const height = Math.max(1, canvas.clientHeight);
      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
    }
    window.addEventListener('resize', resize, { passive: true });
    resize();

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.disable(gl.DEPTH_TEST);

    const startTime = performance.now();
    let isVisible = true;
    let isContextLost = false;
    let rafId = 0;

    function stopLoop() {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = 0;
      }
    }

    function startLoop() {
      if (!rafId && isVisible && !document.hidden && !isContextLost) {
        rafId = requestAnimationFrame(render);
      }
    }

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          isVisible = entry.isIntersecting;
        });
        if (isVisible && !document.hidden) startLoop();
        else stopLoop();
      }, { threshold: 0.05 });
      observer.observe(canvas);
    }

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stopLoop();
      else startLoop();
    });

    canvas.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      isContextLost = true;
      stopLoop();
    }, false);

    canvas.addEventListener('webglcontextrestored', () => {
      isContextLost = false;
      initHeroWebGL();
    }, false);

    function render(now) {
      rafId = 0;
      if (!isVisible || document.hidden || isContextLost) return;

      resize();
      if (canvas.width === 0 || canvas.height === 0) return;

      const elapsed = (now - startTime) * 0.001;
      const collapseProgress = Math.min(1.0, Math.max(0.0, (elapsed - 0.6) / 1.8));

      currentParallaxX += (targetParallaxX - currentParallaxX) * 0.05;
      currentParallaxY += (targetParallaxY - currentParallaxY) * 0.05;

      gl.clearColor(0.0, 0.0, 0.0, 0.0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(program);

      const aspect = canvas.width / Math.max(1, canvas.height);
      const proj = createPerspectiveMatrix(Math.PI / 3.5, aspect, 0.1, 100.0);
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
      rafId = requestAnimationFrame(render);
    }

    startLoop();
  }

  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(initHeroWebGL, { timeout: 120 });
  } else {
    setTimeout(initHeroWebGL, 40);
  }
})();
