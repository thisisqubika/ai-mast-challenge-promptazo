/* Recap screen — FEST-06
   Renders the AI-generated event recap inside the phone frame.
   Entry point: window.navigateToRecap(eventId) called from main.js. */

import { fetchRecap, fetchMatchState } from './api.js';

const $r = (id) => document.getElementById(id);
const homeScroll = () => document.querySelector('.phone > .scroll');

// ── Renderers ─────────────────────────────────────────────────────────────────
function renderBackRow() {
  return `
    <div class="rc-back">
      <button class="rc-back__btn" id="rcBackBtn" type="button" aria-label="Volver">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2.2"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="rc-back__title">Crónica IA</span>
    </div>`;
}

function renderLoading() {
  return renderBackRow() + `
    <div class="recap-loading">
      <div class="recap-loading__spinner"></div>
      <p class="recap-loading__text">Analizando la vibra del evento...</p>
    </div>`;
}

function renderError(msg) {
  return renderBackRow() + `
    <div class="recap-error-state">
      <div class="recap-error-state__icon">⚠️</div>
      <p class="recap-error-state__text">${msg}</p>
    </div>`;
}

function renderRecapContent(data) {
  const highlights = (data.highlights || []).map((h) => `
    <div class="recap-slide">
      <div class="recap-slide__label">${h.label}</div>
      <p class="recap-slide__desc">${h.description}</p>
    </div>`).join('');

  const fallbackNotice = data.fallback
    ? `<div class="recap-fallback-notice">Resumen generado sin IA (modo offline).</div>`
    : '';

  const highlightsBlock = highlights
    ? `<div class="recap-highlights">
         <div class="recap-highlights__title">Momentos destacados</div>
         <div class="recap-carousel">${highlights}</div>
       </div>`
    : '';

  return renderBackRow() +
    fallbackNotice +
    `<div class="recap-scorefinal">
       <div class="recap-scorefinal__label">Resultado Final</div>
       <div class="recap-scorefinal__teams">
         <span class="recap-scorefinal__team">${data.home_team}</span>
         <span class="recap-scorefinal__score">${data.home_score} – ${data.away_score}</span>
         <span class="recap-scorefinal__team">${data.away_team}</span>
       </div>
     </div>` +
    `<div class="recap-narrative">
       <div class="recap-narrative__label">✨ Crónica</div>
       <p class="recap-narrative__text">${data.narrative}</p>
     </div>` +
    highlightsBlock;
}

// ── Navigation ────────────────────────────────────────────────────────────────
function showView() {
  const home = homeScroll();
  const view = $r('recapView');
  if (home) home.hidden = true;
  if (view) { view.hidden = false; view.scrollTop = 0; }
}

function hideView() {
  const home = homeScroll();
  const view = $r('recapView');
  if (home) home.hidden = false;
  if (view) view.hidden = true;
}

function wireBack() {
  const btn = $r('rcBackBtn');
  if (btn) btn.addEventListener('click', hideView);
}

async function navigateToRecap(eventId) {
  const view = $r('recapView');
  if (!view) return;

  showView();
  view.innerHTML = renderLoading();
  wireBack();

  // Validate entity exists
  let state;
  try {
    state = await fetchMatchState(eventId);
  } catch (_) {
    view.innerHTML = renderError('Partido no encontrado.');
    wireBack();
    return;
  }

  // Validate match has ended
  if (state.status !== 'ended') {
    const label = state.status === 'pre' ? 'pre-partido' : 'en vivo';
    view.innerHTML = renderError(
      `El partido está ${label}.<br>La crónica estará disponible al finalizar.`
    );
    wireBack();
    return;
  }

  // Fetch AI recap
  try {
    const data = await fetchRecap(eventId);
    view.innerHTML = renderRecapContent(data);
    wireBack();
  } catch (_) {
    view.innerHTML = renderError('No se pudo generar la crónica. Intenta nuevamente.');
    wireBack();
  }
}

window.navigateToRecap = navigateToRecap;
