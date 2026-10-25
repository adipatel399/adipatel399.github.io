import * as THREE from 'three';
import { RoomEnvironment } from './assets/vendor/RoomEnvironment.js';
import { GLTFLoader } from './assets/vendor/GLTFLoader.js';
import { DRACOLoader } from './assets/vendor/DRACOLoader.js';

const host = document.getElementById('heroPortrait');
const canvas = document.getElementById('portraitCanvas');
const motion = matchMedia('(prefers-reduced-motion: reduce)');
const ready = () => window.dispatchEvent(new Event('portrait-ready'));

async function buildPortrait() {
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .91;
  const scene = new THREE.Scene();
  // Local studio lighting supplies real reflections on the curved lenses and frames.
  const pmrem = new THREE.PMREMGenerator(renderer);
  const studio = new RoomEnvironment();
  const environment = pmrem.fromScene(studio, .025);
  // Keep the skin under the portrait lights; reflections belong to the eyewear.
  studio.dispose();
  pmrem.dispose();
  const camera = new THREE.OrthographicCamera(-2.5, 2.5, 2.5, -2.5, .1, 30);
  camera.position.set(0, .87, 9);
  camera.lookAt(0, .87, 0);
  scene.add(new THREE.HemisphereLight(0xf3efff, 0x38303f, 1.25));
  function light(color, intensity, x, y, z) {
    const l = new THREE.DirectionalLight(color, intensity);
    l.position.set(x, y, z);
    scene.add(l);
  }
  light(0xffe9d9, 2.5, -3, 4, 5);
  light(0xc4d3ff, 1.15, 3, 2, 3);
  light(0xa889ff, 2.8, 2, 3, -3);

  const decoder = new DRACOLoader().setDecoderPath('./assets/vendor/draco/').setWorkerLimit(1);
  const loader = new GLTFLoader().setDRACOLoader(decoder);
  let gltf;
  try {
    gltf = await loader.loadAsync('./assets/avatar/portrait.glb?v=reference-polo-final');
  } finally {
    decoder.dispose();
  }
  const body = new THREE.Group();
  body.add(gltf.scene);
  scene.add(body);
  const head = gltf.scene.getObjectByName('Head');
  if (!head) throw new Error('Portrait head rig is missing');
  const headRest = head.quaternion.clone();
  const turn = new THREE.Quaternion();
  const rotation = new THREE.Euler(0, 0, 0, 'YXZ');
  gltf.scene.traverse(object => {
    if (!object.isMesh) return;
    // The silhouette changes as the head turns; do not cull from the bind-pose bounds.
    object.frustumCulled = false;
    if (object.material.name === 'Textured dark hair') {
      object.material.alphaTest = .4;
      object.material.transparent = false;
      object.material.depthWrite = true;
    }
    const polished = /sunglasses/i.test(object.material.name);
    if (polished) {
      object.material.envMap = environment.texture;
      object.material.envMapIntensity = .35;
    }
    if (object.material.map) object.material.map.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
  });

  let visible = true;
  let running = false;
  let entered = document.body.classList.contains('loaded');
  let start = performance.now();
  let last = 0;
  let lastDraw = 0;
  const target = { x: 0, y: 0 };
  const current = { x: 0, y: 0 };
  function look(event) {
    const bounds = host.getBoundingClientRect();
    target.x = THREE.MathUtils.clamp((event.clientX - bounds.left - bounds.width / 2) / (innerWidth / 2), -1, 1) * .38;
    target.y = THREE.MathUtils.clamp((event.clientY - bounds.top - bounds.height * .22) / (innerHeight / 2), -1, 1) * .16;
    wake();
  }
  addEventListener('pointermove', look, { passive: true });
  addEventListener('pointerdown', look, { passive: true });
  addEventListener('intro-complete', () => { entered = true; start = performance.now(); wake(); });
  document.addEventListener('pointerleave', () => { target.x = target.y = 0; wake(); });
  addEventListener('blur', () => { target.x = target.y = 0; });

  function fit() {
    const width = host.clientWidth, height = host.clientHeight;
    if (!width || !height) return;
    renderer.setSize(width, height, false);
    host.closest('.hero').style.setProperty('--portrait-title-bottom', `${parseFloat(getComputedStyle(host).bottom) + height * .09}px`);
    const aspect = width / height;
    const viewHeight = Math.max(2.9, 2.2 / aspect);
    const fadeEnd = .5 + 1.31 / viewHeight - .012;
    host.style.setProperty('--portrait-fade-start', `${(fadeEnd - .12) * 100}%`);
    host.style.setProperty('--portrait-fade-end', `${fadeEnd * 100}%`);
    camera.left = -viewHeight * aspect / 2;
    camera.right = viewHeight * aspect / 2;
    camera.top = viewHeight / 2;
    camera.bottom = -viewHeight / 2;
    camera.updateProjectionMatrix();
    const poster = host.querySelector('.portrait-fallback');
    poster.style.height = `${height * 2.9 / viewHeight}px`;
    poster.style.top = `${(height - height * 2.9 / viewHeight) / 2}px`;
    wake();
  }
  function animate(time) {
    if (!visible || document.hidden) { running = false; return; }
    const dt = Math.min((time - last) / 1000 || .016, .05);
    last = time;
    const follow = motion.matches ? 1 : 1 - Math.exp(-8 * dt);
    current.x += (target.x - current.x) * follow;
    current.y += (target.y - current.y) * follow;
    rotation.set(current.y, current.x, -current.x * .035);
    head.quaternion.copy(headRest).multiply(turn.setFromEuler(rotation));
    const progress = motion.matches ? 1 : Math.min(1, (time - start) / 1400);
    const ease = 1 - (1 - progress) ** 3;
    const breathing = motion.matches ? 0 : Math.sin(time / 1650) * .003;
    body.position.y = (entered ? -.10 * (1 - ease) : -.10) + breathing;
    body.rotation.y = entered ? -.14 * (1 - ease) : -.14;
    body.scale.setScalar(1 + breathing * .22);
    // Thirty frames per second is enough for the slow idle breathing on mobile.
    if (time - lastDraw > 1000 / 30 || motion.matches) {
      renderer.render(scene, camera);
      lastDraw = time;
    }
    if (!motion.matches || Math.abs(target.x - current.x) > .001 || Math.abs(target.y - current.y) > .001) {
      requestAnimationFrame(animate);
    } else running = false;
  }
  function wake() {
    if (visible && !document.hidden && !running) { running = true; last = 0; requestAnimationFrame(animate); }
  }
  new ResizeObserver(fit).observe(host);
  new IntersectionObserver(entries => { visible = entries[0].isIntersecting; wake(); }, { rootMargin: '60px' }).observe(host);
  document.addEventListener('visibilitychange', wake);
  motion.addEventListener('change', wake);
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault(); visible = false; host.classList.remove('portrait-ready');
  });
  canvas.addEventListener('webglcontextrestored', () => { visible = true; host.classList.add('portrait-ready'); wake(); });
  fit();
  renderer.render(scene, camera);
  host.classList.add('portrait-ready');
  ready();
  wake();
}

buildPortrait().catch(error => {
  console.warn('Interactive portrait unavailable; showing the Blender render.', error);
  host.classList.add('portrait-unavailable');
  ready();
});
