/* Recap screen — Stories-style 3-phase flow
   Post-match detail → AI loader → Instagram-style slide viewer
   Entry point: window.navigateToRecap(eventId) */

import { fetchRecap, fetchMatchState, getEventDetail, fetchMedia } from './api.js';

// ─── Constants ────────────────────────────────────────────────────────────────

const TONE_MAP = {
  Exciting:  'emocionante',
  Inspiring: 'inspirador',
  Humorous:  'humorístico',
  Nostalgic: 'nostálgico',
};

const SLIDE_BGS = [
  'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=750&h=1624&fit=crop&q=85',
  'https://images.unsplash.com/photo-1431324155629-1a6dae1434d5?w=750&h=1624&fit=crop&q=85',
  'https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=750&h=1624&fit=crop&q=85',
  'https://images.unsplash.com/photo-1560272564-c83b66b1ad12?w=750&h=1624&fit=crop&q=85',
];

const COLLAGE_IMGS = [
  'https://images.unsplash.com/photo-1553778263-73a83bab9b0c?w=400&h=420&fit=crop&q=80',
  'https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=400&h=420&fit=crop&q=80',
  'https://images.unsplash.com/photo-1527829443-1a3f005eb6c1?w=400&h=420&fit=crop&q=80',
  'https://images.unsplash.com/photo-1459865264687-595d652de67e?w=400&h=420&fit=crop&q=80',
];

const PHOTO_ROWS = [
  { icon: 'ti-clock',        label: 'Moments before the goal', count: 14, imgs: [
    'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=280&h=220&fit=crop&q=80',
    'https://images.unsplash.com/photo-1431324155629-1a6dae1434d5?w=280&h=220&fit=crop&q=80',
    'https://images.unsplash.com/photo-1553778263-73a83bab9b0c?w=280&h=220&fit=crop&q=80',
  ]},
  { icon: 'ti-ball-football', label: 'First goal',              count: 16, imgs: [
    'https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=280&h=220&fit=crop&q=80',
    'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=280&h=220&fit=crop&q=80',
    'https://images.unsplash.com/photo-1527829443-1a3f005eb6c1?w=280&h=220&fit=crop&q=80',
  ]},
  { icon: 'ti-confetti',     label: 'Final celebration',       count: 23, imgs: [
    'https://images.unsplash.com/photo-1560272564-c83b66b1ad12?w=280&h=220&fit=crop&q=80',
    'https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=280&h=220&fit=crop&q=80',
    'https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=280&h=220&fit=crop&q=80',
  ]},
];

const PHRASES = [
  'Analyzing the match celebration...',
  'Reviewing the best fan photos...',
  'Capturing the energy of the night...',
  'Reliving every match moment...',
  'AI is crafting your story...',
  'Counting the goals with excitement...',
  'Gathering the highlights...',
];

// ─── Photo helpers ────────────────────────────────────────────────────────────

// Return real photo URL at index (cycling), or a fallback Unsplash URL.
function _bgUrl(idx, fallback) {
  if (_mediaList.length === 0) return fallback;
  return _mediaList[idx % _mediaList.length].url;
}

// Return 4 photo URLs for the community collage, mixing real + fallback.
function _collageUrls() {
  const urls = _mediaList.slice(0, 4).map(m => m.url);
  while (urls.length < 4) urls.push(COLLAGE_IMGS[urls.length % COLLAGE_IMGS.length]);
  return urls;
}

// Render the fan photo strip for the post-match screen.
function _renderPhotoStrip() {
  if (_mediaList.length === 0) {
    return `<div style="padding:0 20px 20px;font-size:13px;color:#475569;text-align:center">No photos uploaded yet.</div>`;
  }
  const cards = _mediaList.slice(0, 12).map(m => `
    <div style="width:140px;height:110px;border-radius:10px;overflow:hidden;flex:none;position:relative">
      <img src="${m.url}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover" loading="lazy">
      <div style="position:absolute;inset:0;background:linear-gradient(to bottom,transparent 40%,rgba(0,0,0,.6))"></div>
      ${m.uploader_handle ? `<span style="position:absolute;bottom:8px;left:8px;font-size:10px;font-weight:700;color:rgba(255,255,255,.65)">${m.uploader_handle}</span>` : ''}
    </div>`).join('');
  return `
    <div style="position:relative;margin:0 -20px">
      <div style="overflow-x:auto;padding:0 20px 4px">
        <div style="display:flex;gap:8px;width:max-content">${cards}</div>
      </div>
      <div style="position:absolute;right:0;top:0;bottom:4px;width:48px;background:linear-gradient(to right,rgba(7,9,13,0),rgba(7,9,13,.92));pointer-events:none"></div>
    </div>`;
}

// ─── State ────────────────────────────────────────────────────────────────────

