/* Event Detail (Previa) — FEST-05 / FEST-08
   Hype Wall wired to real /media API. Upload modal with file + caption. */

import { fetchMedia, uploadMedia, likeMedia, getEventDetail, fetchMatchState, submitPrediction, generateVideoRecap } from './api.js';

// ── Event state (populated from API on navigate) ───────────────────────────────
const edEvent = {
  id: 'evt-004',
  isPast: false,
  attendeeCount: 0,
  matchStatus: 'pre',     // pre | live | ended
  matchHomeScore: 0,
  matchAwayScore: 0,
  matchGoals: [],
  venueName: '',
  venueDistance: '',
  attending: '',
  amenities: [],
  recapVideoUrl: null,
  match: { home: '', homeFlag: '', away: '', awayFlag: '', competition: '', countdownLabel: '' },
};

function _computeCountdown(kickoffIso) {
  const diff = Math.floor((new Date(kickoffIso) - Date.now()) / 1000);
  if (diff <= 0) return null;
  if (diff < 3600) return `Starts in ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `Starts in ${Math.floor(diff / 3600)} h`;
  return `Starts in ${Math.floor(diff / 86400)} days`;
}

function _applyEventData(data) {
  edEvent.isPast        = data.status === 'past';
  edEvent.attendeeCount = data.attendee_count || 0;
  edCheckedIn = !!(data.attendees && data.attendees.some(a => a.user_id === edCurrentUser.id));
  edEvent.venueName     = data.venue_name || '';
  edEvent.venueDistance = data.venue_distance || '';
  edEvent.attending     = data.attendee_count ? `${data.attendee_count} going` : '';
  edEvent.amenities     = data.amenities || [];
  edEvent.recapVideoUrl = data.recap_video_url || null;
  edEvent.match = {
    home:           data.home_team || '',
    homeFlag:       data.home_flag || '',
    away:           data.away_team || '',
    awayFlag:       data.away_flag || '',
    competition:    data.competition || '',
    countdownLabel: _computeCountdown(data.kickoff_iso) || '',
  };
}

// ── Hype Wall state ───────────────────────────────────────────────────────────
let hypePosts = [];
const edCurrentUser = { id: 'user_003', name: 'Carlos', handle: '@carlos_fan' };

// ── Check-in state ────────────────────────────────────────────────────────────
let edCheckedIn = false;

async function _checkIn(eventId) {
  try {
    await fetch(`http://localhost:8000/api/v1/events/${eventId}/checkin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: edCurrentUser.id, name: edCurrentUser.name }),
    });
    edCheckedIn = true;
  } catch (_) {}
}

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
      <button class="ed-back__btn" id="edBackBtn" type="button" aria-label="Back">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2.2"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="ed-back__venue">${event.venueName}</span>
    </div>`;
}

function renderMatchHeader(match) {
  const ms = edEvent.matchStatus;

  let pillHtml;
  if (ms === 'live') {
    pillHtml = `<div class="ed-match__previa-pill ed-match__previa-pill--live">
      <div class="ed-pill-dot"></div>LIVE
    </div>`;
  } else if (ms === 'ended' || edEvent.isPast) {
    pillHtml = `<div class="ed-match__previa-pill ed-match__previa-pill--ended">Ended</div>`;
  } else {
    pillHtml = `<div class="ed-match__previa-pill">PRE-MATCH</div>`;
  }

  const showScore = ms === 'live' || ms === 'ended';
  const scoreHtml = showScore
    ? `${edEvent.matchHomeScore} – ${edEvent.matchAwayScore}`
    : '– : –';

  const homeGoals = showScore ? edEvent.matchGoals.filter(g => g.team === match.home) : [];
  const awayGoals = showScore ? edEvent.matchGoals.filter(g => g.team === match.away) : [];

  const _lastName = (name) => name.split(' ').pop();
  const _goalItems = (goals) => goals.map(g =>
    `<div class="ed-match__team-goal">⚽ ${g.minute}' ${_lastName(g.player)}</div>`
  ).join('');

  const homeGoalsHtml = homeGoals.length
    ? `<div class="ed-match__team-goals">${_goalItems(homeGoals)}</div>` : '';
  const awayGoalsHtml = awayGoals.length
    ? `<div class="ed-match__team-goals">${_goalItems(awayGoals)}</div>` : '';

  const countdownHtml = ms === 'pre' && match.countdownLabel
    ? `<div class="ed-match__countdown">⏱ ${match.countdownLabel}</div>`
    : '';

  return `
    <div class="ed-match">
      <div class="ed-match__status">${pillHtml}</div>
      <div class="ed-match__teams">
        <div class="ed-match__team">
          <div class="ed-match__team-flag">${match.homeFlag}</div>
          <div class="ed-match__team-name">${match.home}</div>
          ${homeGoalsHtml}
        </div>
        <div class="ed-match__score">${scoreHtml}</div>
        <div class="ed-match__team">
          <div class="ed-match__team-flag">${match.awayFlag}</div>
          <div class="ed-match__team-name">${match.away}</div>
          ${awayGoalsHtml}
        </div>
      </div>
      ${countdownHtml}
      <div class="ed-match__competition">${match.competition}</div>
    </div>`;
}

