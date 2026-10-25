document.documentElement.classList.add('has-js');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

// The intro and portrait enter together; a slow GPU never blocks the page.
(() => {
  const pre = document.getElementById('preloader');
  const t0 = performance.now();
  const duration = reduced ? 0 : 1900;
  let ready = false;
  window.addEventListener('portrait-ready', () => { ready = true; });
  function frame(t) {
    const progress = Math.min((t - t0) / Math.max(duration, 1), 1);
    const value = Math.round((1 - Math.pow(1 - progress, 2.5)) * 100);
    document.getElementById('loaderCount').textContent = String(value).padStart(2, '0');
    if (progress < 1 || (!ready && t - t0 < 2800 && !reduced)) return requestAnimationFrame(frame);
    document.getElementById('loaderCount').textContent = '100';
    pre.classList.add('done');
    document.body.classList.add('loaded');
    window.dispatchEvent(new Event('intro-complete'));
    setTimeout(() => pre.remove(), reduced ? 0 : 1000);
  }
  requestAnimationFrame(frame);
})();

// Compact mobile navigation, including keyboard and outside-click dismissal.
(() => {
  const nav = document.getElementById('navbar');
  const toggle = nav.querySelector('button');
  const links = nav.querySelectorAll('.nav-links a');
  function close() { nav.classList.remove('menu-open'); toggle.setAttribute('aria-expanded', 'false'); }
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open)); nav.classList.toggle('menu-open', open);
  });
  links.forEach(a => a.addEventListener('click', close));
  document.addEventListener('pointerdown', e => { if (!nav.contains(e.target)) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav.classList.contains('menu-open')) { close(); toggle.focus(); } });
  matchMedia('(min-width: 761px)').addEventListener('change', close);
  let lastY = scrollY;
  addEventListener('scroll', () => {
    const y=Math.max(0,scrollY),delta=y-lastY;
    nav.classList.toggle('scrolled',y>30);
    if(y<70 || nav.classList.contains('menu-open')) nav.classList.remove('nav-hidden');
    else if(Math.abs(delta)>4) nav.classList.toggle('nav-hidden',delta>0);
    if(Math.abs(delta)>4) lastY=y;
  }, {passive:true});
  nav.addEventListener('focusin',()=>nav.classList.remove('nav-hidden'));
})();

// The page keeps scrolling down while only the project rail moves sideways.
(() => {
  const section = document.getElementById('work');
  const track = document.getElementById('workTrack');
  const wrap = section.querySelector('.work-wrap');
  const panels = [...track.querySelectorAll('.panel')];
  const prev = document.getElementById('workPrev'), next = document.getElementById('workNext');
  let travel = 0, journey = 0, current = 0, pending = false;
  function update() {
    pending = false;
    const p = Math.max(0, Math.min(1, reduced ? wrap.scrollLeft / Math.max(travel,1) : -section.getBoundingClientRect().top / journey));
    if (!reduced) track.style.transform = `translate3d(${-travel * p}px,0,0)`;
    current = Math.min(panels.length - 1, Math.round(p * (panels.length - 1)));
    prev.disabled = current === 0; next.disabled = current === panels.length - 1;
  }
  function fit() {
    travel = Math.max(0, track.scrollWidth - wrap.clientWidth);
    journey = Math.max(1, travel * .58);
    section.style.setProperty('--journey', `${journey}px`);
    update();
  }
  function go(index) {
    index = Math.max(0, Math.min(panels.length - 1, index));
    if (reduced) wrap.scrollTo({left: index * (panels[0].getBoundingClientRect().width + parseFloat(getComputedStyle(track).gap)), behavior:'instant'});
    else scrollTo({ top: scrollY + section.getBoundingClientRect().top + journey * index / (panels.length - 1), behavior: 'smooth' });
  }
  prev.addEventListener('click', () => go(current - 1)); next.addEventListener('click', () => go(current + 1));
  panels.forEach((panel, i) => panel.addEventListener('focusin', () => go(i)));
  let swipe = null, swiped = false;
  track.addEventListener('pointerdown', e => { if (e.pointerType === 'touch' && !reduced) { swipe = { x: e.clientX, y: e.clientY, scroll: scrollY }; swiped = false; } });
  track.addEventListener('pointermove', e => {
    if (!swipe) return;
    const dx=e.clientX-swipe.x, dy=e.clientY-swipe.y;
    if (Math.abs(dx)>15 && Math.abs(dx)>Math.abs(dy)*1.3) { swiped=true; scrollTo({ top:swipe.scroll-dx*journey/travel, behavior:'instant' }); }
  }, {passive:true});
  ['pointerup','pointercancel'].forEach(type => track.addEventListener(type, () => { swipe=null; }));
  track.addEventListener('click', e => { if(swiped) {e.preventDefault();swiped=false;} }, true);
  addEventListener('scroll', () => { if (!pending) { pending = true; requestAnimationFrame(update); } }, { passive: true });
  wrap.addEventListener('scroll', update, {passive:true});
  new ResizeObserver(fit).observe(wrap);
  document.fonts.ready.then(fit);
  fit();
})();