let _eventId     = null;
let _eventData   = null;
let _matchState  = null;     // match state (goals, teams) for goal-direction detection
let _mediaList   = [];       // real photos fetched from API
let _slideCount  = 5;
let _tone        = 'Exciting';
let _rcCurrent   = 0;        // DOM index of the currently visible slide
let _rcTotal     = 5;        // how many slides are active (1 | 3 | 5)
let _activeIdx   = [];       // which DOM indices are active, e.g. [0,1,2] for 3-slide mode
let _phraseTimer        = null;
let _prevView           = null;
let _floatCtaWasHidden  = true;

// ─── DOM helpers ──────────────────────────────────────────────────────────────

const $r = id => document.getElementById(id);
const homeScroll = () => document.querySelector('.phone > .scroll');

// ─── View management ──────────────────────────────────────────────────────────

// All scrollable phone views — hiding them all before showing one is the only
// safe way to prevent flex-1 siblings from splitting the screen.
function _allPhoneViews() {
  return [
    homeScroll(),
    $r('eventDetailView'),
    $r('mapaView'),
    $r('misEventosView'),
    $r('createEventView'),
    $r('recapView'),
  ].filter(Boolean);
}

function showView() {
  const home     = homeScroll();
  const ed       = $r('eventDetailView');
  const view     = $r('recapView');
  const livebar  = document.querySelector('.live-bar');
  const floatCta = document.getElementById('edFloatCta');
  _prevView          = (ed && !ed.hidden) ? ed : home;
  _floatCtaWasHidden = floatCta ? floatCta.hidden : true;
  _allPhoneViews().forEach(v => { v.hidden = true; });
  if (view)   { view.hidden = false; view.scrollTop = 0; }
  if (livebar)  livebar.hidden  = true;
  if (floatCta) floatCta.hidden = true;
}

function hideView() {
  if (_phraseTimer) { clearInterval(_phraseTimer); _phraseTimer = null; }
  const view     = $r('recapView');
  const floatCta = document.getElementById('edFloatCta');
  _allPhoneViews().forEach(v => { v.hidden = true; });
  if (view)       view.innerHTML = '';
  if (_prevView)  _prevView.hidden = false;
  if (floatCta)   floatCta.hidden  = _floatCtaWasHidden;
  if (typeof window._updateLiveBar === 'function') window._updateLiveBar();
}

// ─── Slide navigation (globals — called from inline onclick in slide HTML) ─────

window._rcGoBack = hideView;

window._rcGoNext = function () {
  const pos = _activeIdx.indexOf(_rcCurrent);
  if (pos < _rcTotal - 1) {
    _rcTransition(_activeIdx[pos + 1], 'forward');
  } else {
    // last slide: pulse share buttons as hint
    document.querySelectorAll('.rc-btn-share').forEach(b => {
      b.style.transform = 'scale(1.04)';
      setTimeout(() => { b.style.transform = ''; }, 180);
    });
  }
};

window._rcGoPrev = function () {
  const pos = _activeIdx.indexOf(_rcCurrent);
  if (pos > 0) _rcTransition(_activeIdx[pos - 1], 'back');
};

function _rcTransition(toIdx, direction) {
  const fromEl = $r(`rc-slide-${_rcCurrent}`);
  const toEl   = $r(`rc-slide-${toIdx}`);
  if (!fromEl || !toEl) return;

  const rm = ['rc-slide--enter-right','rc-slide--enter-left','rc-slide--exit-left','rc-slide--exit-right','rc-slide--current'];
  fromEl.classList.remove(...rm);
  toEl.classList.remove(...rm);

  if (direction === 'forward') {
    fromEl.classList.add('rc-slide--exit-left');
    toEl.classList.add('rc-slide--enter-right');
  } else {
    fromEl.classList.add('rc-slide--exit-right');
    toEl.classList.add('rc-slide--enter-left');
  }

  setTimeout(() => {
    fromEl.classList.remove('rc-slide--exit-left', 'rc-slide--exit-right', 'rc-slide--current');
    toEl.classList.remove('rc-slide--enter-right', 'rc-slide--enter-left');
    toEl.classList.add('rc-slide--current');
    _rcCurrent = toIdx;
    _rcSyncChrome();
  }, 270);
}

function _rcSyncChrome() {
  const activePos = _activeIdx.indexOf(_rcCurrent); // 0-based position in active list
  const display   = activePos + 1;

  for (let i = 0; i < 7; i++) {
    const row = $r(`rc-prog-${i}`);
    if (!row) continue;

    row.innerHTML = '';
    for (let s = 0; s < _rcTotal; s++) {
      const seg = document.createElement('div');
      seg.className = 'rc-seg'
        + (s < activePos ? ' rc-seg--done' : s === activePos ? ' rc-seg--active' : '');
      if (s === activePos) {
        const fill = document.createElement('div');
        fill.className = 'rc-seg-fill';
        seg.appendChild(fill);
      }
      row.appendChild(seg);
    }

    const counter = $r(`rc-counter-${i}`);
    if (counter) counter.textContent = `${display} / ${_rcTotal}`;

    const label = $r(`rc-label-${i}`);
    if (label) label.textContent = `Slide ${display} of ${_rcTotal}`;
  }
}

