/* Tribuna Home — vanilla JS home feed.
   Seleccion, Upcoming, and Recap sections are loaded from the real API. */

// ── State ──────────────────────────────────────────────────────────────────
const state = { activeTab: 'inicio', activeCategory: 'fifa26', searchQuery: '' };

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
// Nav tab swaps between Create (home screen) and Home (detail screens)
let navTabs = [{ id: 'crear', label: 'Create' }];

function _setNavContext(ctx) {
  navTabs = ctx === 'home'
    ? [{ id: 'crear', label: 'Create' }]
    : [{ id: 'inicio', label: 'Home' }];
  renderNav();
}
window._setNavContext = _setNavContext;

// ── Date / time helpers ──────────────────────────────────────────────────────
const _MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

// Ensure the ISO string is treated as UTC when no timezone designator is present.
// "2026-06-22T14:00" → "2026-06-22T14:00Z"; strings already ending in Z or ±HH:MM pass through.
function _normIso(iso) {
  if (!iso) return iso;
  return /Z$|[+-]\d{2}:\d{2}$/.test(iso) ? iso : iso + 'Z';
}

function _fmtDate(iso) {
  const d = new Date(_normIso(iso));
  return `${d.getUTCDate()} ${_MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

function _fmtShortDate(iso) {
  const d = new Date(_normIso(iso));
  return `${d.getUTCDate()} ${_MONTHS[d.getUTCMonth()]}`;
}

function _fmtTime(iso) {
  const d = new Date(_normIso(iso));
  return `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`;
}

function _fmtCountdown(iso) {
  const diffDays = Math.floor((new Date(_normIso(iso)) - Date.now()) / 86400000);
  if (diffDays < 0) return null;
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  return `in ${diffDays} days`;
}

// ── Live clock ───────────────────────────────────────────────────────────────
function _updateClock() {
  const el = document.getElementById('statusTime');
  if (!el) return;
  const now = new Date();
  el.textContent = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
}
_updateClock();
setInterval(_updateClock, 10000);

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
    $('rowSeleccion').innerHTML = '<div style="padding:16px;color:var(--muted);font-size:12px">No matches available</div>';
    return;
  }
  $('rowSeleccion').innerHTML = events.map((e) => {
    const countdown = _fmtCountdown(e.kickoff_iso);
    const timeStr = _fmtTime(e.kickoff_iso);
    const matchLabel = countdown === 'Today' ? `Today · ${timeStr}` : `${_fmtShortDate(e.kickoff_iso)} · ${timeStr}`;
    const avatars = _miniAvatars(e.attendee_count);
    const attendLabel = e.attendee_count ? `${e.attendee_count} going` : 'Be the first';
    return `
    <div class="card-sel" data-event-id="${e.id}" data-kickoff-iso="${e.kickoff_iso || ''}" style="cursor:pointer">
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
                type="button">${!!localStorage.getItem('apuntado_'+e.id) ? '✓ Joined' : 'Join'}</button>
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
        <button class="card-recap__cronica" type="button" data-recap-event-id="${r.id}">✨ See recap</button>
        <div class="card-recap__photos">📸 ${r.photos} photos</div>
      </div>
    </div>`).join('');
}

function renderUpcoming(events) {
  if (!events.length) {
    $('rowUpcoming').innerHTML = '<div style="padding:16px;color:var(--muted);font-size:12px">No upcoming events</div>';
    return;
  }
  $('rowUpcoming').innerHTML = events.map((u) => {
    const countdown = _fmtCountdown(u.kickoff_iso) || 'Coming soon';
    return `
    <div class="card-up" data-event-id="${u.id}" data-kickoff-iso="${u.kickoff_iso || ''}" style="cursor:pointer">
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

function renderMisEventos() {
  const registered = [..._seleccionEvents, ..._upcomingEvents].filter(
    (e) => localStorage.getItem(`apuntado_${e.id}`)
  );
  const track = $('misEventosTrack');
  if (!track) return;
  if (!registered.length) {
    track.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;gap:14px;padding:40px 0;text-align:center">
        <div style="font-size:48px">🎉</div>
        <div style="font-size:15px;font-weight:700;color:var(--ink)">You haven't joined any fan fests yet</div>
        <div style="font-size:13px;color:var(--muted)">Explore events and tap "Join"</div>
      </div>`;
    return;
  }
  track.innerHTML = registered.map((e) => {
    const countdown = _fmtCountdown(e.kickoff_iso);
    const timeStr = _fmtTime(e.kickoff_iso);
    const matchLabel = countdown === 'Today' ? `Today · ${timeStr}` : `${_fmtShortDate(e.kickoff_iso)} · ${timeStr}`;
    return `
    <div class="card-sel" data-event-id="${e.id}" data-kickoff-iso="${e.kickoff_iso || ''}" style="cursor:pointer;margin-bottom:12px">
      <div class="card-sel__match">
        <div class="card-sel__match-teams">${e.home_flag} ${e.home_team} vs ${e.away_flag} ${e.away_team}</div>
        <div class="card-sel__match-time">${matchLabel}</div>
      </div>
      <div class="card-sel__name">${e.venue_name}</div>
      <div class="card-sel__loc"><span>📍</span><span>${e.venue_distance || e.venue_address || ''}</span></div>
      ${tags(e.amenities)}
      <div class="card-sel__foot">
        <div class="attend"><span class="attend__count">✓ Joined</span></div>
      </div>
    </div>`;
  }).join('');
}

// ── Registration helpers ──────────────────────────────────────────────────────
function apuntarseAlEvento(eventId) {
  if (localStorage.getItem(`apuntado_${eventId}`)) return;
  localStorage.setItem(`apuntado_${eventId}`, '1');
  document.querySelectorAll(`[data-event-id="${eventId}"] .btn-apuntar`).forEach(btn => {
    btn.textContent = '✓ Joined';
    btn.classList.add('is-apuntado');
  });
  // Increment attendance counter in the DOM and in cached event arrays
  document.querySelectorAll(`[data-event-id="${eventId}"] .attend__count`).forEach(el => {
    const current = parseInt(el.textContent) || 0;
    el.textContent = `${current + 1} going`;
  });
  [_seleccionEvents, _upcomingEvents].forEach(arr => {
    const ev = arr.find(e => e.id === eventId);
    if (ev) ev.attendee_count = (ev.attendee_count || 0) + 1;
  });
  _updateLiveBar();
}

function _isToday(iso) {
  if (!iso) return false;
  const today = new Date();
  const todayStr = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, '0'),
    String(today.getDate()).padStart(2, '0'),
  ].join('-');
  return iso.startsWith(todayStr);
}

function _updateLiveBar() {
  const livebar = document.querySelector('.live-bar');
  if (!livebar) return;
  const allEvents = [..._seleccionEvents, ..._upcomingEvents];
  const registered = allEvents.find(e =>
    localStorage.getItem(`apuntado_${e.id}`) &&
    (e.status === 'pre' || e.status === 'live') &&
    _isToday(e.kickoff_iso)
  );
  if (registered) {
    const matchEl = livebar.querySelector('.live-bar__match');
    const labelEl = livebar.querySelector('.live-bar__label');
    if (matchEl) matchEl.textContent = `${registered.home_team} vs ${registered.away_team}`;
    if (labelEl) labelEl.textContent = registered.status === 'live' ? 'Live Match' : 'Pre-match';
    livebar.dataset.eventId = registered.id;
    livebar.hidden = false;
  } else {
    livebar.hidden = true;
    delete livebar.dataset.eventId;
  }
}

// ── Search filter ────────────────────────────────────────────────────────────
function _filterEvents(events, query) {
  if (!query) return events;
  const q = query.toLowerCase();
  return events.filter(e =>
    [e.venue_name, e.home_team, e.away_team, e.venue_address]
      .join(' ').toLowerCase().includes(q)
  );
}

// ── API loaders ───────────────────────────────────────────────────────────────
async function loadRecapCards() {
  try {
    const res = await fetch('http://localhost:8000/api/v1/events?status=past');
    if (!res.ok) throw new Error('api error');
    const events = await res.json();
    events.sort((a, b) => new Date(b.kickoff_iso) - new Date(a.kickoff_iso));
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
      const label = countdown === 'Today' ? `Today ${timeStr}` : `${_fmtShortDate(first.kickoff_iso)} · ${timeStr}`;
      subtitle.textContent = `${first.home_team} vs ${first.away_team} · ${label}`;
    }
    _seleccionEvents = selEvents;
    renderSeleccion(_filterEvents(selEvents, state.searchQuery));
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
    renderUpcoming(_filterEvents(events, state.searchQuery));
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

function _switchHomeTab(tab) {
  const homeViews = ['homeView', 'mapaView', 'misEventosView'];
  homeViews.forEach((id) => { const el = $(id); if (el) el.hidden = true; });
  if (tab === 'mapa') {
    $('mapaView').hidden = false;
  } else if (tab === 'eventos') {
    renderMisEventos();
    $('misEventosView').hidden = false;
  } else {
    $('homeView').hidden = false;
  }
}

$('navTabs').addEventListener('click', (e) => {
  const btn = e.target.closest('[data-tab]');
  if (!btn) return;
  if (btn.dataset.tab === 'inicio') {
    if (typeof window.navigateToHome === 'function') window.navigateToHome();
    else _switchHomeTab('inicio');
    return;
  }
  if (btn.dataset.tab === 'crear') {
    if (typeof window.navigateToCreateEvent === 'function') window.navigateToCreateEvent();
    return;
  }
  state.activeTab = btn.dataset.tab;
  renderNav();
  _switchHomeTab(btn.dataset.tab);
});

$('rowSeleccion').addEventListener('click', (e) => {
  if (e.target.closest('.btn-apuntar')) {
    const card = e.target.closest('[data-event-id]');
    if (card) apuntarseAlEvento(card.dataset.eventId);
    return;
  }
  const card = e.target.closest('[data-event-id]');
  if (card && typeof window.navigateToEventDetail === 'function') {
    window.navigateToEventDetail({ id: card.dataset.eventId, kickoff_iso: card.dataset.kickoffIso });
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
    window.navigateToEventDetail({ id: card.dataset.eventId, kickoff_iso: card.dataset.kickoffIso });
  }
});

renderCategories();
renderNav();

// Async sections
loadRecapCards();
loadSeleccionCards();
loadUpcomingCards();

$('rowRecap').addEventListener('click', (e) => {
  const resultEl = e.target.closest('[data-recap-detail-id]');
  if (resultEl && typeof window.navigateToRecap === 'function') {
    window.navigateToRecap(resultEl.dataset.recapDetailId);
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

window._updateLiveBar = _updateLiveBar;

const _searchInput = document.getElementById('searchInput');
if (_searchInput) {
  _searchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.trim();
    renderSeleccion(_filterEvents(_seleccionEvents, state.searchQuery));
    renderUpcoming(_filterEvents(_upcomingEvents, state.searchQuery));
  });
}
