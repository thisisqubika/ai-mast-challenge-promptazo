/* Tribuna Home — vanilla JS home feed.
   Seleccion, Upcoming, and Recap sections are loaded from the real API. */

// ── State ──────────────────────────────────────────────────────────────────
const state = { activeTab: 'inicio', activeCategory: 'fifa26' };

// ── Static data ─────────────────────────────────────────────────────────────
const categories = [
  { id: 'fifa26',   label: 'FIFA 26',   icon: 'ti ti-trophy' },
  { id: 'futbol',   label: 'Fútbol',    icon: 'ti ti-ball-football' },
  { id: 'musica',   label: 'Música',    icon: 'ti ti-music' },
  { id: 'shows',    label: 'Shows',     icon: 'ti ti-masks-theater' },
  { id: 'deportes', label: 'Deportes',  icon: 'ti ti-run' },
  { id: 'cultura',  label: 'Cultura',   icon: 'ti ti-palette' },
  { id: 'otros',    label: 'Otros',     icon: 'ti ti-sparkles' },
];

const worldCards = [
  { isLive: false, home: 'Brasil', homeFlag: '🇧🇷', away: 'França', awayFlag: '🇫🇷',
    kickoff: '18:00', statusText: 'en 45m', venue: 'Club House Alberdi', distance: '2.1km',
    amenities: [['🍺', 'Cervezas'], ['📺', 'Pantalla']] },
  { isLive: true, home: 'España', homeFlag: '🇪🇸', away: 'Alemania', awayFlag: '🇩🇪',
    score: '1 – 0', statusText: "LIVE 34'", venue: 'Bar Munich', distance: '1.8km',
    amenities: [['🍺', 'Cervezas'], ['🎶', 'DJ']] },
  { isLive: false, home: 'Portugal', homeFlag: '🇵🇹', away: 'Marruecos', awayFlag: '🇲🇦',
    kickoff: '22:00', statusText: 'en 2h 30m', venue: 'Roof Lounge', distance: '3km',
    amenities: [['🍷', 'Vinos'], ['📺', 'Pantalla']] },
];

// Recap cards — loaded from API; static array is a render-before-fetch placeholder
let recapCards = [];

// Events cached for live-bar registration logic
let _seleccionEvents = [];
let _upcomingEvents  = [];

const navIcons = {
  inicio:  '<svg width="23" height="23" viewBox="0 0 24 24" fill="none"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1v-9.5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  mapa:    '<svg width="23" height="23" viewBox="0 0 24 24" fill="none"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M9 4v14M15 6v14" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  crear:   '<svg width="23" height="23" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  eventos: '<svg width="23" height="23" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" stroke-width="2"/><path d="M3 9h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  perfil:  '<svg width="23" height="23" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/><path d="M4 21c0-4 3.5-6 8-6s8 2 8 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
};
const navTabs = [
  { id: 'inicio', label: 'Inicio' },
  { id: 'mapa', label: 'Mapa' },
  { id: 'crear', label: 'Crear' },
  { id: 'eventos', label: 'Mis eventos' },
  { id: 'perfil', label: 'Perfil' },
];

// ── Date / time helpers ──────────────────────────────────────────────────────
const _MONTHS = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];

