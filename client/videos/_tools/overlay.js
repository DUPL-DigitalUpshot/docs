// Demo overlay: step caption, spotlight ring, visible cursor. Survives reloads via sessionStorage.
(() => {
  if (!location.protocol.startsWith('http')) return;
  const CSS = `
  #demo-cap{position:fixed;left:260px;bottom:22px;z-index:2147483646;max-width:430px;
    background:rgba(17,24,39,.94);color:#fff;border-radius:14px;padding:14px 18px 15px;
    font:500 14px/1.45 Inter,system-ui,sans-serif;box-shadow:0 12px 32px rgba(0,0,0,.28);
    border-left:5px solid #3b5bfd;transition:opacity .25s,transform .25s;pointer-events:none}
  #demo-cap.hide{opacity:0;transform:translateY(8px)}
  #demo-cap .k{font:700 11.5px/1 Inter,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#9fb0ff;margin-bottom:7px}
  #demo-cap .t{font:700 19px/1.25 Inter,sans-serif;margin-bottom:4px}
  #demo-cap .s{color:#d1d5db;font-size:14px}
  #demo-ring{position:fixed;z-index:2147483645;border:3px solid #ffb020;border-radius:10px;
    box-shadow:0 0 0 6px rgba(255,176,32,.28);pointer-events:none;transition:all .25s;opacity:0}
  #demo-cur{position:fixed;z-index:2147483647;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;
    background:rgba(59,91,253,.35);border:2px solid #3b5bfd;pointer-events:none;transition:transform .12s}
  #demo-cur.down{transform:scale(.7);background:rgba(59,91,253,.6)}`;
  function ensure() {
    if (!document.body || document.getElementById('demo-cap')) return;
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    const cap = document.createElement('div'); cap.id = 'demo-cap'; cap.className = 'hide';
    cap.innerHTML = '<div class="k"></div><div class="t"></div><div class="s"></div>';
    const ring = document.createElement('div'); ring.id = 'demo-ring';
    const cur = document.createElement('div'); cur.id = 'demo-cur';
    const p = JSON.parse(sessionStorage.getItem('demo-cur') || '[640,360]');
    cur.style.left = p[0] + 'px'; cur.style.top = p[1] + 'px';
    document.body.append(cap, ring, cur);
    const saved = sessionStorage.getItem('demo-caption');
    if (saved) window.__demoCaption(...JSON.parse(saved));
  }
  window.__demoCaption = (k, t, s, pos) => {
    sessionStorage.setItem('demo-caption', JSON.stringify([k, t, s, pos]));
    const cap = document.getElementById('demo-cap'); if (!cap) return;
    if (!t) { cap.className = 'hide'; return; }
    cap.querySelector('.k').textContent = k; cap.querySelector('.t').textContent = t;
    cap.querySelector('.s').textContent = s || '';
    cap.style.left = (pos && pos.left != null ? pos.left : 260) + 'px';
    cap.style.bottom = (pos && pos.bottom != null ? pos.bottom : 22) + 'px';
    cap.className = '';
  };
  window.__demoRing = (r) => {
    const ring = document.getElementById('demo-ring'); if (!ring) return;
    if (!r) { ring.style.opacity = 0; return; }
    const pad = 6;
    Object.assign(ring.style, {left: r.x - pad + 'px', top: r.y - pad + 'px',
      width: r.width + pad * 2 + 'px', height: r.height + pad * 2 + 'px', opacity: 1});
  };
  addEventListener('mousemove', e => {
    const c = document.getElementById('demo-cur'); if (!c) return;
    c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px';
    sessionStorage.setItem('demo-cur', JSON.stringify([e.clientX, e.clientY]));
  }, true);
  addEventListener('mousedown', () => document.getElementById('demo-cur')?.classList.add('down'), true);
  addEventListener('mouseup', () => document.getElementById('demo-cur')?.classList.remove('down'), true);
  new MutationObserver(ensure).observe(document, {childList: true, subtree: true});
  document.addEventListener('DOMContentLoaded', ensure);
})();
