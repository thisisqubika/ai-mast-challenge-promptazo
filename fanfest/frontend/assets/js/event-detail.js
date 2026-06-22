/* Event Detail (Previa) — FEST-05 / FEST-08
   Hype Wall wired to real /media API. Upload modal with file + caption. */

import { fetchMedia, uploadMedia, likeMedia, getEventDetail, fetchMatchState, syncFixture, submitPrediction, generateVideoRecap } from './api.js';

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
  venueAddress: '',
  venueDistance: '',
  attending: '',
  amenities: [],
  recapVideoUrl: null,
  match: { home: '', homeFlag: '', away: '', awayFlag: '', competition: '', countdownLabel: '' },
};

// ── Media URL helper (backend on :8000, frontend on :8080) ───────────────────
const MEDIA_BASE = 'http://localhost:8000';
function _mediaUrl(url) {
  if (!url) return '';
  return url.startsWith('/') ? MEDIA_BASE + url : url;
}

// ── Live sync (API-Football polling) ──────────────────────────────────────────
let _syncInterval = null;
const SYNC_INTERVAL_MS = 3 * 60 * 1000; // 3 minutes

function _stopLiveSync() {
  if (_syncInterval) { clearInterval(_syncInterval); _syncInterval = null; }
}

function _applyMatchState(ms) {
  edEvent.matchStatus    = ms.status;
  edEvent.matchHomeScore = ms.home_score;
  edEvent.matchAwayScore = ms.away_score;
  edEvent.matchGoals     = ms.goals || [];
  // Update only the match header in-place to preserve scroll position
  const matchEl = document.querySelector('.ed-hero-card');
  if (matchEl) {
    const tmp = document.createElement('div');
    tmp.innerHTML = renderMatchHeader(edEvent.match);
    matchEl.replaceWith(tmp.firstElementChild);
  }
  if (ms.status === 'ended') _stopLiveSync();
}

function _startLiveSync(eventId) {
  _stopLiveSync();
  _syncInterval = setInterval(async () => {
    try {
      const ms = await syncFixture(eventId);
      _applyMatchState(ms);
    } catch (_) { /* silently skip failed syncs */ }
  }, SYNC_INTERVAL_MS);
}

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
  edEvent.venueAddress  = data.venue_address || '';
  edEvent.venueDistance = data.venue_distance || '';
  edEvent.kickoffIso    = data.kickoff_iso || null;
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
    <div class="ed-nav-header">
      <button class="ed-back__btn" id="edBackBtn" type="button" aria-label="Back">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2.2"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <div class="ed-nav-title"><span>${event.venueName}</span></div>
    </div>`;
}

function renderMatchHeader(match) {
  const ms = edEvent.matchStatus;

  // Status pill
  let pillClass = '', pillText = 'PRE-MATCH';
  if (ms === 'live') { pillClass = 'ed-status-pill--live'; pillText = 'LIVE'; }
  else if (ms === 'ended' || edEvent.isPast) { pillClass = 'ed-status-pill--ended'; pillText = 'EVENT FINISHED'; }
  const subText = (ms === 'pre' && match.countdownLabel) ? match.countdownLabel : '';

  const showScore = ms === 'live' || ms === 'ended' || edEvent.isPast;
  const isPre = !showScore;

  const homeGoals = showScore ? edEvent.matchGoals.filter(g => g.team === match.home) : [];
  const awayGoals = showScore ? edEvent.matchGoals.filter(g => g.team === match.away) : [];
  const _lastName = (name) => name.split(' ').pop();
  const _goalItems = (goals) => goals.map(g =>
    `<div class="ed-team-goal">⚽ ${g.minute}' ${_lastName(g.player)}</div>`
  ).join('');
  const homeGoalsHtml = homeGoals.length ? `<div class="ed-team-goals">${_goalItems(homeGoals)}</div>` : '';
  const awayGoalsHtml = awayGoals.length ? `<div class="ed-team-goals">${_goalItems(awayGoals)}</div>` : '';

  const liveHtml = ms === 'live' ? `
    <div class="ed-live-indicator">
      <div class="ed-live-dot-wrap">
        <div class="ed-live-dot-ring"></div><div class="ed-live-dot-core"></div>
      </div>
      <span class="ed-live-label">LIVE</span>
    </div>` : '';

  const predZone = renderPredictionZone(match);
  const divider  = predZone ? '<div class="ed-card-divider"></div>' : '';

  return `
    <div class="ed-hero-card">
      <div class="ed-status-area">
        <div class="ed-status-pill ${pillClass}">${pillText}</div>
        ${subText ? `<span class="ed-status-sub">${subText}</span>` : ''}
      </div>
      <div class="ed-score-row">
        <div class="ed-team-col">
          <div class="ed-team-flag">${match.homeFlag}</div>
          <span class="ed-team-name">${match.home}</span>
          ${homeGoalsHtml}
        </div>
        <div class="ed-score-center">
          <div class="ed-score-pills">
            <div class="ed-score-digit${isPre ? ' ed-score-digit--pre' : ''}">${showScore ? edEvent.matchHomeScore : '–'}</div>
            <span class="ed-score-sep">–</span>
            <div class="ed-score-digit${isPre ? ' ed-score-digit--pre' : ''}">${showScore ? edEvent.matchAwayScore : '–'}</div>
          </div>
          ${liveHtml}
        </div>
        <div class="ed-team-col">
          <div class="ed-team-flag">${match.awayFlag}</div>
          <span class="ed-team-name">${match.away}</span>
          ${awayGoalsHtml}
        </div>
      </div>
      <div class="ed-competition-line"><span>${match.competition}</span></div>
      ${divider}${predZone}
    </div>`;
}

