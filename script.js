// Always replay the intro from the top; don't let the browser restore a mid-page scroll position
if ("scrollRestoration" in history) history.scrollRestoration = "manual";
window.scrollTo(0, 0);

const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const hasGsap = typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined";
if (hasGsap) {
  gsap.registerPlugin(ScrollTrigger);
  document.documentElement.classList.add("has-gsap");
}

/* ============ Preloader: 0 → 100 counter, then curtain lift ============ */
(() => {
  const count = document.getElementById("loaderCount");
  const pre = document.getElementById("preloader");
  const total = reduced ? 200 : 1900;
  const t0 = performance.now();
  function frame(t) {
    const p = Math.min((t - t0) / total, 1);
    const eased = 1 - Math.pow(1 - p, 2.5);
    count.textContent = Math.round(eased * 100);
    if (p < 1) requestAnimationFrame(frame);
    else {
      pre.classList.add("done");
      document.body.classList.add("loaded");
      setTimeout(() => (pre.style.display = "none"), 1000);
    }
  }
  requestAnimationFrame(frame);
})();

/* ============ Custom cursor ============ */
(() => {
  if (window.matchMedia("(hover: none)").matches) return;
  const dot = document.getElementById("cursorDot");
  const ring = document.getElementById("cursorRing");
  let x = -100, y = -100, rx = -100, ry = -100;
  window.addEventListener("mousemove", (e) => { x = e.clientX; y = e.clientY; });
  (function loop() {
    rx += (x - rx) * 0.16;
    ry += (y - ry) * 0.16;
    dot.style.transform = `translate(${x - 4}px, ${y - 4}px)`;
    ring.style.transform = `translate(${rx - 19}px, ${ry - 19}px)`;
    requestAnimationFrame(loop);
  })();
  document.querySelectorAll("a, [data-hover]").forEach((el) => {
    el.addEventListener("mouseenter", () => ring.classList.add("hovering"));
    el.addEventListener("mouseleave", () => ring.classList.remove("hovering"));
  });
})();

/* ============ Statement: split into words, light up on scroll ============ */
(() => {
  const st = document.getElementById("statement");
  const KEY = new Set(["AI", "engineer", "RAG", "10K+", "JARVIS", "BNP", "Paribas", "ships.", "8.41."]);
  const words = st.textContent.trim().split(/\s+/);
  st.innerHTML = words
    .map((w) => `<span class="word${KEY.has(w) ? " key" : ""}">${w}</span>`)
    .join(" ");
  const spans = st.querySelectorAll(".word");
  if (hasGsap && !reduced) {
    ScrollTrigger.create({
      trigger: st,
      start: "top 85%",
      end: "bottom 45%",
      scrub: 0.4,
      onUpdate: (self) => {
        const n = Math.floor(self.progress * spans.length);
        spans.forEach((s, i) => s.classList.toggle("lit", i <= n));
      },
    });
  } else {
    spans.forEach((s) => s.classList.add("lit"));
  }
})();

/* ============ Reveal-on-scroll for section furniture ============ */
(() => {
  const targets = document.querySelectorAll(
    ".sec-label, .display-h, .career-item, .stat, .stack-hint, .contact-mail, .socials"
  );
  targets.forEach((t) => t.classList.add("rv"));
  const io = new IntersectionObserver((es) => {
    es.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("on"); io.unobserve(e.target); }
    });
  }, { threshold: 0.15 });
  targets.forEach((t) => io.observe(t));
})();

/* ============ Count-up stats ============ */
(() => {
  const nums = document.querySelectorAll(".stat-big");
  const io = new IntersectionObserver((es) => {
    es.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      io.unobserve(el);
      const target = parseFloat(el.dataset.count);
      const dec = parseInt(el.dataset.decimals || "0", 10);
      const prefix = el.dataset.prefix || "";
      const t0 = performance.now(), dur = 1500;
      (function f(t) {
        const p = Math.min((t - t0) / dur, 1);
        el.textContent = prefix + (target * (1 - Math.pow(1 - p, 3))).toFixed(dec);
        if (p < 1) requestAnimationFrame(f);
      })(t0);
    });
  }, { threshold: 0.5 });
  nums.forEach((n) => io.observe(n));
})();

/* ============ Horizontal work gallery (pinned, scrubbed) ============ */
(() => {
  const track = document.getElementById("workTrack");
  if (!hasGsap || reduced || window.innerWidth < 860) return;
  const dist = () => track.scrollWidth - window.innerWidth;
  gsap.to(track, {
    x: () => -dist(),
    ease: "none",
    scrollTrigger: {
      trigger: "#work",
      start: "top top",
      end: () => "+=" + dist(),
      pin: true,
      scrub: 1,
      invalidateOnRefresh: true,
    },
  });
})();

/* ============ Parallax orbs ============ */
(() => {
  if (!hasGsap || reduced) return;
  gsap.to(".orb-1", { y: 250, scrollTrigger: { trigger: "body", start: "top top", end: "max", scrub: 1.5 } });
  gsap.to(".orb-2", { y: -200, scrollTrigger: { trigger: "body", start: "top top", end: "max", scrub: 1.5 } });
})();

