/* Tribuna Home — vanilla port of Tribuna Home.dc.html
   Mock data is inline (Feature 01: discovery feed, mocked dataset). */

// ── State ──────────────────────────────────────────────────────────────────
const state = { activeTab: 'inicio', activeCategory: 'fifa26' };

// ── Data ───────────────────────────────────────────────────────────────────
const categories = [
  { id: 'fifa26',   label: 'FIFA 26',   icon: 'ti ti-trophy' },
  { id: 'futbol',   label: 'Fútbol',    icon: 'ti ti-ball-football' },
  { id: 'musica',   label: 'Música',    icon: 'ti ti-music' },
  { id: 'shows',    label: 'Shows',     icon: 'ti ti-masks-theater' },
  { id: 'deportes', label: 'Deportes',  icon: 'ti ti-run' },
  { id: 'cultura',  label: 'Cultura',   icon: 'ti ti-palette' },
  { id: 'otros',    label: 'Otros',     icon: 'ti ti-sparkles' },
];

const seleccionVenues = [
  { name: 'La Mona Sports Bar', distance: '400m · Güemes',
    amenities: [['🍔', 'Foodtruck'], ['🐾', 'Pet-friendly'], ['📺', 'Pantalla']], attending: '34 van a ir' },
  { name: 'Terraza El Cerro', distance: '1.2km · Nueva Córdoba',
    amenities: [['🍺', 'Cervezas'], ['🎵', 'Música'], ['📺', 'Pantalla']], attending: '21 van a ir' },
  { name: 'Plaza San Martín', distance: '800m · Centro',
    amenities: [['📺', 'Pantalla gigante'], ['🍔', 'Foodtruck']], attending: '56 van a ir' },
];
const seleccionAvatars = [['JL', '#7c3aed'], ['RP', '#0ea5e9'], ['SG', '#f59e0b']];

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

const recapCards = [
  { result: 'ARG 3–3 FRA', stage: 'Final · 18 dic 2022', photos: '247', oppFlag: '🇫🇷' },
  { result: 'ARG 2–0 AUS', stage: 'Octavos · 3 dic 2022', photos: '184', oppFlag: '🇦🇺' },
  { result: 'ARG 3–0 CRO', stage: 'Semis · 13 dic 2022', photos: '312', oppFlag: '🇭🇷' },
];

const upcomingCards = [
  { home: 'España', homeFlag: '🇪🇸', away: 'Alemania', awayFlag: '🇩🇪',
    date: '24 jun', kickoff: '18:00', countdown: 'en 2 días', venue: 'Stadium Bar Palermo', distance: '2.3km',
    amenities: [['📺', 'Pantalla'], ['🍺', 'Cervezas']] },
  { home: 'Inglaterra', homeFlag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', away: 'Francia', awayFlag: '🇫🇷',
    date: '25 jun', kickoff: '21:00', countdown: 'en 3 días', venue: 'Fan Fest Parque Sarmiento', distance: '1.5km',
    amenities: [['🎶', 'DJ'], ['🍔', 'Foodtruck']] },
  { home: 'Argentina', homeFlag: '🇦🇷', away: 'Polonia', awayFlag: '🇵🇱',
    date: '26 jun', kickoff: '18:00', countdown: 'en 4 días', venue: 'La Mona Sports Bar', distance: '400m',
    amenities: [['🍔', 'Foodtruck'], ['🐾', 'Pet-friendly']] },
];

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

// ── Helpers ──────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const tags = (list) => `<div class="tags">${list.map(([icon, label]) =>
  `<div class="tag"><span>${icon}</span><span>${label}</span></div>`).join('')}</div>`;

// ── Renderers ────────────────────────────────────────────────────────────────
function renderCategories() {
  $('catTabs').innerHTML = categories.map((c) => `
    <button class="cat-tab${c.id === state.activeCategory ? ' is-active' : ''}" data-cat="${c.id}" type="button">
      <i class="${c.icon}"></i><span>${c.label}</span>
    </button>`).join('');
}

function renderSeleccion() {
  const avatars = seleccionAvatars.map(([ini, bg]) =>
    `<div class="mini-avatar" style="background:${bg}">${ini}</div>`).join('');
  $('rowSeleccion').innerHTML = seleccionVenues.map((v) => `
    <div class="card-sel">
      <div class="card-sel__match">
        <div class="card-sel__match-teams">🇦🇷 Argentina vs 🇲🇽 México</div>
        <div class="card-sel__match-time">Hoy · 21:00</div>
      </div>
      <div class="card-sel__name">${v.name}</div>
      <div class="card-sel__loc"><span>📍</span><span>${v.distance}</span></div>
      ${tags(v.amenities)}
      <div class="card-sel__foot">
        <div class="attend">
          <div class="avatar-stack">${avatars}</div>
          <span class="attend__count">${v.attending}</span>
        </div>
        <button class="btn-apuntar" type="button">Me apunto</button>
      </div>
    </div>`).join('');
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
          <div class="recap-flag recap-flag--arg">🇦🇷</div>
          <div class="card-recap__vs-label">vs</div>
          <div class="recap-flag recap-flag--opp">${r.oppFlag}</div>
        </div>
      </div>
      <div class="card-recap__body">
        <div class="card-recap__result">${r.result}</div>
        <div class="card-recap__stage">${r.stage}</div>
        <div class="divider"></div>
        <div class="card-recap__cronica">✨ Ver crónica</div>
        <div class="card-recap__photos">📸 ${r.photos} fotos</div>
      </div>
    </div>`).join('');
}

function renderUpcoming() {
  $('rowUpcoming').innerHTML = upcomingCards.map((u) => `
    <div class="card-up">
      <div class="card-up__head">
        <div class="team"><div class="team__flag">${u.homeFlag}</div><div class="team__name">${u.home}</div></div>
        <div class="when">
          <div class="when__date">${u.date}</div>
          <div class="when__kickoff">${u.kickoff}</div>
          <div class="when__countdown">${u.countdown}</div>
        </div>
        <div class="team"><div class="team__flag">${u.awayFlag}</div><div class="team__name">${u.away}</div></div>
      </div>
      <div class="card-up__body">
        <div class="card-up__venue">${u.venue}</div>
        <div class="card-up__loc"><span>📍</span><span>${u.distance}</span></div>
        ${tags(u.amenities)}
        <div class="card-up__foot"><button class="btn-apuntar" type="button">Me apunto</button></div>
      </div>
    </div>`).join('');
}

function renderNav() {
  $('navTabs').innerHTML = navTabs.map((t) => `
    <button class="navtab${t.id === state.activeTab ? ' is-active' : ''}" data-tab="${t.id}" type="button">
      <div>${navIcons[t.id]}</div>
      <span>${t.label}</span>
      <div class="navtab__dot"></div>
    </button>`).join('');
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
  state.activeTab = btn.dataset.tab;
  renderNav();
});

renderCategories();
renderSeleccion();
renderWorld();
renderRecap();
renderUpcoming();
renderNav();