// ─── Phrase cycling (used by loader) ──────────────────────────────────────────

function _startPhrases() {
  if (_phraseTimer) clearInterval(_phraseTimer);
  let idx = 0;
  const el = $r('rcPhrase');
  if (!el) return;
  el.textContent = PHRASES[0];
  _phraseTimer = setInterval(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(-8px)';
    setTimeout(() => {
      idx = (idx + 1) % PHRASES.length;
      el.textContent = PHRASES[idx];
      el.style.transform = 'translateY(8px)';
      setTimeout(() => { el.style.opacity = '1'; el.style.transform = 'translateY(0)'; }, 40);
    }, 280);
  }, 2400);
}

// ─── Phase 1: Post-match screen ───────────────────────────────────────────────

function renderPostMatch(event) {
  const homeFlag  = event.home_flag || '⚽';
  const awayFlag  = event.away_flag || '⚽';
  const homeTeam  = event.home_team || 'Home';
  const awayTeam  = event.away_team || 'Away';
  const venue     = event.venue_name || '';
  const distance  = event.venue_distance || '';
  const comp      = event.competition || '';
  const homeScore = _matchState?.home_score ?? '–';
  const awayScore = _matchState?.away_score ?? '–';

  const view = $r('recapView');
  view.innerHTML = `
    <div class="rc-postmatch">

      <!-- Header -->
      <div style="flex:none;height:44px;background:#07090D;display:flex;align-items:center;padding:0 16px;position:relative;z-index:10">
        <button id="rcBackBtn" style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;background:rgba(255,255,255,.06);border-radius:10px;border:none;cursor:pointer">
          <i class="ti ti-arrow-left" style="font-size:18px;color:#F1F5F9"></i>
        </button>
        <div style="position:absolute;left:0;right:0;display:flex;justify-content:center;pointer-events:none">
          <span style="font-size:14px;font-weight:700;color:#F1F5F9">${venue}</span>
        </div>
      </div>

      <!-- Scrollable body -->
      <div class="rc-scroll-body">

        <!-- Hero card -->
        <div style="background:#172435;padding:22px 20px 0;border-bottom:1px solid rgba(255,255,255,.05)">
          <div style="display:flex;flex-direction:column;align-items:center;gap:6px;margin-bottom:20px">
            <div style="background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);border-radius:20px;padding:5px 14px">
              <span style="font-size:11px;font-weight:800;color:#94A3B8;letter-spacing:.8px">EVENT FINISHED</span>
            </div>
          </div>

          <!-- Score -->
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:14px">
            <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:8px">
              <div style="width:50px;height:50px;border-radius:50%;background:#07090D;border:1.5px solid rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;font-size:27px">${homeFlag}</div>
              <span style="font-size:14px;font-weight:700;color:#F1F5F9">${homeTeam}</span>
            </div>
            <div style="flex:none;display:flex;align-items:center;gap:8px">
              <div style="background:rgba(255,255,255,.07);border-radius:8px;padding:6px 14px;font-size:28px;font-weight:900;color:#F1F5F9;line-height:1">${homeScore} – ${awayScore}</div>
            </div>
            <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:8px">
              <div style="width:50px;height:50px;border-radius:50%;background:#07090D;border:1.5px solid rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;font-size:27px">${awayFlag}</div>
              <span style="font-size:14px;font-weight:700;color:#F1F5F9">${awayTeam}</span>
            </div>
          </div>
          ${comp ? `<div style="text-align:center;margin-bottom:14px"><span style="font-size:11px;font-weight:500;color:#475569">${comp}</span></div>` : ''}
          <div style="height:1px;background:rgba(255,255,255,.06);margin:0 -20px"></div>
        </div>

        <!-- Venue strip -->
        <div style="margin:12px 20px 0;background:#172435;border-radius:12px;padding:12px 14px">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:36px;height:36px;border-radius:10px;background:rgba(117,170,219,.1);display:flex;align-items:center;justify-content:center;flex:none">
              <i class="ti ti-building-store" style="font-size:18px;color:#75AADB"></i>
            </div>
            <div style="flex:1;min-width:0">
              <div style="font-size:14px;font-weight:700;color:#F1F5F9">${venue}</div>
              ${distance ? `<div style="font-size:12px;color:#475569;margin-top:2px">${distance}</div>` : ''}
            </div>
            <div style="display:flex;align-items:center;gap:5px;background:rgba(117,170,219,.1);border:1px solid rgba(117,170,219,.3);border-radius:20px;padding:5px 10px;flex:none">
              <i class="ti ti-sparkles" style="font-size:13px;color:#75AADB"></i>
              <span style="font-size:12px;font-weight:700;color:#75AADB">AI Recap</span>
            </div>
          </div>
        </div>

        <!-- Photo strip -->
        <div style="margin:20px 20px 12px">
          <div style="font-size:16px;font-weight:800;color:#F1F5F9;margin-bottom:4px">Match moments</div>
          <div style="font-size:12px;color:#475569">${_mediaList.length > 0 ? `${_mediaList.length} photos from fans` : 'Fan photos'}</div>
        </div>
        ${_renderPhotoStrip()}

      </div><!-- /rc-scroll-body -->

      <!-- Sticky CTA -->
      <div style="position:absolute;bottom:0;left:0;right:0;z-index:20;background:rgba(7,9,13,.95);padding:12px 20px 20px">
        <button id="rcGenerateBtn" style="width:100%;height:52px;background:#10B981;border:none;border-radius:14px;font-family:inherit;font-size:15px;font-weight:900;color:#022C22;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px">
          <i class="ti ti-sparkles" style="font-size:17px"></i>
          <span>Generate recap</span>
        </button>
      </div>

      <!-- Customise drawer -->
      <div class="rc-drawer" id="rcDrawer">
        <div class="rc-drawer-sheet">
          <div style="width:32px;height:4px;background:rgba(255,255,255,.15);border-radius:2px;margin:0 auto 20px"></div>
          <div style="margin-bottom:20px">
            <div style="font-size:18px;font-weight:900;color:#F1F5F9;margin-bottom:4px">Customize recap</div>
            <div style="font-size:12px;color:#475569">Choose the tone and number of slides</div>
          </div>

          <!-- Slide count -->
          <div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px">Slides</div>
          <div style="display:flex;background:#07090D;border-radius:12px;padding:4px;margin-bottom:16px" id="rcCntRow">
            <button class="rc-cnt-btn" data-count="3">3</button>
            <button class="rc-cnt-btn rc-cnt-btn--active" data-count="5">5</button>
            <button class="rc-cnt-btn" data-count="7">7</button>
          </div>

          <!-- Tone -->
          <div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px">Tone</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:20px" id="rcToneRow">
            <button class="rc-tone-btn rc-tone-btn--active" data-tone="Exciting">
              <div class="rc-tone-dot" style="background:#75AADB"></div><span>Exciting</span>
            </button>
            <button class="rc-tone-btn" data-tone="Inspiring">
              <div class="rc-tone-dot" style="background:#9B7FD4"></div><span>Inspiring</span>
            </button>
            <button class="rc-tone-btn" data-tone="Humorous">
              <div class="rc-tone-dot" style="background:#E8C25A"></div><span>Humorous</span>
            </button>
            <button class="rc-tone-btn" data-tone="Nostalgic">
              <div class="rc-tone-dot" style="background:#E8845A"></div><span>Nostalgic</span>
            </button>
          </div>

          <button id="rcGenerateNowBtn" style="display:flex;width:100%;height:52px;background:#10B981;border:none;border-radius:14px;font-family:inherit;font-size:15px;font-weight:900;color:#022C22;cursor:pointer;align-items:center;justify-content:center;gap:8px">
            <i class="ti ti-sparkles" style="font-size:17px"></i>
            <span>Generate now</span>
          </button>
        </div>
      </div>

    </div>`;

  // Wire interactions
  $r('rcBackBtn').addEventListener('click', hideView);

  $r('rcGenerateBtn').addEventListener('click', () => {
    $r('rcDrawer').classList.add('rc-drawer--open');
  });

  $r('rcDrawer').addEventListener('click', e => {
    if (e.target === $r('rcDrawer')) $r('rcDrawer').classList.remove('rc-drawer--open');
  });

  $r('rcCntRow').addEventListener('click', e => {
    const btn = e.target.closest('.rc-cnt-btn');
    if (!btn) return;
    $r('rcCntRow').querySelectorAll('.rc-cnt-btn').forEach(b => b.classList.remove('rc-cnt-btn--active'));
    btn.classList.add('rc-cnt-btn--active');
    _slideCount = parseInt(btn.dataset.count, 10);
  });

  $r('rcToneRow').addEventListener('click', e => {
    const btn = e.target.closest('.rc-tone-btn');
    if (!btn) return;
    $r('rcToneRow').querySelectorAll('.rc-tone-btn').forEach(b => b.classList.remove('rc-tone-btn--active'));
    btn.classList.add('rc-tone-btn--active');
    _tone = btn.dataset.tone;
  });

  $r('rcGenerateNowBtn').addEventListener('click', () => {
    $r('rcDrawer').classList.remove('rc-drawer--open');
    _generate();
  });
}

