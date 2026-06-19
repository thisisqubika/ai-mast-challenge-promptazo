/* Event Detail (Previa) — FEST-05
   Vanilla port of Tribuna Event Detail.dc.html (Previa state).
   Mock data is inline; prediction/upload calls are mocked until backends land. */

// ── Mock data ─────────────────────────────────────────────────────────────────
const edEvent = {
  id: 'event_001',
  venueName: 'La Mona Sports Bar',
  venueDistance: '400m · Güemes',
  attending: '47 van a ir',
  amenities: [
    ['🍔', 'Foodtruck'], ['🐾', 'Pet-friendly'], ['📺', 'Pantalla grande'],
    ['🍺', 'Cervezas'], ['🎵', 'Música en vivo'],
  ],
  match: {
    home: 'Argentina', homeFlag: '🇦🇷',
    away: 'México',    awayFlag: '🇲🇽',
    competition: 'FIFA World Cup 2026 · Grupo C · Jornada 2',
    countdownLabel: 'Comienza en 10 min',
  },
};

const hypePosts = [
  {
    type: 'photo',
    handle: '@juancruz_arg', initials: 'JC', avatarColor: '#7c3aed',
    timeAgo: 'hace 5 min',
    caption: '¡Llegando al fan fest! El ambiente está increíble 🔥🇦🇷',
    likes: 24, comments: 3,
  },
  {
    type: 'video',
    handle: '@rp_mati', initials: 'RP', avatarColor: '#0ea5e9',
    timeAgo: 'hace 12 min',
    caption: 'El pantallón ya está listo 📺⚡',
    duration: '0:28', likes: 61, comments: 8,
  },
  {
    type: 'text',
    handle: '@sofiaG', initials: 'SG', avatarColor: '#f59e0b',
    timeAgo: 'hace 18 min',
    caption: 'Alguien más yendo desde Nueva Córdoba? Busco con quien ir 🙋‍♀️',
    likes: null, comments: 5,
  },
];