function renderEventInfo(event) {
  const chips = event.amenities.map(([i, l]) => edChip(i, l)).join('');
  const attendLabel = edEvent.isPast
    ? `${edEvent.attendeeCount} attended`
    : edEvent.attendeeCount ? `${edEvent.attendeeCount} going` : '';
  const attendHtml = attendLabel
    ? `<div class="ed-info__attending">👥 ${attendLabel}</div>`
    : '';
  return `
    <div class="ed-info">
      <div class="ed-info__venue">${event.venueName}</div>
      <div class="ed-info__loc"><span>📍</span><span>${event.venueDistance}</span></div>
      ${attendHtml}
      <div class="ed-info__chips">${chips}</div>
    </div>`;
}

function renderActionButtons() {
  if (edEvent.isPast || edState.predictSent) return '';
  const predictOpen = edState.showPredict;
  return `
    <div class="ed-actions">
      <button class="ed-btn ed-btn--predict${predictOpen ? ' is-open' : ''}"
              id="edPredictBtn" type="button">
        ${predictOpen ? '✕ Close' : '🎯 Predict'}
      </button>
    </div>`;
}

function renderPredictPanel() {
  if (edState.predictSent) {
    return `
      <div class="ed-predict-confirmed">
        <span class="ed-predict-confirmed__icon">✅</span>
        <span class="ed-predict-confirmed__text">
          Prediction · ${edEvent.match.home} ${edState.homeScore} – ${edState.awayScore} ${edEvent.match.away}
        </span>
      </div>`;
  }
  if (!edState.showPredict) return '';
  return `
    <div class="ed-predict-panel" id="edPredictPanel">
      <div class="ed-predict__title">Your prediction</div>
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
        Confirm prediction →
      </button>
    </div>`;
}

const AVATAR_COLORS = ['#7c3aed','#0ea5e9','#f59e0b','#10b981','#ef4444','#8b5cf6','#06b6d4'];

function _avatarColor(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[h % AVATAR_COLORS.length];
}

function _initials(name) {
  return (name || '?').replace(/^@/, '').split(/[\s_]/).map(w => w[0] || '').join('').slice(0, 2).toUpperCase();
}