// ─── Phase 2: Loader screen ───────────────────────────────────────────────────

function renderLoader(event) {
  const homeFlag = event.home_flag || '⚽';
  const awayFlag = event.away_flag || '⚽';
  const homeTeam = event.home_team || 'Home';
  const awayTeam = event.away_team || 'Away';
  const venue    = event.venue_name || '';

  $r('recapView').innerHTML = `
    <div class="rc-loader">
      <div class="rc-loader-body">

        <!-- Match pill -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:8px;margin-bottom:48px">
          <div style="background:#172435;border:.5px solid rgba(255,255,255,.08);border-radius:20px;padding:8px 16px;display:inline-flex;align-items:center;gap:8px">
            <span style="font-size:16px">${homeFlag}</span>
            <span style="font-size:13px;font-weight:700;color:#F1F5F9">${homeTeam} vs ${awayTeam}</span>
            <span style="font-size:16px">${awayFlag}</span>
          </div>
          ${venue ? `<div style="font-size:11px;color:#475569">${venue}</div>` : ''}
        </div>

        <!-- Circular arc -->
        <div style="position:relative;width:160px;height:160px;display:flex;align-items:center;justify-content:center;margin-bottom:20px">
          <svg width="160" height="160" style="position:absolute;inset:0" viewBox="0 0 160 160">
            <circle class="rc-arc-track" cx="80" cy="80" r="72"/>
            <circle class="rc-arc-fill" id="rcArc" cx="80" cy="80" r="72"/>
          </svg>
          <div style="width:120px;height:120px;border-radius:50%;background:#172435;border:2px solid rgba(117,170,219,.2);display:flex;align-items:center;justify-content:center;z-index:1">
            <i class="ti ti-sparkles" style="font-size:36px;color:#75AADB"></i>
          </div>
          <div style="position:absolute;inset:0;animation:rcOrbitBall 2.4s linear infinite">
            <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);font-size:22px">⚽</div>
          </div>
          <div style="position:absolute;inset:0;animation:rcOrbitBall 2.4s linear infinite;animation-delay:-.8s;opacity:.55">
            <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);font-size:22px">⚽</div>
          </div>
          <div style="position:absolute;inset:0;animation:rcOrbitBall 2.4s linear infinite;animation-delay:-1.6s;opacity:.28">
            <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);font-size:22px">⚽</div>
          </div>
        </div>

        <div style="font-size:15px;font-weight:700;color:#F1F5F9;margin-bottom:12px;text-align:center">Generating your recap...</div>

        <!-- Progress bar -->
        <div class="rc-loader-bar-track">
          <div class="rc-loader-bar" id="rcBar"></div>
        </div>

        <!-- Rotating phrases -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center">
          <div style="font-size:13px;font-weight:500;color:rgba(241,242,237,.3);margin-bottom:2px">Reviewing the best photos of the night...</div>
          <div class="rc-phrase" id="rcPhrase" style="font-size:14px;font-weight:600;color:#F1F5F9">${PHRASES[0]}</div>
          <div style="font-size:13px;color:rgba(241,242,237,.15)">Capturing the fan energy...</div>
          <div style="font-size:11px;font-style:italic;color:#475569;margin-top:16px">This takes a few seconds · Grab another coffee?</div>
        </div>

      </div>
    </div>`;

  // Start animations (force reflow so CSS animation restarts cleanly)
  const arc = $r('rcArc');
  const bar = $r('rcBar');
  void arc.offsetWidth;
  void bar.offsetWidth;
  arc.classList.add('rc-arc-fill--on');
  bar.classList.add('rc-loader-bar--on');

  _startPhrases();
}

