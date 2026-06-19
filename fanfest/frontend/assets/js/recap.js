import { fetchRecap, fetchMatchState } from './api.js';

const EVENT_ID = 'event_001';

function renderLoading() {
  return `<div class="recap-loading">
    <div class="recap-loading__spinner"></div>
    <p class="recap-loading__text">Analizando la vibra del evento...</p>
  </div>`;
}

function renderFinalScore(data) {
  return `<div class="recap-scorefinal">
    <div class="recap-scorefinal__label">Resultado Final</div>
    <div class="recap-scorefinal__teams">
      <span class="recap-scorefinal__team">${data.home_team}</span>
      <span class="recap-scorefinal__score">${data.home_score} – ${data.away_score}</span>
      <span class="recap-scorefinal__team">${data.away_team}</span>
    </div>
  </div>`;
}

function renderNarrative(narrative) {
  return `<div class="recap-narrative">
    <div class="recap-narrative__label">Crónica IA</div>
    <p class="recap-narrative__text">${narrative}</p>
  </div>`;
}

function renderHighlights(highlights) {
  if (!highlights || highlights.length === 0) return '';
  const slides = highlights.map(h => `
    <div class="recap-slide">
      <div class="recap-slide__label">${h.label}</div>
      <p class="recap-slide__desc">${h.description}</p>
    </div>`).join('');
  return `<div class="recap-highlights">
    <div class="recap-highlights__title">Momentos destacados</div>
    <div class="recap-carousel">${slides}</div>
  </div>`;
}

function renderPredictions(correctPredictors) {
  if (correctPredictors && correctPredictors.length > 0) {
    const names = correctPredictors.join(', ');
    return `<div class="recap-predictions">
      <div class="recap-predictions__title">Predicciones correctas</div>
      <p class="recap-predictions__names">${names}</p>
    </div>`;
  }
  return `<div class="recap-predictions recap-predictions--empty">
    <div class="recap-predictions__title">Predicciones correctas</div>
    <p class="recap-predictions__coming-soon">Las predicciones estarán disponibles pronto.</p>
  </div>`;
}

function renderPhotosSection(photoCount) {
  if (photoCount <= 0) {
    return `<div class="recap-photos">
      <div class="recap-photos__title">Fotos del evento</div>
      <p class="recap-photos__empty">No se subieron fotos durante el evento.</p>
    </div>`;
  }
  return `<div class="recap-photos">
    <div class="recap-photos__title">Fotos del evento</div>
    <p class="recap-photos__count">${photoCount} foto${photoCount !== 1 ? 's' : ''} compartida${photoCount !== 1 ? 's' : ''} por los fans.</p>
  </div>`;
}

function renderActions() {
  return `<div class="recap-actions">
    <button class="recap-btn recap-btn--share" id="recapShareBtn" type="button">Compartir recuerdo</button>
    <button class="recap-btn recap-btn--react" id="recapReactBtn" type="button">Reaccionar</button>
  </div>`;
}

function renderNextEvents() {
  return `<div class="recap-next">
    <div class="recap-next__title">Proximos fan fests</div>
    <div class="recap-next__card">
      <div class="recap-next__event">Argentina vs Brasil · 28 Jun</div>
      <div class="recap-next__location">Buenos Aires · Estadio Monumental</div>
    </div>
    <div class="recap-next__card">
      <div class="recap-next__event">Uruguay vs Colombia · 2 Jul</div>
      <div class="recap-next__location">Montevideo · Estadio Centenario</div>
    </div>
  </div>`;
}

function renderFallbackNotice(fallback) {
  if (!fallback) return '';
  return `<div class="recap-fallback-notice">Resumen generado con informacion del partido (modo sin conexion a IA).</div>`;
}

function renderRecapView(data) {
  return `
    ${renderFallbackNotice(data.fallback)}
    ${renderFinalScore(data)}
    ${renderNarrative(data.narrative)}
    ${renderHighlights(data.highlights)}
    ${renderPredictions(data.correct_predictors)}
    ${renderPhotosSection(data.photo_count)}
    ${renderActions()}
    ${renderNextEvents()}`;
}

function wireActions() {
  const shareBtn = document.getElementById('recapShareBtn');
  const reactBtn = document.getElementById('recapReactBtn');

  if (shareBtn) {
    shareBtn.addEventListener('click', () => {
      const shareData = { title: 'Fan Fest Recap', text: '¡Viví el partido con nosotros!', url: window.location.href };
      if (navigator.share) {
        navigator.share(shareData).catch(() => {});
      } else {
        navigator.clipboard.writeText(window.location.href).then(() => {
          shareBtn.textContent = 'Link copiado!';
          setTimeout(() => { shareBtn.textContent = 'Compartir recuerdo'; }, 2000);
        }).catch(() => {});
      }
    });
  }

  if (reactBtn) {
    let reacted = false;
    reactBtn.addEventListener('click', () => {
      reacted = !reacted;
      reactBtn.textContent = reacted ? 'Reaccionaste!' : 'Reaccionar';
      reactBtn.classList.toggle('recap-btn--reacted', reacted);
    });
  }
}

async function mountRecap() {
  const container = document.getElementById('recapView');
  if (!container) return;

  try {
    const state = await fetchMatchState(EVENT_ID);
    if (state.status !== 'ended') return;
  } catch (_) {
    return;
  }

  container.innerHTML = renderLoading();
  container.classList.add('recap-view--visible');

  try {
    const data = await fetchRecap(EVENT_ID);
    container.innerHTML = renderRecapView(data);
    wireActions();
  } catch (err) {
    container.innerHTML = `<p class="recap-error">No se pudo generar el resumen. Intenta nuevamente.</p>`;
  }
}

mountRecap();
