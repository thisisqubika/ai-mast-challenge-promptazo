const API_BASE = 'http://localhost:8000/api/v1';
const USER_NAME_KEY = 'fanfest_user_name';
const USER_ID_KEY = 'fanfest_user_id';

function getUserIdentity() {
  let name = localStorage.getItem(USER_NAME_KEY);
  let id = localStorage.getItem(USER_ID_KEY);
  if (!name) {
    name = prompt('Tu nombre para FanFest:') || 'Hincha';
    id = 'user_' + Date.now();
    localStorage.setItem(USER_NAME_KEY, name);
    localStorage.setItem(USER_ID_KEY, id);
  }
  return { name, id };
}

async function fetchEvent(eventId) {
  const res = await fetch(`${API_BASE}/events/${eventId}`);
  if (!res.ok) throw new Error('Event not found');
  return res.json();
}

async function postPrediction(eventId, userId, name, homeScore, awayScore) {
  const res = await fetch(`${API_BASE}/events/${eventId}/predictions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, name, home_score: homeScore, away_score: awayScore }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Error');
  }
  return res.json();
}

async function postCheckin(eventId, userId, name) {
  const res = await fetch(`${API_BASE}/events/${eventId}/checkin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al hacer check-in');
  }
  return res.json();
}

function formatKickoff(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-AR', { day: 'numeric', month: 'short', year: 'numeric' })
      + ' · ' + d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
  } catch (_) { return isoString; }
}

function renderEvent(event, predState) {
  const attendeeCount = event.attendees ? event.attendees.length : 0;
  return `
    <div class="ev-header">
      <button class="ev-back" id="evBack" type="button" aria-label="Volver">←</button>
      <span class="ev-title">Detalle del evento</span>
    </div>
    <div class="ev-body">
      <div class="ev-match">
        <div class="ev-teams">
          <div class="ev-team">
            <div class="ev-flag">${event.home_flag}</div>
            <div class="ev-team-name">${event.home_team}</div>
          </div>
          <div class="ev-vs">VS</div>
          <div class="ev-team">
            <div class="ev-flag">${event.away_flag}</div>
            <div class="ev-team-name">${event.away_team}</div>
          </div>
        </div>
        <div class="ev-meta">${event.venue_name} · ${formatKickoff(event.kickoff_iso)}</div>
      </div>

      <div class="ev-info-row">📍 <span>${event.venue_address}</span></div>
      <div class="ev-info-row">👤 <span>Organiza ${event.organizer}</span></div>

      <div class="ev-section-title">Tu pronóstico</div>
      <div class="ev-prediction">
        <div class="ev-pred-row">
          <div class="ev-pred-team">
            <div class="ev-pred-flag">${event.home_flag}</div>
            <div class="ev-stepper">
              <button class="ev-step-btn" id="homeDown" type="button">−</button>
              <span class="ev-step-val" id="homeVal">${predState.home}</span>
              <button class="ev-step-btn" id="homeUp" type="button">+</button>
            </div>
          </div>
          <div class="ev-pred-vs">–</div>
          <div class="ev-pred-team">
            <div class="ev-pred-flag">${event.away_flag}</div>
            <div class="ev-stepper">
              <button class="ev-step-btn" id="awayDown" type="button">−</button>
              <span class="ev-step-val" id="awayVal">${predState.away}</span>
              <button class="ev-step-btn" id="awayUp" type="button">+</button>
            </div>
          </div>
        </div>
        <button class="ev-pred-submit" id="predSubmit" type="button">Guardar pronóstico</button>
        <div class="ev-pred-msg" id="predMsg"></div>
      </div>

      <div class="ev-section-title">Asistentes</div>
      <div class="ev-attendees">👥 <span>${attendeeCount} confirmado${attendeeCount !== 1 ? 's' : ''}</span></div>

      <div class="ev-section-title">Links</div>
      <div class="ev-actions">
        <a class="ev-action-btn" href="${event.calendar_link}" target="_blank" rel="noopener">
          <span class="ev-action-icon">📅</span><span>Calendario</span>
        </a>
        <a class="ev-action-btn" href="${event.maps_link}" target="_blank" rel="noopener">
          <span class="ev-action-icon">🗺️</span><span>Maps</span>
        </a>
        <button class="ev-action-btn" id="shareBtn" type="button">
          <span class="ev-action-icon">🔗</span><span>Compartir</span>
        </button>
      </div>

      <button class="ev-checkin-btn" id="checkinBtn" type="button">📍 Ya estoy acá</button>
    </div>`;
}