// ─── Phase 3: Slides screen ───────────────────────────────────────────────────

function _chrome(idx) {
  return `
    <div class="rc-slide-chrome">
      <div class="rc-progress-row" id="rc-prog-${idx}"></div>
      <div class="rc-slide-header">
        <button class="rc-slide-back" onclick="window._rcGoBack()">← Back</button>
        <div class="rc-slide-wordmark">TRIBUNA</div>
        <span class="rc-slide-counter" id="rc-counter-${idx}"></span>
      </div>
    </div>`;
}

function _taps(idx) {
  return `
    <div class="rc-tap-prev" onclick="window._rcGoPrev()"></div>
    <div class="rc-tap-next" onclick="window._rcGoNext()"></div>`;
}

function _actions(idx) {
  return `
    <div class="rc-slide-actions">
      <div class="rc-action-row">
        <button class="rc-btn-dl">
          <i class="ti ti-download" style="font-size:18px;color:#F1F5F9"></i>
          <span style="font-size:14px;font-weight:700;color:#F1F5F9">Download</span>
        </button>
        <button class="rc-btn-share">
          <i class="ti ti-share" style="font-size:18px;color:#07090D"></i>
          <span style="font-size:14px;font-weight:900;color:#07090D">Share</span>
        </button>
      </div>
      <div class="rc-slide-label" id="rc-label-${idx}"></div>
    </div>`;
}