// ── State ─────────────────────────────────────────────────────────────────────
const edState = {
  showPredict: false,
  homeScore: 0,
  awayScore: 0,
  predictSent: false,
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const $ed = (id) => document.getElementById(id);
const edChip = (icon, label) =>
  `<div class="tag"><span>${icon}</span><span>${label}</span></div>`;

// ── Renderers ─────────────────────────────────────────────────────────────────
function renderBackRow(event) {
  return `
    <div class="ed-back">
      <button class="ed-back__btn" id="edBackBtn" type="button" aria-label="Volver">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2.2"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="ed-back__venue">${event.venueName}</span>
    </div>`;
}

function renderMatchHeader(match) {
  return `
    <div class="ed-match">
      <div class="ed-match__status">
        <div class="ed-match__previa-pill">PREVIA</div>
      </div>
      <div class="ed-match__teams">
        <div class="ed-match__team">
          <div class="ed-match__team-flag">${match.homeFlag}</div>
          <div class="ed-match__team-name">${match.home}</div>
        </div>
        <div class="ed-match__score">– : –</div>
        <div class="ed-match__team">
          <div class="ed-match__team-flag">${match.awayFlag}</div>
          <div class="ed-match__team-name">${match.away}</div>
        </div>
      </div>
      <div class="ed-match__countdown">⏱ ${match.countdownLabel}</div>
      <div class="ed-match__competition">${match.competition}</div>
    </div>`;
}

function renderEventInfo(event) {
  const chips = event.amenities.map(([i, l]) => edChip(i, l)).join('');
  return `
    <div class="ed-info">
      <div class="ed-info__venue">${event.venueName}</div>
      <div class="ed-info__loc"><span>📍</span><span>${event.venueDistance}</span></div>
      <div class="ed-info__attending">👥 ${event.attending}</div>
      <div class="ed-info__chips">${chips}</div>
    </div>`;
}

function renderActionButtons() {
  const predictOpen = edState.showPredict && !edState.predictSent;
  return `
    <div class="ed-actions">
      <button class="ed-btn ed-btn--upload" type="button" disabled aria-disabled="true">
        📷 Subir foto
      </button>
      <button class="ed-btn ed-btn--predict${predictOpen ? ' is-open' : ''}"
              id="edPredictBtn" type="button">
        ${predictOpen ? '✕ Cerrar' : '🎯 Predecir'}
      </button>
    </div>`;
}

function renderPredictPanel() {
  if (edState.predictSent) {
    return `
      <div class="ed-predict-confirmed">
        <span class="ed-predict-confirmed__icon">✅</span>
        <span class="ed-predict-confirmed__text">
          Predicción enviada · ${edEvent.match.home} ${edState.homeScore} – ${edState.awayScore} ${edEvent.match.away}
        </span>
      </div>`;
  }
  if (!edState.showPredict) return '';
  return `
    <div class="ed-predict-panel" id="edPredictPanel">
      <div class="ed-predict__title">Tu predicción</div>
      <div class="ed-predict__steppers">
        <div class="ed-predict__team">
          <div class="ed-predict__team-label">ARG</div>
          <div class="ed-predict__stepper">
            <button class="ed-predict__step-btn" data-step="home" data-dir="-1" type="button">−</button>
            <div class="ed-predict__val">${edState.homeScore}</div>
            <button class="ed-predict__step-btn" data-step="home" data-dir="1" type="button">+</button>
          </div>
        </div>
        <div class="ed-predict__sep">–</div>
        <div class="ed-predict__team">
          <div class="ed-predict__team-label">MEX</div>
          <div class="ed-predict__stepper">
            <button class="ed-predict__step-btn" data-step="away" data-dir="-1" type="button">−</button>
            <div class="ed-predict__val">${edState.awayScore}</div>
            <button class="ed-predict__step-btn" data-step="away" data-dir="1" type="button">+</button>
          </div>
        </div>
      </div>
      <button class="ed-predict__confirm" id="edConfirmBtn" type="button">
        Confirmar predicción →
      </button>
    </div>`;
}

function renderHypePost(post) {
  let mediaHtml = '';
  if (post.type === 'photo') {
    mediaHtml = `<div class="hype-post__media"><span class="hype-post__media-icon">🖼️</span></div>`;
  } else if (post.type === 'video') {
    mediaHtml = `
      <div class="hype-post__media">
        <span class="hype-post__media-icon">▶️</span>
        <span class="hype-post__duration">${post.duration}</span>
      </div>`;
  }
  const likeCount  = post.likes    != null ? `<span class="hype-post__action-count">${post.likes}</span>`    : '';
  const commentCount = post.comments ? `<span class="hype-post__action-count">${post.comments}</span>` : '';
  return `
    <div class="hype-post">
      <div class="hype-post__header">
        <div class="hype-post__avatar" style="background:${post.avatarColor}">${post.initials}</div>
        <div class="hype-post__meta">
          <div class="hype-post__handle">${post.handle}</div>
          <div class="hype-post__time">${post.timeAgo}</div>
        </div>
      </div>
      ${mediaHtml}
      <div class="hype-post__caption">${post.caption}</div>
      <div class="hype-post__actions">
        <button class="hype-post__action" type="button">
          <span class="hype-post__action-icon">❤️</span>${likeCount}
        </button>
        <button class="hype-post__action" type="button">
          <span class="hype-post__action-icon">💬</span>${commentCount}
        </button>
        <span class="hype-post__action-sep"></span>
        <button class="hype-post__action" type="button">
          <span class="hype-post__action-icon">↗️</span>
        </button>
      </div>
    </div>`;
}

function renderEventDetail() {
  const container = $ed('eventDetailView');
  if (!container) return;
  container.innerHTML =
    renderBackRow(edEvent) +
    renderMatchHeader(edEvent.match) +
    renderEventInfo(edEvent) +
    renderActionButtons() +
    renderPredictPanel() +
    `<div class="ed-divider">
       <div class="ed-divider__line"></div>
       <div class="ed-divider__label">Previa</div>
       <div class="ed-divider__line"></div>
     </div>` +
    hypePosts.map(renderHypePost).join('') +
    `<div class="ed-empty-state">
       <div class="ed-empty-state__icon">⚽</div>
       <div class="ed-empty-state__text">
         Los eventos del partido aparecerán aquí<br>
         Inicio · Goles · Entretiempo · Fin
       </div>
     </div>` +
    `<div class="ed-float-cta">
       <button class="ed-float-cta__btn" id="edUploadCta" type="button">
         📸 Subir foto / video
       </button>
     </div>`;
}

// ── Navigation ────────────────────────────────────────────────────────────────
function navigateToEventDetail() {
  edState.showPredict = false;
  edState.homeScore   = 0;
  edState.awayScore   = 0;
  edState.predictSent = false;

  const homeScroll   = document.querySelector('.phone > .scroll');
  const detailView   = $ed('eventDetailView');
  if (homeScroll)  homeScroll.hidden  = true;
  if (detailView) { detailView.hidden = false; detailView.scrollTop = 0; }
  renderEventDetail();
}

function navigateToHome() {
  const homeScroll = document.querySelector('.phone > .scroll');
  const detailView = $ed('eventDetailView');
  if (homeScroll)  homeScroll.hidden  = false;
  if (detailView)  detailView.hidden  = true;
}

// ── Event delegation ──────────────────────────────────────────────────────────
$ed('eventDetailView').addEventListener('click', (e) => {
  if (e.target.closest('#edBackBtn')) {
    navigateToHome();
    return;
  }

  if (e.target.closest('#edPredictBtn')) {
    if (!edState.predictSent) edState.showPredict = !edState.showPredict;
    renderEventDetail();
    return;
  }

  const stepBtn = e.target.closest('[data-step]');
  if (stepBtn) {
    const team = stepBtn.dataset.step;
    const dir  = parseInt(stepBtn.dataset.dir, 10);
    if (team === 'home') edState.homeScore = Math.min(9, Math.max(0, edState.homeScore + dir));
    else                 edState.awayScore = Math.min(9, Math.max(0, edState.awayScore + dir));
    renderEventDetail();
    return;
  }

  if (e.target.closest('#edConfirmBtn')) {
    edState.predictSent = true;
    edState.showPredict = false;
    renderEventDetail();
    return;
  }

  // Upload CTA — mocked: log and no-op until feature-03 backend lands
  if (e.target.closest('#edUploadCta')) {
    console.log('[FEST-05] Upload CTA tapped — mocked, no-op in Previa');
  }
});

// Exposed for main.js navigation
window.navigateToEventDetail = navigateToEventDetail;