/* ============ Techstack physics balls (matter.js) ============ */
(() => {
  if (typeof Matter === "undefined") return;
  const wrap = document.getElementById("stackWrap");
  const canvas = document.getElementById("stackCanvas");
  const ctx = canvas.getContext("2d");
  const TECHS = [
    "Python", "C++", "Java", "JS", "SQL", "LangChain", "RAG", "LLMs",
    "Docker", "AWS", "Flask", "Power BI", "Sklearn", "Pandas", "Git", "NLP",
  ];
  let engine, balls = [], started = false, raf;

  function fit() {
    canvas.width = wrap.clientWidth * devicePixelRatio;
    canvas.height = wrap.clientHeight * devicePixelRatio;
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  }

  function start() {
    if (started) return;
    started = true;
    fit();
    const W = wrap.clientWidth, H = wrap.clientHeight;
    engine = Matter.Engine.create({ gravity: { y: 1 } });
    const wallOpts = { isStatic: true };
    Matter.Composite.add(engine.world, [
      Matter.Bodies.rectangle(W / 2, H + 40, W * 2, 80, wallOpts),
      Matter.Bodies.rectangle(-40, H / 2, 80, H * 4, wallOpts),
      Matter.Bodies.rectangle(W + 40, H / 2, 80, H * 4, wallOpts),
    ]);
    const base = Math.max(34, Math.min(56, W / 18));
    balls = TECHS.map((label, i) => {
      const r = base + (label.length > 6 ? 12 : label.length > 3 ? 6 : 0);
      const b = Matter.Bodies.circle(
        60 + Math.random() * (W - 120),
        -80 - i * 90,
        r,
        { restitution: 0.55, friction: 0.05, frictionAir: 0.008 }
      );
      b.label = label;
      b.r = r;
      b.hue = i % 3; // 0 white, 1 lavender, 2 violet
      return b;
    });
    Matter.Composite.add(engine.world, balls);

    // drag interaction
    const mouse = Matter.Mouse.create(canvas);
    mouse.pixelRatio = devicePixelRatio;
    const mc = Matter.MouseConstraint.create(engine, {
      mouse, constraint: { stiffness: 0.15, render: { visible: false } },
    });
    Matter.Composite.add(engine.world, mc);
    // let page scrolling still work over the canvas
    mouse.element.removeEventListener("wheel", mouse.mousewheel);
    mouse.element.removeEventListener("mousewheel", mouse.mousewheel);
    mouse.element.removeEventListener("DOMMouseScroll", mouse.mousewheel);
    mouse.element.removeEventListener("touchmove", mouse.mousemove);

    (function loop() {
      Matter.Engine.update(engine, 1000 / 60);
      draw();
      raf = requestAnimationFrame(loop);
    })();
  }

  function draw() {
    const W = wrap.clientWidth, H = wrap.clientHeight;
    ctx.clearRect(0, 0, W, H);
    for (const b of balls) {
      ctx.save();
      ctx.translate(b.position.x, b.position.y);
      ctx.rotate(b.angle);
      const grad = ctx.createRadialGradient(-b.r * 0.35, -b.r * 0.35, b.r * 0.1, 0, 0, b.r);
      if (b.hue === 1) { grad.addColorStop(0, "#e6ddff"); grad.addColorStop(1, "#b39dfa"); }
      else if (b.hue === 2) { grad.addColorStop(0, "#a98ef7"); grad.addColorStop(1, "#7c4ff0"); }
      else { grad.addColorStop(0, "#ffffff"); grad.addColorStop(1, "#d8d4e8"); }
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(0, 0, b.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = b.hue === 2 ? "#f4f0ff" : "#1a1030";
      ctx.font = `700 ${Math.max(12, b.r / 2.6)}px Satoshi, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(b.label, 0, 0);
      ctx.restore();
    }
  }

  const io = new IntersectionObserver((es) => {
    es.forEach((e) => { if (e.isIntersecting) { start(); io.disconnect(); } });
  }, { threshold: 0.2 });
  io.observe(wrap);
  window.addEventListener("resize", () => { if (started) fit(); });
})();

/* ============ Recalculate scroll distances once web fonts are in ============ */
if (hasGsap && document.fonts?.ready) {
  document.fonts.ready.then(() => ScrollTrigger.refresh());
}

/* ============ Magnetic LET'S TALK ============ */
(() => {
  if (window.matchMedia("(hover: none)").matches || reduced) return;
  const el = document.getElementById("letsTalk");
  el.addEventListener("mousemove", (e) => {
    const r = el.getBoundingClientRect();
    const dx = (e.clientX - r.left - r.width / 2) / r.width;
    const dy = (e.clientY - r.top - r.height / 2) / r.height;
    el.style.transform = `translate(${dx * 26}px, ${dy * 18}px)`;
  });
  el.addEventListener("mouseleave", () => { el.style.transform = ""; });
})();