function _buildAllSlides(recap, event) {
  const homeFlag = event.home_flag || '⚽';
  const awayFlag = event.away_flag || '⚽';
  const homeTeam = event.home_team || 'Home';
  const awayTeam = event.away_team || 'Away';
  const venue    = event.venue_name || '';
  const homeScore = recap.home_score ?? '–';
  const awayScore = recap.away_score ?? '–';
  const highlights = recap.highlights || [];
  const narrative  = recap.narrative  || '';

  const collage = _collageUrls();
  const h = i => highlights[i] || {};  // safe highlight accessor

  // ── Slide 0: Opening ──────────────────────────────────────────────────────
  const s0 = `
    <div class="rc-slide" id="rc-slide-0">
      <div class="rc-slide-bg" style="background-image:url('${_bgUrl(0, SLIDE_BGS[0])}')">
        <div class="rc-slide-bg-overlay" style="background:linear-gradient(to top,rgba(0,0,0,.88) 0%,rgba(0,0,0,.3) 45%,rgba(0,0,0,.45) 100%)"></div>
      </div>
      ${_chrome(0)}
      <div class="rc-s1-content">
        <div style="font-size:10px;font-weight:800;color:#75AADB;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px">TRIBUNA.AI</div>
        <div style="font-size:30px;font-weight:900;color:#fff;letter-spacing:-.5px;line-height:1.08;margin-bottom:10px">A NIGHT<br>TO REMEMBER</div>
        <div style="font-size:13px;color:rgba(255,255,255,.6);margin-bottom:14px">${homeTeam} ${homeScore} – ${awayScore} ${awayTeam}${venue ? ' · ' + venue : ''}</div>
        ${h(0).description ? `<div style="font-size:13px;color:rgba(255,255,255,.75);font-style:italic;line-height:1.5;margin-bottom:14px">"${h(0).description}"</div>` : ''}
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <div style="background:rgba(255,255,255,.14);border-radius:20px;padding:5px 12px;font-size:11px;font-weight:700;color:#fff">🔥 AI Recap</div>
          <div style="background:rgba(255,255,255,.14);border-radius:20px;padding:5px 12px;font-size:11px;font-weight:700;color:#fff">${homeFlag} ${awayFlag}</div>
        </div>
      </div>
      ${_taps(0)}
      ${_actions(0)}
    </div>`;

  // ── Slide 1: Key highlight ─────────────────────────────────────────────────
  // The backend now anchors highlights to HOME goals, so slide 1 is always
  // a home goal celebration (or a positive fan moment if no goals were scored).
  const homeGoalsScored = (_matchState?.goals || []).filter(
    g => g.team === _matchState?.home_team
  ).length;
  const s1IsGoal  = homeGoalsScored > 0;
  const s1BigText = s1IsGoal ? '¡¡GOOOL!!' : (h(1).label || '');
  const s1BigSize = s1IsGoal ? '52' : '28';
  const s1 = `
    <div class="rc-slide" id="rc-slide-1">
      <div class="rc-slide-bg" style="background-image:url('${_bgUrl(1, SLIDE_BGS[1])}')">
        <div class="rc-slide-bg-overlay" style="background:linear-gradient(to top,rgba(0,2,26,.95) 0%,rgba(0,5,40,.55) 45%,rgba(0,3,30,.65) 100%)"></div>
      </div>
      <div style="position:absolute;top:30%;left:50%;transform:translate(-50%,-50%);width:280px;height:280px;background:radial-gradient(circle,rgba(117,170,219,.22) 0%,transparent 70%);z-index:2;pointer-events:none"></div>
      ${_chrome(1)}
      <div class="rc-s2-content">
        ${h(1).label ? `<div style="font-size:11px;font-weight:800;color:#75AADB;letter-spacing:.1em;text-transform:uppercase;margin-bottom:14px">${h(1).label}</div>` : ''}
        ${s1BigText ? `<div style="font-size:${s1BigSize}px;font-weight:900;color:#fff;letter-spacing:-2px;line-height:.9;margin-bottom:14px;text-shadow:0 0 40px rgba(117,170,219,.55);text-transform:uppercase">${s1BigText}</div>` : ''}
        <div style="width:48px;height:1px;background:rgba(255,255,255,.2);margin:0 auto 16px"></div>
        ${h(1).description ? `<div style="font-size:13px;color:rgba(255,255,255,.7);font-style:italic;line-height:1.55;padding:0 8px">"${h(1).description}"</div>` : ''}
      </div>
      ${_taps(1)}
      ${_actions(1)}
    </div>`;

  // ── Slide 2: Community collage + stats ────────────────────────────────────
  const s2 = `
    <div class="rc-slide" id="rc-slide-2">
      <div class="rc-s3-grid">
        ${collage.map(url => `<div class="rc-s3-cell"><img src="${url}" alt="" loading="lazy"></div>`).join('')}
      </div>
      <div class="rc-s3-overlay"></div>
      ${_chrome(2)}
      <div class="rc-s3-card">
        <div class="rc-s3-card-inner">
          <div style="font-size:10px;font-weight:800;color:#75AADB;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px">✨ Recap generated by Tribuna AI</div>
          <div style="height:.5px;background:rgba(255,255,255,.08);margin-bottom:12px"></div>
          <div style="font-size:18px;font-weight:900;color:#F1F5F9;margin-bottom:14px">The night in numbers</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:14px">
            <div><div style="font-size:24px;font-weight:900;color:#F1F5F9">${homeScore} ⚽ ${awayScore}</div><div style="font-size:11px;color:#475569;margin-top:2px">Final score</div></div>
            <div><div style="font-size:24px;font-weight:900;color:#F1F5F9">${highlights.length} ⚡</div><div style="font-size:11px;color:#475569;margin-top:2px">Highlights</div></div>
            <div><div style="font-size:24px;font-weight:900;color:#F1F5F9">${_mediaList.length} 📸</div><div style="font-size:11px;color:#475569;margin-top:2px">Fan photos</div></div>
            <div><div style="font-size:24px;font-weight:900;color:#F1F5F9">100%</div><div style="font-size:11px;color:#475569;margin-top:2px">Fan vibes</div></div>
          </div>
          ${h(2).description ? `<div style="font-size:11px;color:#75AADB;font-style:italic;line-height:1.4">"${h(2).description}"</div>` : ''}
        </div>
      </div>
      ${_taps(2)}
      ${_actions(2)}
    </div>`;

  // ── Slide 3: Narrative quote ───────────────────────────────────────────────
  // Prefer the AI highlight description; fall back to the narrative paragraph (trimmed).
  const s3desc = h(3).description || (narrative ? (narrative.length > 130 ? narrative.slice(0, 127) + '…' : narrative) : '');
  const s3 = `
    <div class="rc-slide" id="rc-slide-3">
      <div class="rc-slide-bg" style="background-image:url('${_bgUrl(3, SLIDE_BGS[2])}')">
        <div class="rc-slide-bg-overlay" style="background:linear-gradient(to top,rgba(0,0,0,.92) 0%,rgba(0,0,0,.45) 50%,rgba(0,0,0,.6) 100%)"></div>
      </div>
      ${_chrome(3)}
      <div class="rc-s4-content">
        ${h(3).label ? `<div style="font-size:10px;font-weight:800;color:#75AADB;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px">${h(3).label}</div>` : ''}
        <div style="font-size:26px;font-weight:900;color:#fff;line-height:1.1;margin-bottom:12px">The moment<br>captured by AI</div>
        ${s3desc ? `<div style="font-size:13px;color:rgba(255,255,255,.55);line-height:1.55;margin-bottom:20px">"${s3desc}"</div>` : ''}
      </div>
      ${_taps(3)}
      ${_actions(3)}
    </div>`;

  // ── Slide 4: Outro / Share ────────────────────────────────────────────────
  const s4 = `
    <div class="rc-slide" id="rc-slide-4">
      <div class="rc-slide-bg" style="background-image:url('${_bgUrl(4, SLIDE_BGS[3])}')">
        <div class="rc-slide-bg-overlay" style="background:linear-gradient(to top,rgba(0,0,0,.9) 0%,rgba(0,0,0,.5) 50%,rgba(0,0,0,.7) 100%)"></div>
      </div>
      ${_chrome(4)}
      <div class="rc-s5-content">
        <div style="font-size:36px;font-weight:900;color:#fff;letter-spacing:-.5px;line-height:1.05;margin-bottom:16px">Share<br>this moment</div>
        ${(h(4).description || venue) ? `<div style="font-size:14px;color:rgba(255,255,255,.55);line-height:1.5;margin-bottom:32px">${h(4).description || (venue ? 'Tu noche en ' + venue + ' ya es parte de la historia de Tribuna' : '')}</div>` : ''}
        <div style="background:rgba(117,170,219,.12);border:1px solid rgba(117,170,219,.25);border-radius:14px;padding:14px 20px;display:inline-block">
          <div style="font-size:12px;font-weight:700;color:#75AADB;letter-spacing:.06em">🏆 TRIBUNA · ${homeTeam.toUpperCase()}</div>
        </div>
      </div>
      ${_taps(4)}
      ${_actions(4)}
    </div>`;

  // ── Slide 5: Extra highlight ──────────────────────────────────────────────
  const s5 = `
    <div class="rc-slide" id="rc-slide-5">
      <div class="rc-slide-bg" style="background-image:url('${_bgUrl(5, SLIDE_BGS[0])}')">
        <div class="rc-slide-bg-overlay" style="background:linear-gradient(to top,rgba(0,2,26,.95) 0%,rgba(0,5,40,.55) 45%,rgba(0,3,30,.65) 100%)"></div>
      </div>
      ${_chrome(5)}
      <div class="rc-s2-content">
        ${h(5).label ? `<div style="font-size:11px;font-weight:800;color:#75AADB;letter-spacing:.1em;text-transform:uppercase;margin-bottom:14px">${h(5).label}</div>` : ''}
        ${h(5).description ? `<div style="font-size:13px;color:rgba(255,255,255,.7);font-style:italic;line-height:1.55;padding:0 8px">"${h(5).description}"</div>` : ''}
      </div>
      ${_taps(5)}
      ${_actions(5)}
    </div>`;

  // ── Slide 6: Extra highlight ──────────────────────────────────────────────
  const s6 = `
    <div class="rc-slide" id="rc-slide-6">
      <div class="rc-slide-bg" style="background-image:url('${_bgUrl(6, SLIDE_BGS[2])}')">
        <div class="rc-slide-bg-overlay" style="background:linear-gradient(to top,rgba(0,0,0,.92) 0%,rgba(0,0,0,.45) 50%,rgba(0,0,0,.6) 100%)"></div>
      </div>
      ${_chrome(6)}
      <div class="rc-s4-content">
        ${h(6).label ? `<div style="font-size:10px;font-weight:800;color:#75AADB;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px">${h(6).label}</div>` : ''}
        ${h(6).description ? `<div style="font-size:13px;color:rgba(255,255,255,.55);line-height:1.55;margin-bottom:20px">"${h(6).description}"</div>` : ''}
      </div>
      ${_taps(6)}
      ${_actions(6)}
    </div>`;

  return [s0, s1, s2, s3, s4, s5, s6];
}