function hideEvent() {
  const view = document.getElementById('eventView');
  if (view) view.classList.remove('is-open');
}

async function showEvent(eventId) {
  const view = document.getElementById('eventView');
  if (!view) return;

  view.innerHTML = '<div style="padding:40px 20px;text-align:center;color:#64748b">Cargando...</div>';
  view.classList.add('is-open');

  let event;
  try {
    event = await fetchEvent(eventId);
  } catch (_) {
    view.innerHTML = '<div class="ev-error">No se pudo cargar el evento.</div>';
    return;
  }

  const predState = { home: 1, away: 0 };
  view.innerHTML = renderEvent(event, predState);

  document.getElementById('evBack').addEventListener('click', hideEvent);

  function clamp(n) { return Math.max(0, Math.min(9, n)); }
  document.getElementById('homeUp').addEventListener('click', () => {
    predState.home = clamp(predState.home + 1);
    document.getElementById('homeVal').textContent = predState.home;
  });
  document.getElementById('homeDown').addEventListener('click', () => {
    predState.home = clamp(predState.home - 1);
    document.getElementById('homeVal').textContent = predState.home;
  });
  document.getElementById('awayUp').addEventListener('click', () => {
    predState.away = clamp(predState.away + 1);
    document.getElementById('awayVal').textContent = predState.away;
  });
  document.getElementById('awayDown').addEventListener('click', () => {
    predState.away = clamp(predState.away - 1);
    document.getElementById('awayVal').textContent = predState.away;
  });

  document.getElementById('predSubmit').addEventListener('click', async () => {
    const { name, id } = getUserIdentity();
    const btn = document.getElementById('predSubmit');
    const msg = document.getElementById('predMsg');
    btn.disabled = true;
    msg.textContent = 'Guardando...';
    try {
      await postPrediction(eventId, id, name, predState.home, predState.away);
      msg.textContent = '✓ Pronóstico guardado';
      msg.style.color = '#10b981';
    } catch (err) {
      msg.textContent = err.message;
      msg.style.color = '#ef4444';
    } finally {
      btn.disabled = false;
    }
  });

  document.getElementById('shareBtn').addEventListener('click', async () => {
    const url = event.invite_link || location.href;
    if (navigator.share) {
      await navigator.share({ title: `${event.home_team} vs ${event.away_team}`, url }).catch(() => {});
    } else {
      await navigator.clipboard.writeText(url).catch(() => {});
      const btn = document.getElementById('shareBtn');
      const span = btn.querySelector('span:last-child');
      if (span) { span.textContent = '¡Copiado!'; setTimeout(() => { span.textContent = 'Compartir'; }, 2000); }
    }
  });

  document.getElementById('checkinBtn').addEventListener('click', async () => {
    const { name, id } = getUserIdentity();
    const btn = document.getElementById('checkinBtn');
    btn.disabled = true;
    btn.textContent = 'Registrando...';
    try {
      await postCheckin(eventId, id, name);
      btn.textContent = '✓ ¡Estás dentro!';
      btn.classList.add('is-done');
      localStorage.setItem('live_uploader_name', name);
      localStorage.setItem('live_uploader_id', id);
      setTimeout(() => { hideEvent(); }, 1800);
    } catch (err) {
      btn.disabled = false;
      btn.textContent = '📍 Ya estoy acá';
      const msg = document.getElementById('predMsg');
      if (msg) { msg.textContent = err.message; msg.style.color = '#ef4444'; }
    }
  });
}

window.showEvent = showEvent;
