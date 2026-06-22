/* FEST-10: Create New Event screen */

import { createEvent } from './api.js';

const $ = (id) => document.getElementById(id);

// ── Screen navigation ─────────────────────────────────────────────────────────

function showCreateScreen() {
  const home = document.querySelector('.phone > .scroll');
  const view = $('createEventView');
  ['eventDetailView','recapView','mapaView','misEventosView','createEventView'].forEach(id => {
    const el = document.getElementById(id); if (el) el.hidden = true;
  });
  if (home) home.hidden = true;
  if (view) { view.hidden = false; view.scrollTop = 0; }
}

function showHomeScreen() {
  const home = document.querySelector('.phone > .scroll');
  ['eventDetailView','recapView','mapaView','misEventosView','createEventView'].forEach(id => {
    const el = document.getElementById(id); if (el) el.hidden = true;
  });
  if (home) home.hidden = false;
}

// ── Form rendering ────────────────────────────────────────────────────────────

function renderForm() {
  $('createEventView').innerHTML = `
    <div class="ce-header">
      <button id="ceClose" class="ce-back" type="button" aria-label="Back">
        <i class="ti ti-chevron-left"></i>
      </button>
      <span class="ce-title">Create Fan Fest</span>
      <div></div>
    </div>

    <form id="ceForm" class="ce-form" novalidate>
      <div class="ce-section">Match</div>

      <div class="ce-field">
        <label for="ceHomeTeam">Home Team <span class="ce-req">*</span></label>
        <input id="ceHomeTeam" name="home_team" type="text" required
               placeholder="e.g.: Argentina" autocomplete="off" />
      </div>

      <div class="ce-field">
        <label for="ceAwayTeam">Away Team <span class="ce-req">*</span></label>
        <input id="ceAwayTeam" name="away_team" type="text" required
               placeholder="e.g.: Brazil" autocomplete="off" />
      </div>

      <div class="ce-field">
        <label for="ceCompetition">Competition</label>
        <input id="ceCompetition" name="competition" type="text"
               placeholder="e.g.: Copa América" autocomplete="off" />
      </div>

      <div class="ce-field">
        <label for="ceKickoff">Date & Time <span class="ce-req">*</span></label>
        <input id="ceKickoff" name="kickoff_iso" type="datetime-local" required />
      </div>

      <div class="ce-section">Venue</div>

      <div class="ce-field">
        <label for="ceVenueName">Stadium / Venue <span class="ce-req">*</span></label>
        <input id="ceVenueName" name="venue_name" type="text" required
               placeholder="e.g.: La Bombonera" autocomplete="off" />
      </div>

      <div class="ce-field">
        <label for="ceVenueAddress">Address <span class="ce-req">*</span></label>
        <input id="ceVenueAddress" name="venue_address" type="text" required
               placeholder="e.g.: Brandsen 805, CABA" autocomplete="off" />
      </div>

      <div class="ce-field">
        <label for="ceOrganizer">Organizer <span class="ce-req">*</span></label>
        <input id="ceOrganizer" name="organizer" type="text" required
               placeholder="e.g.: FanFest BA" autocomplete="off" />
      </div>

      <div class="ce-section">Amenities</div>

      <div class="ce-amenities" id="ceAmenities">
        ${[
          ['🍺','Beers'],['📺','Screen'],['🎶','DJ'],['🍔','Food'],
          ['🪑','Tables'],['🚗','Parking'],['🍷','Wine'],['☕','Coffee'],
          ['🎮','Gaming'],['🧃','Non-alcoholic'],
        ].map(([emoji, label]) =>
          `<button type="button" class="ce-tag" data-emoji="${emoji}" data-label="${label}">
            <span>${emoji}</span> ${label}
          </button>`
        ).join('')}
      </div>

      <div id="ceError" class="ce-error" hidden></div>

      <button id="ceSubmit" type="submit" class="ce-submit">Create Event</button>
    </form>

    <!-- Success overlay — shown after creation -->
    <div id="ceSuccess" class="ce-success" hidden>
      <div class="ce-success__icon">🎉</div>
      <div class="ce-success__title">Event Created!</div>
      <div class="ce-success__sub">Your fan fest has been scheduled.</div>
      <button id="ceOpenEvent" class="ce-success__btn-primary">View Event</button>
      <button id="ceGoHome" class="ce-success__btn-secondary">Back to Home</button>
    </div>
  `;

  $('ceClose').addEventListener('click', navigateBackHome);
  $('ceForm').addEventListener('submit', handleSubmit);
  $('ceAmenities').addEventListener('click', (e) => {
    const tag = e.target.closest('.ce-tag');
    if (tag) tag.classList.toggle('ce-tag--on');
  });
}

// ── Submit handler ────────────────────────────────────────────────────────────

async function handleSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const submitBtn = $('ceSubmit');
  const errorEl  = $('ceError');

  const required = ['home_team', 'away_team', 'kickoff_iso', 'venue_name', 'venue_address', 'organizer'];
  for (const name of required) {
    if (!form[name] || !form[name].value.trim()) {
      form[name].focus();
      return;
    }
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Creating…';
  errorEl.hidden = true;

  const amenities = [...$('ceAmenities').querySelectorAll('.ce-tag--on')]
    .map(t => [t.dataset.emoji, t.dataset.label]);

  const data = {
    home_team:     form.home_team.value.trim(),
    away_team:     form.away_team.value.trim(),
    competition:   form.competition.value.trim(),
    kickoff_iso:   form.kickoff_iso.value,
    venue_name:    form.venue_name.value.trim(),
    venue_address: form.venue_address.value.trim(),
    organizer:     form.organizer.value.trim(),
    amenities,
  };

  try {
    const created = await createEvent(data);
    showSuccess(created);
  } catch (err) {
    const msg = err?.detail || (typeof err === 'string' ? err : 'Error creating the event. Please try again.');
    errorEl.textContent = msg;
    errorEl.hidden = false;
    submitBtn.disabled = false;
    submitBtn.textContent = 'Create Event';
  }
}

// ── Success overlay ───────────────────────────────────────────────────────────

function showSuccess(event) {
  const form    = $('ceForm');
  const overlay = $('ceSuccess');
  if (form)    form.hidden    = true;
  if (overlay) overlay.hidden = false;

  $('ceGoHome').addEventListener('click', navigateBackHome);
  $('ceOpenEvent').addEventListener('click', () => {
    navigateBackHome();
    if (typeof window.navigateToEventDetail === 'function') {
      window.navigateToEventDetail({ id: event.id });
    }
  });
}

// ── Navigation ────────────────────────────────────────────────────────────────

export function navigateToCreateEvent() {
  renderForm();
  showCreateScreen();
}

function navigateBackHome() {
  showHomeScreen();
  if (typeof window.loadUpcomingCards === 'function') window.loadUpcomingCards();
  if (typeof window.loadSeleccionCards === 'function') window.loadSeleccionCards();
}

window.navigateToCreateEvent = navigateToCreateEvent;