function _timeAgo(isoStr) {
  const diff = Math.floor((Date.now() - new Date(isoStr)) / 1000);
  if (diff < 60)   return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`;
  return `${Math.floor(diff / 86400)} days ago`;
}

function renderHypePost(post) {
  const handle = post.uploader_handle || post.handle || '@fan';
  const name   = post.uploader_name  || handle;
  const bg     = _avatarColor(handle);
  const initials = _initials(handle);
  const timeAgo  = post.uploaded_at ? _timeAgo(post.uploaded_at) : (post.timeAgo || '');
  const likes    = post.likes_count  != null ? post.likes_count  : (post.likes  || 0);
  const comments = post.comments     ? post.comments.length     : (post.comment_count || 0);
  const mediaType = post.media_type || post.type || 'photo';
  const caption   = post.caption || '';

  let mediaHtml = '';
  if (mediaType === 'photo' && post.url && !post.url.startsWith('/mock')) {
    mediaHtml = `<div class="hype-post__media"><img src="${post.url}" alt="media" loading="lazy" style="width:100%;height:100%;object-fit:cover"></div>`;
  } else if (mediaType === 'video' && post.url && !post.url.startsWith('/mock')) {
    mediaHtml = `
      <div class="hype-post__media">
        <video src="${post.url}" controls style="width:100%;height:100%;object-fit:cover"></video>
      </div>`;
  } else if (mediaType === 'video') {
    mediaHtml = `<div class="hype-post__media"><span class="hype-post__media-icon">▶️</span></div>`;
  } else {
    mediaHtml = `<div class="hype-post__media"><span class="hype-post__media-icon">🖼️</span></div>`;
  }

  const likedByMe = post._likedByMe || false;

  return `
    <div class="hype-post" data-media-id="${post.id || ''}">
      <div class="hype-post__header">
        <div class="hype-post__avatar" style="background:${bg}">${initials}</div>
        <div class="hype-post__meta">
          <div class="hype-post__handle">${handle}</div>
          <div class="hype-post__time">${timeAgo}</div>
        </div>
      </div>
      ${mediaHtml}
      ${caption ? `<div class="hype-post__caption">${caption}</div>` : ''}
      <div class="hype-post__actions">
        <button class="hype-post__action hype-post__like-btn${likedByMe ? ' is-liked' : ''}"
                type="button" data-media-id="${post.id || ''}">
          <span class="hype-post__action-icon">${likedByMe ? '❤️' : '🤍'}</span>
          <span class="hype-post__action-count hype-post__like-count">${likes}</span>
        </button>
        <button class="hype-post__action" type="button">
          <span class="hype-post__action-icon">💬</span>
          <span class="hype-post__action-count">${comments}</span>
        </button>
        <span class="hype-post__action-sep"></span>
        <button class="hype-post__action" type="button">
          <span class="hype-post__action-icon">↗️</span>
        </button>
      </div>
    </div>`;
}

function renderRecapBtn() {
  if (!edEvent.isPast) return '';
  const hasVideo = !!edEvent.recapVideoUrl;
  return `
    <div class="ed-recap-cta">
      <button class="ed-recap-cta__btn" id="edRecapBtn" type="button">
        ✨ View match recap
      </button>
      <button class="ed-recap-cta__btn ed-recap-cta__btn--video${hasVideo ? ' is-generated' : ''}"
              id="edGenerateVideoBtn" type="button"${hasVideo ? ' disabled' : ''}>
        🎬 ${hasVideo ? 'Video generated' : 'Generate recap video'}
      </button>
    </div>`;
}

function renderUploadModal() {
  return `
    <div class="ed-upload-modal" id="edUploadModal" hidden>
      <div class="ed-upload-modal__backdrop" id="edUploadBackdrop"></div>
      <div class="ed-upload-modal__sheet">
        <div class="ed-upload-modal__title">Upload photo / video</div>
        <label class="ed-upload-modal__file-label" for="edMediaInput">
          <span id="edMediaLabel">📎 Choose file</span>
          <input type="file" id="edMediaInput" accept="image/jpeg,image/png,image/gif,video/mp4,video/quicktime" style="display:none">
        </label>
        <textarea id="edCaptionInput" class="ed-upload-modal__caption"
          placeholder="Write a caption... (max. 280 characters)" maxlength="280" rows="3"></textarea>
        <button class="ed-upload-modal__submit" id="edUploadSubmit" type="button">
          Post 🚀
        </button>
        <button class="ed-upload-modal__cancel" id="edUploadCancel" type="button">
          Cancel
        </button>
        <div class="ed-upload-modal__error" id="edUploadError" hidden></div>
      </div>
    </div>`;
}

function renderEventDetail() {
  const container = $ed('eventDetailView');
  if (!container) return;
  const feedHtml = hypePosts.length
    ? hypePosts.map(renderHypePost).join('')
    : `<div class="ed-hype-empty">
         <div style="font-size:22px;margin-bottom:6px">📸</div>
         <div style="font-size:11px;color:var(--muted)">Be the first to upload a photo or video</div>
       </div>`;

  container.innerHTML =
    renderBackRow(edEvent) +
    renderMatchHeader(edEvent.match) +
    renderEventInfo(edEvent) +
    renderActionButtons() +
    renderPredictPanel() +
    renderRecapBtn() +
    `<div class="ed-divider">
       <div class="ed-divider__line"></div>
       <div class="ed-divider__label">Hype Wall</div>
       <div class="ed-divider__line"></div>
     </div>` +
    feedHtml +
    (hypePosts.length === 0
      ? `<div class="ed-empty-state">
           <div class="ed-empty-state__icon">⚽</div>
           <div class="ed-empty-state__text">
             Match events will appear here<br>
             Kickoff · Goals · Half-time · Final
           </div>
         </div>`
      : '') +
    renderUploadModal();

  _updateFloatCta();
}

// ── Phone-level float CTA ─────────────────────────────────────────────────────
function _updateFloatCta() {
  const el = document.getElementById('edFloatCta');
  if (!el) return;
  if (!edEvent.isPast && edCheckedIn) {
    el.innerHTML = `<button class="ed-float-cta__btn" id="edUploadCta" type="button">
      📸 Upload photo / video
    </button>`;
    el.hidden = false;
  } else {
    el.hidden = true;
    el.innerHTML = '';
  }
}

document.getElementById('edFloatCta').addEventListener('click', (e) => {
  if (e.target.closest('#edUploadCta')) _openUploadModal();
});

// ── Navigation ────────────────────────────────────────────────────────────────
async function loadHypeFeed() {
  try {
    const data = await fetchMedia(edEvent.id);
    hypePosts = data.media || [];
  } catch (_) {
    hypePosts = [];
  }
}

async function navigateToEventDetail(venue) {
  edState.showPredict     = false;
  edState.homeScore       = 0;
  edState.awayScore       = 0;
  edState.predictSent     = false;
  edEvent.isPast          = false;
  edCheckedIn             = false;

  // Restore a previously submitted prediction for this event
  if (venue && venue.id) {
    const saved = localStorage.getItem(`pred_${venue.id}`);
    if (saved) {
      try {
        const { homeScore, awayScore } = JSON.parse(saved);
        edState.homeScore   = homeScore;
        edState.awayScore   = awayScore;
        edState.predictSent = true;
      } catch (_) {}
    }
  }
  edEvent.matchStatus     = 'pre';
  edEvent.matchHomeScore  = 0;
  edEvent.matchAwayScore  = 0;
  edEvent.matchGoals      = [];
  edEvent.attendeeCount   = 0;

  if (venue && venue.id) edEvent.id = venue.id;

  try {
    const data = await getEventDetail(edEvent.id);
    _applyEventData(data);
  } catch (_) {
    if (venue) {
      edEvent.venueName     = venue.name     || edEvent.venueName;
      edEvent.venueDistance = venue.distance || edEvent.venueDistance;
      edEvent.attending     = venue.attending || edEvent.attending;
      edEvent.amenities     = venue.amenities || edEvent.amenities;
      edEvent.isPast        = venue.status === 'past';
    }
  }

  try {
    const ms = await fetchMatchState(edEvent.id);
    edEvent.matchStatus    = ms.status;
    edEvent.matchHomeScore = ms.home_score;
    edEvent.matchAwayScore = ms.away_score;
    edEvent.matchGoals     = ms.goals || [];
  } catch (_) {
    // match state unavailable — pill will show based on event status
    if (edEvent.isPast) edEvent.matchStatus = 'ended';
  }

  const homeScroll = document.querySelector('.phone > .scroll');
  const detailView = $ed('eventDetailView');
  const livebar    = document.querySelector('.live-bar');
  // Hide every sibling view to prevent flex-1 splits
  ['eventDetailView','recapView','mapaView','misEventosView','createEventView'].forEach(id => {
    const el = document.getElementById(id); if (el) el.hidden = true;
  });
  if (homeScroll) homeScroll.hidden = true;
  if (detailView) { detailView.hidden = false; detailView.scrollTop = 0; }
  if (livebar)    livebar.hidden = true;
  await loadHypeFeed();
  renderEventDetail();
}

function navigateToHome() {
  const homeScroll = document.querySelector('.phone > .scroll');
  const floatCta   = document.getElementById('edFloatCta');
  // Hide every non-home view to prevent flex-1 splits
  ['eventDetailView','recapView','mapaView','misEventosView','createEventView'].forEach(id => {
    const el = document.getElementById(id); if (el) el.hidden = true;
  });
  if (homeScroll)  homeScroll.hidden  = false;
  if (floatCta)  { floatCta.hidden = true; floatCta.innerHTML = ''; }
  if (typeof window._updateLiveBar === 'function') window._updateLiveBar();
}

// ── Upload modal state ────────────────────────────────────────────────────────
let _uploadFile = null;

function _openUploadModal() {
  const modal = $ed('edUploadModal');
  if (modal) modal.hidden = false;
}

function _closeUploadModal() {
  const modal = $ed('edUploadModal');
  if (modal) modal.hidden = true;
  _uploadFile = null;
  const label = $ed('edMediaLabel');
  if (label) label.textContent = '📎 Choose file';
  const caption = $ed('edCaptionInput');
  if (caption) caption.value = '';
  const err = $ed('edUploadError');
  if (err) { err.hidden = true; err.textContent = ''; }
}

async function _submitUpload() {
  if (!_uploadFile) return;
  const caption = ($ed('edCaptionInput') || {}).value || '';
  const errEl = $ed('edUploadError');
  try {
    const post = await uploadMedia(
      edEvent.id, _uploadFile,
      edCurrentUser.id, edCurrentUser.name, edCurrentUser.handle,
      caption || null,
    );
    _closeUploadModal();
    hypePosts.unshift(post);
    renderEventDetail();
  } catch (err) {
    const msg = err && err.detail
      ? (Array.isArray(err.detail) ? err.detail[0].msg : err.detail)
      : 'Upload failed. Please try again.';
    if (errEl) { errEl.textContent = msg; errEl.hidden = false; }
  }
}

// ── Event delegation ──────────────────────────────────────────────────────────
$ed('eventDetailView').addEventListener('click', async (e) => {
  if (e.target.closest('#edBackBtn')) {
    navigateToHome();
    return;
  }

  if (e.target.closest('#edRecapBtn')) {
    if (typeof window.navigateToRecap === 'function') {
      window.navigateToRecap(edEvent.id);
    }
    return;
  }

  if (e.target.closest('#edGenerateVideoBtn')) {
    const btn = document.getElementById('edGenerateVideoBtn');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    btn.textContent = '⏳ Generating video...';
    try {
      const result = await generateVideoRecap(edEvent.id);
      edEvent.recapVideoUrl = result.video_url;
      btn.textContent = '🎬 Video generated';
      btn.classList.add('is-generated');
      if (typeof window.navigateToRecap === 'function') {
        window.navigateToRecap(edEvent.id);
      }
    } catch (err) {
      btn.disabled = false;
      btn.textContent = '🎬 Generate recap video';
      const detail = err && err.detail ? err.detail : 'Generation failed. Please try again.';
      alert(detail);
    }
    return;
  }

  if (e.target.closest('#edUploadCta')) {
    _openUploadModal();
    return;
  }

  if (e.target.closest('#edUploadCancel') || e.target.closest('#edUploadBackdrop')) {
    _closeUploadModal();
    return;
  }

  if (e.target.closest('#edUploadSubmit')) {
    await _submitUpload();
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
    // Persist to DB and localStorage so state survives navigation
    try {
      await submitPrediction(edEvent.id, {
        userId: edCurrentUser.id,
        name: edCurrentUser.name,
        homeScore: edState.homeScore,
        awayScore: edState.awayScore,
      });
    } catch (_) {}
    localStorage.setItem(`pred_${edEvent.id}`, JSON.stringify({
      homeScore: edState.homeScore,
      awayScore: edState.awayScore,
    }));
    return;
  }

  const likeBtn = e.target.closest('.hype-post__like-btn');
  if (likeBtn) {
    const mediaId = likeBtn.dataset.mediaId;
    if (!mediaId) return;
    try {
      const result = await likeMedia(edEvent.id, mediaId, edCurrentUser.id);
      const post = hypePosts.find(p => p.id === mediaId);
      if (post) {
        post.likes_count = result.likes_count;
        post._likedByMe  = result.liked_by_me;
      }
      const countEl = likeBtn.querySelector('.hype-post__like-count');
      const iconEl  = likeBtn.querySelector('.hype-post__action-icon');
      if (countEl) countEl.textContent = result.likes_count;
      if (iconEl)  iconEl.textContent  = result.liked_by_me ? '❤️' : '🤍';
      likeBtn.classList.toggle('is-liked', result.liked_by_me);
    } catch (_) { /* optimistic update failed silently */ }
    return;
  }
});

$ed('eventDetailView').addEventListener('change', (e) => {
  if (e.target.id === 'edMediaInput') {
    const file = e.target.files && e.target.files[0];
    if (file) {
      _uploadFile = file;
      const label = $ed('edMediaLabel');
      if (label) label.textContent = `📎 ${file.name}`;
    }
  }
});

// Exposed for main.js navigation
window.navigateToEventDetail = navigateToEventDetail;

window.performEstoyAqui = async () => {
  const livebar = document.querySelector('.live-bar');
  const eventId = (livebar && livebar.dataset.eventId) ? livebar.dataset.eventId : edEvent.id;
  await navigateToEventDetail({ id: eventId });
  if (!edCheckedIn) {
    await _checkIn(edEvent.id);
    renderEventDetail();
  }
  if (livebar) livebar.hidden = true;
};