function renderSlides(recap, event, slideCount) {
  // Which of the 7 DOM elements are active:
  // 3 → [0,1,2], 5 → [0,1,2,3,4], 7 → [0,1,2,3,4,5,6]
  _activeIdx  = Array.from({ length: slideCount }, (_, i) => i);
  _rcTotal    = slideCount;
  _rcCurrent  = 0;

  const allSlides = _buildAllSlides(recap, event);

  $r('recapView').innerHTML = allSlides.join('');

  // Make first active slide visible
  const firstEl = $r(`rc-slide-${_activeIdx[0]}`);
  if (firstEl) firstEl.classList.add('rc-slide--current');

  _rcSyncChrome();
}

// ─── Generation flow ──────────────────────────────────────────────────────────

async function _generate() {
  const event = _eventData;

  // Switch to loader
  renderLoader(event);

  // Minimum loader display time + API call in parallel
  const minWait = new Promise(r => setTimeout(r, 2500));
  const [recapResult] = await Promise.allSettled([
    fetchRecap(_eventId, TONE_MAP[_tone] || 'emocionante', _slideCount),
  ]);
  await minWait;

  if (_phraseTimer) { clearInterval(_phraseTimer); _phraseTimer = null; }

  if (recapResult.status === 'rejected') {
    $r('recapView').innerHTML = `
      <div class="rc-error">
        <button class="rc-error__back" onclick="window._rcGoBack()">← Back</button>
        <div style="font-size:36px">⚠️</div>
        <p style="font-size:14px;font-weight:500;color:#64748b;line-height:1.5;margin:0">Could not generate the recap.<br>Please try again.</p>
      </div>`;
    return;
  }

  renderSlides(recapResult.value, event, _slideCount);
}