function _fmtDate(iso) {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${_MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

function _fmtShortDate(iso) {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${_MONTHS[d.getUTCMonth()]}`;
}

function _fmtTime(iso) {
  const d = new Date(iso);
  return `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`;
}

function _fmtCountdown(iso) {
  const diffDays = Math.floor((new Date(iso) - Date.now()) / 86400000);
  if (diffDays < 0) return null;
  if (diffDays === 0) return 'Hoy';
  if (diffDays === 1) return 'Mañana';
  return `en ${diffDays} días`;
}

// ── Helpers ──────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const tags = (list) => `<div class="tags">${list.map(([icon, label]) =>
  `<div class="tag"><span>${icon}</span><span>${label}</span></div>`).join('')}</div>`;

const _AVATAR_COLORS = ['#7c3aed', '#0ea5e9', '#f59e0b', '#10b981', '#ef4444'];
function _miniAvatars(count) {
  const pairs = [['FA','#7c3aed'], ['RP','#0ea5e9'], ['SG','#f59e0b']];
  return pairs.slice(0, Math.min(count, 3))
    .map(([ini, bg]) => `<div class="mini-avatar" style="background:${bg}">${ini}</div>`)
    .join('');
}

// ── Renderers ────────────────────────────────────────────────────────────────
function renderCategories() {
  $('catTabs').innerHTML = categories.map((c) => `
    <button class="cat-tab${c.id === state.activeCategory ? ' is-active' : ''}" data-cat="${c.id}" type="button">
      <i class="${c.icon}"></i><span>${c.label}</span>
    </button>`).join('');
}

function renderSeleccion(events) {
  if (!events.length) {
    $('rowSeleccion').innerHTML = '<div style="padding:16px;color:var(--muted);font-size:12px">Sin partidos disponibles</div>';
    return;
  }
  $('rowSeleccion').innerHTML = events.map((e) => {
    const countdown = _fmtCountdown(e.kickoff_iso);
    const timeStr = _fmtTime(e.kickoff_iso);
    const matchLabel = countdown === 'Hoy' ? `Hoy · ${timeStr}` : `${_fmtShortDate(e.kickoff_iso)} · ${timeStr}`;
    const avatars = _miniAvatars(e.attendee_count);
    const attendLabel = e.attendee_count ? `${e.attendee_count} van a ir` : 'Sé el primero';
    return `
    <div class="card-sel" data-event-id="${e.id}" style="cursor:pointer">
      <div class="card-sel__match">
        <div class="card-sel__match-teams">${e.home_flag} ${e.home_team} vs ${e.away_flag} ${e.away_team}</div>
        <div class="card-sel__match-time">${matchLabel}</div>
      </div>
      <div class="card-sel__name">${e.venue_name}</div>
      <div class="card-sel__loc"><span>📍</span><span>${e.venue_distance || e.venue_address || ''}</span></div>
      ${tags(e.amenities)}
      <div class="card-sel__foot">
        <div class="attend">
          <div class="avatar-stack">${avatars}</div>
          <span class="attend__count">${attendLabel}</span>
        </div>
        <button class="btn-apuntar${!!localStorage.getItem('apuntado_'+e.id) ? ' is-apuntado' : ''}"
                type="button">${!!localStorage.getItem('apuntado_'+e.id) ? '✓ Apuntado' : 'Me apunto'}</button>
      </div>
    </div>`;
  }).join('');
}

function renderWorld() {
  $('rowWorld').innerHTML = worldCards.map((w) => {
    const center = w.isLive
      ? `<div class="score-col__score">${w.score}</div>
         <div class="live-flag">
           <div class="live-dot"><div class="live-dot__ring"></div><div class="live-dot__core"></div></div>
           <span class="live-flag__text">${w.statusText}</span>
         </div>`
      : `<div class="score-col__kickoff">${w.kickoff}</div>
         <div class="score-col__status">${w.statusText}</div>`;
    return `
    <div class="card-world${w.isLive ? ' is-live' : ''}">
      <div class="card-world__head">
        <div class="team"><div class="team__flag">${w.homeFlag}</div><div class="team__name">${w.home}</div></div>
        <div class="score-col">${center}</div>
        <div class="team"><div class="team__flag">${w.awayFlag}</div><div class="team__name">${w.away}</div></div>
      </div>
      <div class="card-world__body">
        <div class="card-world__venue">${w.venue} <span>· ${w.distance}</span></div>
        ${tags(w.amenities)}
        <button class="btn-link" type="button">Ver fan fests →</button>
      </div>
    </div>`;
  }).join('');
}

function renderRecap() {
  const pitch = `<svg width="120" height="50" viewBox="0 0 120 50" fill="none" class="card-recap__pitch"><path d="M0 50 Q15 30 30 40 Q45 22 60 34 Q75 16 90 32 Q105 24 120 36 L120 50Z" fill="#f1f5f9"/></svg>`;
  $('rowRecap').innerHTML = recapCards.map((r) => `
    <div class="card-recap">
      <div class="card-recap__hero">
        ${pitch}
        <div class="card-recap__vs">
          <div class="recap-flag recap-flag--arg">${r.homeFlag}</div>
          <div class="card-recap__vs-label">vs</div>
          <div class="recap-flag recap-flag--opp">${r.oppFlag}</div>
        </div>
      </div>
      <div class="card-recap__body">
        <div class="card-recap__result"
             style="cursor:pointer"
             data-recap-detail-id="${r.id}"
             data-recap-status="${r.status}">${r.result}</div>
        <div class="card-recap__stage">${r.stage}</div>
        <div class="divider"></div>
        <button class="card-recap__cronica" type="button" data-recap-event-id="${r.id}">✨ Ver crónica</button>
        <div class="card-recap__photos">📸 ${r.photos} fotos</div>
      </div>
    </div>`).join('');
}

function renderUpcoming(events) {
  if (!events.length) {
    $('rowUpcoming').innerHTML = '<div style="padding:16px;color:var(--muted);font-size:12px">Sin próximos eventos</div>';
    return;
  }
  $('rowUpcoming').innerHTML = events.map((u) => {
    const countdown = _fmtCountdown(u.kickoff_iso) || 'Próximamente';
    return `
    <div class="card-up" data-event-id="${u.id}" style="cursor:pointer">
      <div class="card-up__head">
        <div class="team"><div class="team__flag">${u.home_flag}</div><div class="team__name">${u.home_team}</div></div>
        <div class="when">
          <div class="when__date">${_fmtShortDate(u.kickoff_iso)}</div>
          <div class="when__kickoff">${_fmtTime(u.kickoff_iso)}</div>
          <div class="when__countdown">${countdown}</div>
        </div>
        <div class="team"><div class="team__flag">${u.away_flag}</div><div class="team__name">${u.away_team}</div></div>
      </div>
      <div class="card-up__body">
        <div class="card-up__venue">${u.venue_name}</div>
        <div class="card-up__loc"><span>📍</span><span>${u.venue_distance || u.venue_address || ''}</span></div>
        ${tags(u.amenities)}
        <div class="card-up__foot"><button class="btn-apuntar${!!localStorage.getItem('apuntado_'+u.id) ? ' is-apuntado' : ''}"
                type="button">${!!localStorage.getItem('apuntado_'+u.id) ? '✓ Apuntado' : 'Me apunto'}</button></div>
      </div>
    </div>`;
  }).join('');
}

function renderNav() {
  $('navTabs').innerHTML = navTabs.map((t) => `
    <button class="navtab${t.id === state.activeTab ? ' is-active' : ''}" data-tab="${t.id}" type="button">
      <div>${navIcons[t.id]}</div>
      <span>${t.label}</span>
      <div class="navtab__dot"></div>
    </button>`).join('');
}

// ── Registration helpers ──────────────────────────────────────────────────────
function apuntarseAlEvento(eventId) {
  if (localStorage.getItem(`apuntado_${eventId}`)) return;
  localStorage.setItem(`apuntado_${eventId}`, '1');
  document.querySelectorAll(`[data-event-id="${eventId}"] .btn-apuntar`).forEach(btn => {
    btn.textContent = '✓ Apuntado';
    btn.classList.add('is-apuntado');
  });
  // Increment attendance counter in the DOM and in cached event arrays
  document.querySelectorAll(`[data-event-id="${eventId}"] .attend__count`).forEach(el => {
    const current = parseInt(el.textContent) || 0;
    el.textContent = `${current + 1} van a ir`;
  });
  [_seleccionEvents, _upcomingEvents].forEach(arr => {
    const ev = arr.find(e => e.id === eventId);
    if (ev) ev.attendee_count = (ev.attendee_count || 0) + 1;
  });
  _updateLiveBar();
}

function _updateLiveBar() {
  const livebar = document.querySelector('.live-bar');
  if (!livebar) return;
  const allEvents = [..._seleccionEvents, ..._upcomingEvents];
  const registered = allEvents.find(e =>
    localStorage.getItem(`apuntado_${e.id}`) && e.status !== 'past'
  );
  if (registered) {
    const matchEl = livebar.querySelector('.live-bar__match');
    const labelEl = livebar.querySelector('.live-bar__label');
    if (matchEl) matchEl.textContent = `${registered.home_team} vs ${registered.away_team}`;
    if (labelEl) labelEl.textContent = registered.status === 'live' ? 'Partido en vivo' : 'Previa';
    livebar.dataset.eventId = registered.id;
    livebar.hidden = false;
  } else {
    livebar.hidden = true;
    delete livebar.dataset.eventId;
  }
}

// ── API loaders ───────────────────────────────────────────────────────────────
async function loadRecapCards() {
  try {
    const res = await fetch('http://localhost:8000/api/v1/events?status=past');
    if (!res.ok) throw new Error('api error');
    const events = await res.json();
    recapCards = events.map((e) => ({
      id: e.id,
      status: e.status,
      homeFlag: e.home_flag,
      oppFlag: e.away_flag,
      result: `${e.home_abbr} ${e.home_score ?? '?'}–${e.away_score ?? '?'} ${e.away_abbr}`,
      stage: _fmtDate(e.kickoff_iso),
      photos: String(e.photo_count),
    }));
    renderRecap();
  } catch (_) {
    // backend unavailable — section stays empty
  }
}

async function loadSeleccionCards() {
  try {
    const res = await fetch('http://localhost:8000/api/v1/events');
    if (!res.ok) throw new Error('api error');
    const events = await res.json();
    const selEvents = events
      .filter((e) => (e.home_team === 'Argentina' || e.away_team === 'Argentina') && e.status !== 'past')
      .sort((a, b) => new Date(a.kickoff_iso) - new Date(b.kickoff_iso));
    const subtitle = $('seleccionSubtitle');
    if (subtitle && selEvents.length) {
      const first = selEvents[0];
      const countdown = _fmtCountdown(first.kickoff_iso);
      const timeStr = _fmtTime(first.kickoff_iso);
      const label = countdown === 'Hoy' ? `Hoy ${timeStr}` : `${_fmtShortDate(first.kickoff_iso)} · ${timeStr}`;
      subtitle.textContent = `${first.home_team} vs ${first.away_team} · ${label}`;
    }
    _seleccionEvents = selEvents;
    renderSeleccion(selEvents);
    _updateLiveBar();
  } catch (_) {
    $('rowSeleccion').innerHTML = '';
  }
}

async function loadUpcomingCards() {
  try {
    const res = await fetch('http://localhost:8000/api/v1/events?status=future');
    if (!res.ok) throw new Error('api error');
    const events = await res.json();
    events.sort((a, b) => new Date(a.kickoff_iso) - new Date(b.kickoff_iso));
    _upcomingEvents = events;
    renderUpcoming(events);
    _updateLiveBar();
  } catch (_) {
    $('rowUpcoming').innerHTML = '';
  }
}

// ── Wire up ──────────────────────────────────────────────────────────────────
$('catTabs').addEventListener('click', (e) => {
  const btn = e.target.closest('[data-cat]');
  if (!btn) return;
  state.activeCategory = btn.dataset.cat;
  renderCategories();
});

$('navTabs').addEventListener('click', (e) => {
  const btn = e.target.closest('[data-tab]');
  if (!btn) return;
  if (btn.dataset.tab === 'crear' && typeof window.navigateToCreateEvent === 'function') {
    window.navigateToCreateEvent();
    return;
  }
  state.activeTab = btn.dataset.tab;
  renderNav();
});

$('rowSeleccion').addEventListener('click', (e) => {
  if (e.target.closest('.btn-apuntar')) {
    const card = e.target.closest('[data-event-id]');
    if (card) apuntarseAlEvento(card.dataset.eventId);
    return;
  }
  const card = e.target.closest('[data-event-id]');
  if (card && typeof window.navigateToEventDetail === 'function') {
    window.navigateToEventDetail({ id: card.dataset.eventId });
  }
});

$('rowUpcoming').addEventListener('click', (e) => {
  if (e.target.closest('.btn-apuntar')) {
    const card = e.target.closest('[data-event-id]');
    if (card) apuntarseAlEvento(card.dataset.eventId);
    return;
  }
  const card = e.target.closest('[data-event-id]');
  if (card && typeof window.navigateToEventDetail === 'function') {
    window.navigateToEventDetail({ id: card.dataset.eventId });
  }
});

renderCategories();
renderWorld();
renderNav();

// Async sections
loadRecapCards();
loadSeleccionCards();
loadUpcomingCards();

$('rowRecap').addEventListener('click', (e) => {
  const resultEl = e.target.closest('[data-recap-detail-id]');
  if (resultEl && typeof window.navigateToEventDetail === 'function') {
    window.navigateToEventDetail({ id: resultEl.dataset.recapDetailId, status: resultEl.dataset.recapStatus });
    return;
  }
  const btn = e.target.closest('[data-recap-event-id]');
  if (btn && typeof window.navigateToRecap === 'function') {
    window.navigateToRecap(btn.dataset.recapEventId);
  }
});

const liveCta = document.querySelector('.live-bar__cta');
if (liveCta) {
  liveCta.addEventListener('click', () => {
    if (typeof window.performEstoyAqui === 'function') {
      window.performEstoyAqui();
    }
  });
}
