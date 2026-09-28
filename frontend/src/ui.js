export const icons = {
  home: '<svg viewBox="0 0 24 24"><path d="M3 11 12 4l9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>',
  book: '<svg viewBox="0 0 24 24"><path d="M4 5a3 3 0 0 1 3-3h5v17H7a3 3 0 0 0-3 3zM20 5a3 3 0 0 0-3-3h-5v17h5a3 3 0 0 1 3 3z"/></svg>',
  file: '<svg viewBox="0 0 24 24"><path d="M6 2h8l4 4v16H6zM14 2v5h5"/></svg>',
  chat: '<svg viewBox="0 0 24 24"><path d="M4 4h16v12H8l-4 4z"/></svg>',
  quiz: '<svg viewBox="0 0 24 24"><path d="M9 6h10M9 12h10M9 18h6M4 6h.01M4 12h.01M4 18h.01"/></svg>',
  cards: '<svg viewBox="0 0 24 24"><path d="m5 4 13-2 2 14-13 2zM4 7l-2 1 4 14 13-4"/></svg>',
  plan: '<svg viewBox="0 0 24 24"><path d="M5 3v3M19 3v3M3 8h18v13H3zM7 12h4M7 16h7"/></svg>',
  chart: '<svg viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',
  spark: '<svg viewBox="0 0 24 24"><path d="m12 2 1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg>',
  globe: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></svg>',
  bell: '<svg viewBox="0 0 24 24"><path d="M6 9a6 6 0 0 1 12 0v5l2 3H4l2-3zM10 20h4"/></svg>',
  download: '<svg viewBox="0 0 24 24"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>',
  user: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
  menu: '<svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
  plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  close: '<svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>',
  arrow: '<svg viewBox="0 0 24 24"><path d="M5 12h14M14 7l5 5-5 5"/></svg>',
  check: '<svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14"/></svg>',
};

export function icon(name, cls='') {
  return `<span class="icon ${cls}">${icons[name] || icons.spark}</span>`;
}

export function esc(value='') {
  return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}

export function fmtDate(value, withTime=false) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return esc(value);
  return new Intl.DateTimeFormat('vi-VN', withTime ? { dateStyle:'medium', timeStyle:'short' } : { dateStyle:'medium' }).format(d);
}

export function fmtBytes(bytes) {
  const n = Number(bytes || 0);
  if (!n) return '0 B';
  const units = ['B','KB','MB','GB'];
  const i = Math.min(Math.floor(Math.log(n)/Math.log(1024)), units.length-1);
  return `${(n/1024**i).toFixed(i ? 1 : 0)} ${units[i]}`;
}

export function toast(message, type='info', timeout=3600) {
  const root = document.getElementById('toast-root');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<div class="toast-dot"></div><div>${esc(message)}</div>`;
  root.appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 260); }, timeout);
}

export function modal({ title, body, actions = '', wide=false }) {
  const root = document.getElementById('modal-root');
  root.innerHTML = `<div class="modal-backdrop" data-modal-close><div class="modal ${wide?'modal-wide':''}" role="dialog" aria-modal="true" aria-label="${esc(title)}" onclick="event.stopPropagation()"><div class="modal-head"><div><span class="eyebrow">Smart Study</span><h2>${esc(title)}</h2></div><button class="icon-btn" data-modal-close>${icon('close')}</button></div><div class="modal-body">${body}</div>${actions?`<div class="modal-actions">${actions}</div>`:''}</div></div>`;
  root.querySelectorAll('[data-modal-close]').forEach(el => el.addEventListener('click', () => root.innerHTML=''));
  requestAnimationFrame(() => root.querySelector('.modal-backdrop')?.classList.add('show'));
  return root;
}

export function closeModal() { document.getElementById('modal-root').innerHTML=''; }

export function button(label, {variant='primary', iconName=null, attrs='', cls=''}={}) {
  return `<button class="btn btn-${variant} ${cls}" ${attrs}>${iconName?icon(iconName):''}<span>${esc(label)}</span></button>`;
}

export function badge(text, tone='neutral') {
  return `<span class="badge badge-${tone}">${esc(text)}</span>`;
}

export function emptyState(title, text, cta='') {
  return `<div class="empty-state reveal"><div class="empty-planet"><span></span></div><h3>${esc(title)}</h3><p>${esc(text)}</p>${cta}</div>`;
}

export function skeletonCards(n=3) {
  return `<div class="card-grid">${Array.from({length:n},()=>`<div class="surface skeleton-card"><div class="skeleton line sm"></div><div class="skeleton line lg"></div><div class="skeleton line"></div><div class="skeleton line med"></div></div>`).join('')}</div>`;
}

export function setBusy(el, busy=true, label='Đang xử lý…') {
  if (!el) return;
  if (busy) {
    el.dataset.original = el.innerHTML;
    el.disabled = true;
    el.innerHTML = `<span class="mini-spinner"></span><span>${esc(label)}</span>`;
  } else {
    el.disabled = false;
    if (el.dataset.original) el.innerHTML = el.dataset.original;
  }
}

export function revealElements(root=document) {
  const items = [...root.querySelectorAll('.reveal:not(.revealed)')];
  if (!('IntersectionObserver' in window)) { items.forEach(x=>x.classList.add('revealed')); return; }
  const io = new IntersectionObserver(entries => entries.forEach(e => { if(e.isIntersecting){ e.target.classList.add('revealed'); io.unobserve(e.target); } }), {threshold:.08});
  items.forEach(x=>io.observe(x));
}

export function initTilt(root=document) {
  root.querySelectorAll('[data-tilt]').forEach(card => {
    if (card.dataset.tiltBound) return;
    card.dataset.tiltBound = '1';
    card.addEventListener('pointermove', e => {
      if (matchMedia('(pointer: coarse)').matches) return;
      const r = card.getBoundingClientRect();
      const x = (e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
      card.style.transform = `perspective(900px) rotateX(${-y*5}deg) rotateY(${x*6}deg) translateY(-3px)`;
    });
    card.addEventListener('pointerleave', ()=> card.style.transform='');
  });
}