// Reveal supporting content without making reading depend on animation libraries.
(() => {
  const targets = document.querySelectorAll('.sec-label, .display-h, .career-item, .stat, .contact-intro, .socials');
  if (!reduced) {
    const io = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('on'); io.unobserve(e.target); } }), { threshold: .08 });
    targets.forEach(t => { t.classList.add('rv'); io.observe(t); });
  }
  const io = new IntersectionObserver(entries => entries.forEach(e => {
    if (!e.isIntersecting) return;
    io.unobserve(e.target);
    const el = e.target, target = Number(el.dataset.count), decimals = Number(el.dataset.decimals || 0), start = performance.now();
    function frame(t) { const p = reduced ? 1 : Math.min(1, (t - start) / 1000); el.textContent = (target * (1 - (1 - p) ** 3)).toFixed(decimals); if (p < 1) requestAnimationFrame(frame); }
    requestAnimationFrame(frame);
  }), { threshold: .3 });
  document.querySelectorAll('.stat-big').forEach(n => io.observe(n));
})();

// Pointer events give touch and mouse the same physical drag and throw behavior.
(() => {
  const canvas = document.getElementById('stackCanvas'), wrap = document.getElementById('stackWrap');
  const labels = ['Python','C++','Java','JS','SQL','LangChain','RAG','LLMs','Docker','AWS','Flask','Power BI','Sklearn','Pandas','Git','NLP'];
  if (!window.Matter) { wrap.textContent = labels.join(' · '); return; }
  const { Engine, Bodies, Body, Composite, Constraint } = Matter;
  const ctx = canvas.getContext('2d');
  const engine = Engine.create({ enableSleeping: true, gravity: { y: .85 } });
  let balls = [], walls = [], width = 0, height = 0, active = false, last = 0, drag = null, pointer = null, moving = false;
  const colors = [['#e9e4fa','#b7a6df','#221734'], ['#b8a0fb','#7850cf','#ffffff'], ['#ffffff','#cecedd','#221734']];
  function fit() {
    const oldW = width, oldH = height;
    width = wrap.clientWidth; height = wrap.clientHeight;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = width * dpr; canvas.height = height * dpr; ctx.setTransform(dpr,0,0,dpr,0,0);
    walls.forEach(w => Composite.remove(engine.world, w));
    walls = [Bodies.rectangle(width/2,height+25,width+100,50,{isStatic:true}), Bodies.rectangle(-25,height/2,50,height*4,{isStatic:true}), Bodies.rectangle(width+25,height/2,50,height*4,{isStatic:true})];
    Composite.add(engine.world,walls);
    balls.forEach(b => {
      const radius=Math.max(25,Math.min(49,width/13))+(b.label.length>5?8:0);
      Body.scale(b,radius/b.r,radius/b.r); b.r=radius;
      Body.setPosition(b,{x:Math.max(b.r,Math.min(width-b.r,b.position.x*width/(oldW||width))),y:Math.min(height-b.r,b.position.y*height/(oldH||height))});
      Matter.Sleeping.set(b,false);
    });
    draw(); wake();
  }
  function populate() {
    if (drag) { Composite.remove(engine.world,drag); drag = null; }
    balls.forEach(b => Composite.remove(engine.world,b));
    const base = Math.max(25, Math.min(49,width/13));
    balls = labels.map((label,i) => {
      const r = base + (label.length>5 ? 8 : 0);
      const cols = Math.max(3,Math.floor(width/(base*2.6)));
      const b = Bodies.circle((i%cols+.5)*width/cols, reduced ? height-50-Math.floor(i/cols)*70 : -r-Math.floor(i/cols)*(base*2.7),r,{restitution:.66, friction:.08, frictionAir:.012, sleepThreshold:80});
      b.label=label; b.r=r; b.palette=colors[i%3]; return b;
    });
    Composite.add(engine.world,balls); if (reduced) { for(let i=0;i<240;i++) Engine.update(engine,1000/60); draw(); } last=0; wake();
  }
  function draw() {
    ctx.clearRect(0,0,width,height);
    balls.forEach(b => {
      const {x,y}=b.position, r=b.r;
      ctx.save(); ctx.translate(x,y); ctx.rotate(b.angle);
      const g=ctx.createRadialGradient(-r*.3,-r*.4,1,0,0,r);
      g.addColorStop(0,b.palette[0]);g.addColorStop(1,b.palette[1]);
      ctx.fillStyle=g;ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.fill();
      ctx.strokeStyle='#ffffff44';ctx.lineWidth=1;ctx.stroke();
      ctx.fillStyle=b.palette[2];ctx.font=`700 ${Math.max(11,r/3.1)}px Satoshi,system-ui`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(b.label,0,0);ctx.restore();
    });
  }
  function loop(time) {
    if (!active || document.hidden) { moving=false; return; }
    Engine.update(engine, Math.min(time-last||16.67,33.33));last=time;draw();
    if (drag || balls.some(b=>!b.isSleeping)) requestAnimationFrame(loop); else moving=false;
  }
  function wake() { if(active&&!moving&&!document.hidden) { moving=true;last=0;requestAnimationFrame(loop); } }
  const point=e=>{const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)*width/r.width,y:(e.clientY-r.top)*height/r.height};};
  canvas.addEventListener('pointerdown',e=>{
    const p=point(e);const ball=[...balls].reverse().find(b=>Math.hypot(b.position.x-p.x,b.position.y-p.y)<b.r+8);
    if(!ball) return;
    pointer=e.pointerId;canvas.setPointerCapture(pointer);
    Matter.Sleeping.set(ball,false);
    drag=Constraint.create({pointA:p,bodyB:ball,pointB:{x:0,y:0},stiffness:.18,damping:.08,length:0});Composite.add(engine.world,drag);wake();
  });
  canvas.addEventListener('pointermove',e=>{if(drag&&e.pointerId===pointer) {drag.pointA=point(e);wake();}});
  const release=()=>{if(drag) Composite.remove(engine.world,drag);drag=null;pointer=null;};
  ['pointerup','pointercancel','lostpointercapture'].forEach(event=>canvas.addEventListener(event,release));
  new IntersectionObserver(entries=>{active=entries[0].isIntersecting;if(active){if(!balls.length)populate();wake();}},{rootMargin:'120px'}).observe(wrap);
  document.addEventListener('visibilitychange',wake);
  document.getElementById('resetStack').addEventListener('click',populate);
  new ResizeObserver(fit).observe(wrap);fit();
})();
