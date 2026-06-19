const BASE_URL = "http://localhost:8000";
const API_BASE = `${BASE_URL}/api/v1`;

// ---------------------------------------------------------------------------
// FEST-02: Event detail, predictions, check-in
// ---------------------------------------------------------------------------

async function getEventDetail(eventId) {
  const response = await fetch(`${API_BASE}/events/${eventId}`);
  if (!response.ok) {
    let errBody;
    try {
      errBody = await response.json();
    } catch (_) {
      errBody = response.statusText;
    }
    throw errBody;
  }
  return response.json();
}

async function submitPrediction(eventId, { userId, name, homeScore, awayScore }) {
  const response = await fetch(`${API_BASE}/events/${eventId}/predictions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      name: name,
      home_score: homeScore,
      away_score: awayScore,
    }),
  });
  if (!response.ok) {
    let errBody;
    try {
      errBody = await response.json();
    } catch (_) {
      errBody = response.statusText;
    }
    throw errBody;
  }
  return response.json();
}

async function checkIn(eventId, { userId, name }) {
  const response = await fetch(`${API_BASE}/events/${eventId}/checkin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, name: name }),
  });
  if (!response.ok) {
    let errBody;
    try {
      errBody = await response.json();
    } catch (_) {
      errBody = response.statusText;
    }
    throw errBody;
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// FEST-03: Live match state, Hype Wall photos
// ---------------------------------------------------------------------------

async function fetchMatchState(eventId) {
  const res = await fetch(`${API_BASE}/events/${eventId}/match-state`);
  if (!res.ok) throw new Error(`fetchMatchState ${res.status}`);
  return res.json();
}

async function fetchPhotos(eventId) {
  const res = await fetch(`${API_BASE}/events/${eventId}/photos`);
  if (!res.ok) throw new Error(`fetchPhotos ${res.status}`);
  return res.json();
}

async function uploadPhoto(eventId, file, uploaderId, uploaderName) {
  const form = new FormData();
  form.append("file", file);
  form.append("uploader_id", uploaderId);
  form.append("uploader_name", uploaderName);
  const res = await fetch(`${API_BASE}/events/${eventId}/photos`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`uploadPhoto ${res.status}`);
  return res.json();
}

async function advanceMatchState(eventId, action, data = {}) {
  const res = await fetch(`${API_BASE}/events/${eventId}/match-state`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, ...data }),
  });
  if (!res.ok) throw new Error(`advanceMatchState ${res.status}`);
  return res.json();
}