function renderPredictionZone(match) {
  if (edEvent.isPast || edEvent.matchStatus === 'live' || edEvent.matchStatus === 'ended') return '';
  const home = (match && match.home) || edEvent.match.home || 'Home';
  const away = (match && match.away) || edEvent.match.away || 'Away';
  if (edState.predictSent) {
    return `
      <div class="ed-prediction-zone">
        <div class="ed-predict-label">YOUR PREDICTION</div>
        <div class="ed-predict-confirmed-row">
          <span class="ed-predict-result">${home} ${edState.homeScore} – ${edState.awayScore} ${away}</span>
          <button class="ed-predict-edit-btn" id="edPredictEditBtn" type="button">✏️ Edit</button>
        </div>
      </div>`;
  }
  return `
    <div class="ed-prediction-zone">
      <div class="ed-predict-label">YOUR PREDICTION</div>
      <div class="ed-predict-subcard">
        <div class="ed-predict-question">What will the final score be?</div>
        <div class="ed-steppers-row">
          <div class="ed-stepper-col">
            <span class="ed-stepper-team-label">${home.slice(0,3).toUpperCase()}</span>
            <div class="ed-stepper-controls">
              <button class="ed-stepper-btn" data-step="home" data-dir="-1" type="button">–</button>
              <div class="ed-stepper-value">${edState.homeScore}</div>
              <button class="ed-stepper-btn" data-step="home" data-dir="1" type="button">+</button>
            </div>
          </div>
          <span class="ed-stepper-sep">–</span>
          <div class="ed-stepper-col">
            <span class="ed-stepper-team-label">${away.slice(0,3).toUpperCase()}</span>
            <div class="ed-stepper-controls">
              <button class="ed-stepper-btn" data-step="away" data-dir="-1" type="button">–</button>
              <div class="ed-stepper-value">${edState.awayScore}</div>
              <button class="ed-stepper-btn" data-step="away" data-dir="1" type="button">+</button>
            </div>
          </div>
        </div>
        <button class="ed-predict-confirm-btn" id="edConfirmBtn" type="button">
          Confirm prediction →
        </button>
      </div>
    </div>`;
}

