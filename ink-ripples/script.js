const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const hint = document.getElementById('hint');
const fadeSlider = document.getElementById('fade');
const clearBtn = document.getElementById('clear');
const modeButtons = document.querySelectorAll('.mode-btn');
const palettesEl = document.getElementById('palettes');

const BG = '10, 10, 18';

const PALETTES = [
  { name: 'Aurora', colors: ['#7df9ff', '#a78bfa', '#f472b6', '#34d399'] },
  { name: 'Ember', colors: ['#ff6b6b', '#ffa94d', '#ffd43b', '#f76707'] },
  { name: 'Deep Sea', colors: ['#0ea5e9', '#22d3ee', '#6366f1', '#2dd4bf'] },
  { name: 'Mono', colors: ['#ffffff', '#e5e7eb', '#cbd5e1', '#f1f5f9'] },
];

let paletteIndex = 0;
let mode = 'both';
let fadeAmount = Number(fadeSlider.value) / 1000;

let dpr = Math.min(window.devicePixelRatio || 1, 2);
let width, height;

function resize() {
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = width + 'px';
  canvas.style.height = height + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
window.addEventListener('resize', resize);
resize();

ctx.fillStyle = `rgb(${BG})`;
ctx.fillRect(0, 0, width, height);

function buildPalettes() {
  palettesEl.innerHTML = '';
  PALETTES.forEach((p, i) => {
    const btn = document.createElement('button');
    btn.className = 'palette-swatch' + (i === paletteIndex ? ' active' : '');
    btn.style.background = `linear-gradient(135deg, ${p.colors[0]}, ${p.colors[2]})`;
    btn.title = p.name;
    btn.addEventListener('click', () => {
      paletteIndex = i;
      document.querySelectorAll('.palette-swatch').forEach(s => s.classList.remove('active'));
      btn.classList.add('active');
    });
    palettesEl.appendChild(btn);
  });
}
buildPalettes();

modeButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    modeButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    mode = btn.dataset.mode;
  });
});

fadeSlider.addEventListener('input', () => {
  fadeAmount = Number(fadeSlider.value) / 1000;
});

clearBtn.addEventListener('click', () => {
  ctx.fillStyle = `rgb(${BG})`;
  ctx.fillRect(0, 0, width, height);
});

function randColor() {
  const c = PALETTES[paletteIndex].colors;
  return c[Math.floor(Math.random() * c.length)];
}

function hexToRgb(hex) {
  const v = parseInt(hex.slice(1), 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

// --- flow field ---
let t = 0;
function curlAngle(x, y) {
  return (
    Math.sin(x * 0.0022 + t * 0.00035) * Math.PI +
    Math.cos(y * 0.0026 - t * 0.00028) * Math.PI
  );
}

// --- particles (trails) ---
class Particle {
  constructor(x, y, vx, vy, color) {
    this.x = x;
    this.y = y;
    this.vx = vx;
    this.vy = vy;
    this.life = 1;
    this.decay = 0.006 + Math.random() * 0.01;
    this.size = 1.5 + Math.random() * 2.5;
    this.color = color;
  }
  update() {
    const angle = curlAngle(this.x, this.y);
    this.vx += Math.cos(angle) * 0.12;
    this.vy += Math.sin(angle) * 0.12;
    this.vx *= 0.94;
    this.vy *= 0.94;
    this.x += this.vx;
    this.y += this.vy;
    this.life -= this.decay;
  }
  draw() {
    if (this.life <= 0) return;
    const [r, g, b] = hexToRgb(this.color);
    ctx.beginPath();
    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${this.life * 0.8})`;
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
  }
}

// --- ripples ---
class Ripple {
  constructor(x, y, color, maxRadius) {
    this.x = x;
    this.y = y;
    this.radius = 2;
    this.maxRadius = maxRadius || 120 + Math.random() * 80;
    this.life = 1;
    this.color = color;
    this.width = 2 + Math.random() * 2;
  }
  update() {
    this.radius += (this.maxRadius - this.radius) * 0.06 + 0.6;
    this.life -= 0.018;
  }
  draw() {
    if (this.life <= 0) return;
    const [r, g, b] = hexToRgb(this.color);
    ctx.beginPath();
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${Math.max(this.life, 0) * 0.6})`;
    ctx.lineWidth = this.width;
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.stroke();
  }
}

let particles = [];
let ripples = [];

let pointer = { x: width / 2, y: height / 2, px: width / 2, py: height / 2, down: false };
let hintHidden = false;

function hideHint() {
  if (!hintHidden) {
    hint.classList.add('hidden');
    hintHidden = true;
  }
}

function spawnTrail(x, y, px, py) {
  const dx = x - px;
  const dy = y - py;
  const dist = Math.hypot(dx, dy);
  const steps = Math.max(1, Math.min(6, Math.floor(dist / 4)));
  for (let i = 0; i < steps; i++) {
    const lx = px + (dx * i) / steps;
    const ly = py + (dy * i) / steps;
    for (let j = 0; j < 2; j++) {
      const spread = (Math.random() - 0.5) * 10;
      particles.push(
        new Particle(
          lx + spread,
          ly + spread,
          dx * 0.05 + (Math.random() - 0.5) * 1.5,
          dy * 0.05 + (Math.random() - 0.5) * 1.5,
          randColor()
        )
      );
    }
  }
  if (particles.length > 900) particles.splice(0, particles.length - 900);
}

function spawnRipple(x, y) {
  ripples.push(new Ripple(x, y, randColor()));
  if (ripples.length > 40) ripples.shift();
}

function getPos(e) {
  const rect = canvas.getBoundingClientRect();
  return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

canvas.addEventListener('pointerdown', (e) => {
  hideHint();
  pointer.down = true;
  const p = getPos(e);
  pointer.x = pointer.px = p.x;
  pointer.y = pointer.py = p.y;
  if (mode === 'ripples' || mode === 'both') spawnRipple(p.x, p.y);
});

canvas.addEventListener('pointermove', (e) => {
  const p = getPos(e);
  pointer.px = pointer.x;
  pointer.py = pointer.y;
  pointer.x = p.x;
  pointer.y = p.y;
  if (mode === 'trails' || mode === 'both') {
    hideHint();
    spawnTrail(pointer.x, pointer.y, pointer.px, pointer.py);
  }
});

canvas.addEventListener('pointerup', () => {
  pointer.down = false;
});

canvas.addEventListener('pointerleave', () => {
  pointer.down = false;
});

function loop() {
  t += 16;

  ctx.fillStyle = `rgba(${BG}, ${fadeAmount})`;
  ctx.fillRect(0, 0, width, height);

  ctx.globalCompositeOperation = 'lighter';

  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.update();
    p.draw();
    if (p.life <= 0) particles.splice(i, 1);
  }

  for (let i = ripples.length - 1; i >= 0; i--) {
    const r = ripples[i];
    r.update();
    r.draw();
    if (r.life <= 0) ripples.splice(i, 1);
  }

  ctx.globalCompositeOperation = 'source-over';

  requestAnimationFrame(loop);
}
loop();