// ─── Main entry ───────────────────────────────────────────────────────────────

async function navigateToRecap(eventId) {
  _eventId    = eventId;
  _slideCount = 5;
  _tone       = 'Exciting';
  const view  = $r('recapView');
  if (!view) return;

  showView();

  // Fetch event detail, match state, and media in parallel
  let event, state, mediaRes;
  try {
    [event, state, mediaRes] = await Promise.all([
      getEventDetail(eventId),
      fetchMatchState(eventId),
      fetchMedia(eventId).catch(() => ({ media: [] })),
    ]);
    _mediaList  = (mediaRes?.media || []).filter(m => m.media_type === 'photo' || !m.media_type);
    _matchState = state;
  } catch (_) {
    view.innerHTML = `
      <div class="rc-error">
        <button class="rc-error__back" onclick="window._rcGoBack()">← Back</button>
        <div style="font-size:36px">⚠️</div>
        <p style="font-size:14px;font-weight:500;color:#64748b;line-height:1.5;margin:0">Event not found.</p>
      </div>`;
    return;
  }

  _eventData = event;

  if (state.status !== 'ended') {
    const label = state.status === 'live' ? 'live' : 'pre-match';
    view.innerHTML = `
      <div class="rc-error">
        <button class="rc-error__back" onclick="window._rcGoBack()">← Back</button>
        <div style="font-size:36px">⏱️</div>
        <p style="font-size:14px;font-weight:500;color:#64748b;line-height:1.5;margin:0">Match is ${label}.<br>The recap will be available when it ends.</p>
      </div>`;
    return;
  }

  renderPostMatch(event);
}

window.navigateToRecap = navigateToRecap;