function renderEventInfo(event) {
  const chips = event.amenities.map(([i, l]) =>
    `<div class="ed-amenity-chip"><span>${i}</span><span>${l}</span></div>`
  ).join('');
  const amenityHtml = chips
    ? `<div class="ed-amenity-scroll"><div class="ed-amenity-row">${chips}</div></div>` : '';

  const dist = event.venueAddress || event.venueDistance;
  const attendLabel = event.isPast
    ? `${event.attendeeCount} attended`
    : event.attendeeCount ? `${event.attendeeCount} going` : '';

  const rightHtml = event.isPast
    ? `<button class="ed-recap-strip-btn" id="edRecapBtn" type="button">✨ AI Recap</button>`
    : attendLabel
      ? `<div class="ed-venue-count-pill">👥 ${attendLabel}</div>`
      : '';

  return `
    <div class="ed-venue-strip">
      <div class="ed-venue-main-row">
        <div class="ed-venue-icon-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
                  stroke="#75AADB" stroke-width="2" stroke-linejoin="round"/>
            <polyline points="9 22 9 12 15 12 15 22"
                      stroke="#75AADB" stroke-width="2" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="ed-venue-text">
          <div class="ed-venue-name">${event.venueName}</div>
          ${dist ? `<div class="ed-venue-dist">${dist}</div>` : ''}
        </div>
        ${rightHtml}
      </div>
      ${amenityHtml}
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

function _photoCard(post) {
  const handle    = post.uploader_handle || post.handle || '@fan';
  const likes     = post.likes_count != null ? post.likes_count : 0;
  const likedByMe = post._likedByMe || false;
  const mediaType = post.media_type || post.type || 'photo';
  const realUrl   = post.url && !post.url.startsWith('/mock') ? _mediaUrl(post.url) : null;
  const mediaId   = post.id || '';

  if (realUrl && mediaType === 'video') {
    return `
      <div class="ed-photo-card" data-media-id="${mediaId}">
        <video src="${realUrl}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"></video>
        <div class="ed-photo-overlay"></div>
        <span class="ed-photo-user">${handle}</span>
        <button class="ed-photo-like hype-post__like-btn${likedByMe ? ' is-liked' : ''}"
                data-media-id="${mediaId}" type="button">
          <span class="hype-post__action-icon">${likedByMe ? '❤️' : '🤍'}</span><span class="hype-post__like-count">${likes}</span>
        </button>
      </div>`;
  }
  if (realUrl) {
    return `
      <div class="ed-photo-card" data-media-id="${mediaId}">
        <img src="${realUrl}" alt="" loading="lazy">
        <div class="ed-photo-overlay"></div>
        <span class="ed-photo-user">${handle}</span>
        <button class="ed-photo-like hype-post__like-btn${likedByMe ? ' is-liked' : ''}"
                data-media-id="${mediaId}" type="button">
          <span class="hype-post__action-icon">${likedByMe ? '❤️' : '🤍'}</span><span class="hype-post__like-count">${likes}</span>
        </button>
      </div>`;
  }
  return `
    <div class="ed-photo-card" data-media-id="${mediaId}">
      <span class="ed-photo-empty-icon">${mediaType === 'video' ? '▶️' : '📸'}</span>
      <span class="ed-photo-user">${handle}</span>
    </div>`;
}

function _milestoneLabel(posts) {
  if (!edEvent.kickoffIso || !posts.length) return null;
  const kickoff = new Date(edEvent.kickoffIso).getTime();
  const firstTs = new Date(posts[0].uploaded_at || 0).getTime();
  const delta   = firstTs - kickoff;
  if (delta < -5 * 60 * 1000) return 'Pre-match';   // >5 min before kickoff
  if (delta < 70 * 60 * 1000) return 'First half';  // up to 70 min after
  if (delta < 110 * 60 * 1000) return 'Second half';
  return 'Post-match';
}

function renderHypeFeed(posts) {
  if (!posts.length) {
    return `
      <div class="ed-timeline">
        <div class="ed-milestone">
          <div class="ed-milestone-icon">📸</div>
          <div class="ed-milestone-content">
            <div class="ed-milestone-label">No photos yet</div>
            <div style="font-size:11px;color:#475569">Be the first to upload</div>
          </div>
        </div>
      </div>`;
  }

  // Group by upload time relative to kickoff.
  // Pre-match:    uploaded before kickoff
  // During match: kickoff → kickoff + 2 h  (covers 90 min + stoppage)
  // Post-match:   uploaded more than 2 h after kickoff
  const groups = [];
  const kickoff = edEvent.kickoffIso ? new Date(edEvent.kickoffIso).getTime() : null;
  const MATCH_DURATION_MS = 2 * 60 * 60 * 1000; // 2 hours

  if (!kickoff) {
    groups.push({ label: 'Match moments', icon: '⚽', posts });
  } else {
    const ts = p => new Date(p.uploaded_at || 0).getTime();
    const pre    = posts.filter(p => ts(p) < kickoff);
    const during = posts.filter(p => ts(p) >= kickoff && ts(p) < kickoff + MATCH_DURATION_MS);
    const post   = posts.filter(p => ts(p) >= kickoff + MATCH_DURATION_MS);
    if (pre.length)    groups.push({ label: 'Pre-match',     icon: '🍺', posts: pre });
    if (during.length) groups.push({ label: 'During match',  icon: '⚽', posts: during });
    if (post.length)   groups.push({ label: 'Post-match',    icon: '🎉', posts: post });
    if (!groups.length) groups.push({ label: 'Match moments', icon: '⚽', posts });
  }

  const milestonesHtml = groups.map(g => `
    <div class="ed-milestone">
      <div class="ed-milestone-icon">${g.icon}</div>
      <div class="ed-milestone-content">
        <div class="ed-milestone-label">${g.label}</div>
        <div class="ed-photo-scroll-wrap">
          <div class="ed-photo-scroll">
            <div class="ed-photo-row">${g.posts.map(_photoCard).join('')}</div>
          </div>
          <div class="ed-photo-fade"></div>
        </div>
      </div>
    </div>`).join('');

  return `
    <div class="ed-timeline">
      <div class="ed-timeline-line"></div>
      ${milestonesHtml}
    </div>`;
}

function renderRecapBtn() {
  if (!edEvent.isPast) return '';
  const hasVideo = !!edEvent.recapVideoUrl;
  return `
    <div class="ed-video-cta">
      <button class="ed-video-cta__btn${hasVideo ? ' is-generated' : ''}"
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
  const photoCount = hypePosts.length;

  container.innerHTML =
    renderBackRow(edEvent) +
    renderMatchHeader(edEvent.match) +
    renderEventInfo(edEvent) +
    renderRecapBtn() +
    `<div class="ed-feed-header">
       <div class="ed-feed-title">Community moments</div>
       <div class="ed-feed-sub">${photoCount ? `${photoCount} photo${photoCount !== 1 ? 's' : ''} from fans` : 'Photos and videos from fans at this event'}</div>
     </div>` +
    renderHypeFeed(hypePosts) +
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
    if (ms.status === 'live') _startLiveSync(edEvent.id);
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
  _stopLiveSync();
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

  if (e.target.closest('#edPredictEditBtn')) {
    edState.predictSent = false;
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
