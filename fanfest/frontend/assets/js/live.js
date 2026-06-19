import { fetchMatchState, fetchPhotos } from './api.js';

const EVENT_ID = 'event_001';
const POLL_INTERVAL = 3000;
const UPLOADER_KEY = 'live_uploader_name';
const UPLOADER_ID_KEY = 'live_uploader_id';

function getOrPromptUploader() {
  let name = localStorage.getItem(UPLOADER_KEY);
  let id = localStorage.getItem(UPLOADER_ID_KEY);
  if (!name) {
    name = prompt('Tu nombre para la Hype Wall:') || 'Anónimo';
    id = `user_${Date.now()}`;
    localStorage.setItem(UPLOADER_KEY, name);
    localStorage.setItem(UPLOADER_ID_KEY, id);
  }
  return { name, id };
}

function formatClock(clockSeconds) {
  const minutes = Math.floor(clockSeconds / 60);
  return `${minutes}'`;
}

function statusBadge(status) {
  if (status === 'live') {
    return `<span class="live-badge">
      <span class="live-dot"><span class="live-dot__ring"></span><span class="live-dot__core"></span></span>
      EN VIVO
    </span>`;
  }
  if (status === 'ended') return '<span class="status-badge status-badge--ended">FINAL</span>';
  return '<span class="status-badge status-badge--pre">PRE-PARTIDO</span>';
}

function clockDisplay(state) {
  if (state.status === 'live') return formatClock(state.clock_seconds);
  if (state.status === 'ended') return 'Final';
  return 'Pre-partido';
}

function goalSummary(state) {
  const total = state.home_score + state.away_score;
  if (total === 0) return '0 goles';
  return `${state.home_team} ${state.home_score} · ${state.away_team} ${state.away_score}`;
}

function renderScoreboard(state) {
  return `
    <div class="scoreboard">
      <div class="scoreboard__status">${statusBadge(state.status)}</div>
      <div class="scoreboard__teams">
        <div class="scoreboard__team">
          <span class="scoreboard__team-name">${state.home_team}</span>
          <span class="scoreboard__score">${state.home_score}</span>
        </div>
        <div class="scoreboard__sep">–</div>
        <div class="scoreboard__team scoreboard__team--away">
          <span class="scoreboard__score">${state.away_score}</span>
          <span class="scoreboard__team-name">${state.away_team}</span>
        </div>
      </div>
      <div class="scoreboard__meta">
        <span class="scoreboard__venue">${state.venue}</span>
        <span class="scoreboard__clock">${clockDisplay(state)}</span>
      </div>
      <div class="scoreboard__summary">${goalSummary(state)}</div>
    </div>`;
}

function renderGoals(goals) {
  if (!goals || goals.length === 0) return '';
  const items = goals.map(g => `
    <div class="goal-card">
      <span class="goal-card__minute">${g.minute}'</span>
      <span class="goal-card__player">${g.player}</span>
      <span class="goal-card__team">${g.team}</span>
    </div>`).join('');
  return `<div class="goals-section"><div class="goals-title">Goles</div><div class="goals-list">${items}</div></div>`;
}

function renderPhotos(photos) {
  if (!photos || photos.length === 0) {
    return '<p class="hype-empty">Aun no hay fotos. Sé el primero en subir una.</p>';
  }
  return photos.map(p => {
    const when = new Date(p.uploaded_at).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
    return `
      <div class="hype-cell">
        <img class="hype-cell__img" src="${p.url}" alt="Foto de ${p.uploader_name}" loading="lazy">
        <div class="hype-cell__label">${p.uploader_name} · ${when}</div>
      </div>`;
  }).join('');
}

function renderRecapBanner() {
  return `
    <div class="recap-banner">
      <div class="recap-banner__title">PARTIDO TERMINADO</div>
      <div class="recap-banner__sub">✨ Recapitulación disponible pronto</div>
    </div>`;
}

function renderLiveView(state, photos) {
  const ended = state.status === 'ended';
  const liveDetail = ended ? '' : `
    ${renderGoals(state.goals)}
    <div class="hype-wall">
      <div class="hype-wall__title">Hype Wall 📸</div>
      <div class="hype-grid" id="hypeGrid">${renderPhotos(photos)}</div>
    </div>`;

  return `
    ${renderScoreboard(state)}
    ${ended ? renderRecapBanner() : ''}
    ${liveDetail}`;
}


async function refreshPhotos() {
  const grid = document.getElementById('hypeGrid');
  if (!grid) return;
  try {
    const data = await fetchPhotos(EVENT_ID);
    grid.innerHTML = renderPhotos(data.photos);
  } catch (_) {}
}

let lastStatus = null;

async function poll() {
  const container = document.getElementById('liveView');
  if (!container) return;
  try {
    const [state, photosData] = await Promise.all([
      fetchMatchState(EVENT_ID),
      fetchPhotos(EVENT_ID),
    ]);
    if (state.status !== lastStatus) {
      lastStatus = state.status;
      container.innerHTML = renderLiveView(state, photosData.photos);
    } else {
      const grid = document.getElementById('hypeGrid');
      if (grid) grid.innerHTML = renderPhotos(photosData.photos);
      const clockEl = container.querySelector('.scoreboard__clock');
      if (clockEl) clockEl.textContent = clockDisplay(state);
    }
  } catch (err) {
    if (!lastStatus) {
      container.innerHTML = '<p class="live-error">Conectando con el servidor...</p>';
    }
  }
}

poll();
setInterval(poll, POLL_INTERVAL);
