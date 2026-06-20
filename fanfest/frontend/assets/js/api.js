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

export async function fetchMatchState(eventId) {
  const res = await fetch(`${API_BASE}/events/${eventId}/match-state`);
  if (!res.ok) throw new Error(`fetchMatchState ${res.status}`);
  return res.json();
}

export async function fetchPhotos(eventId) {
  const res = await fetch(`${API_BASE}/events/${eventId}/photos`);
  if (!res.ok) throw new Error(`fetchPhotos ${res.status}`);
  return res.json();
}

export async function uploadPhoto(eventId, file, uploaderId, uploaderName) {
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

// ---------------------------------------------------------------------------
// FEST-08: Hype Wall — media upload, likes, comments
// ---------------------------------------------------------------------------

export async function fetchMedia(eventId) {
  const res = await fetch(`${API_BASE}/events/${eventId}/media`);
  if (!res.ok) throw new Error(`fetchMedia ${res.status}`);
  return res.json();
}

export async function uploadMedia(eventId, file, uploaderId, uploaderName, uploaderHandle, caption) {
  const form = new FormData();
  form.append("file", file);
  form.append("uploader_id", uploaderId);
  form.append("uploader_name", uploaderName);
  if (uploaderHandle) form.append("uploader_handle", uploaderHandle);
  if (caption) form.append("caption", caption);
  const res = await fetch(`${API_BASE}/events/${eventId}/media`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw err;
  }
  return res.json();
}

export async function likeMedia(eventId, mediaId, userId) {
  const res = await fetch(`${API_BASE}/events/${eventId}/media/${mediaId}/likes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error(`likeMedia ${res.status}`);
  return res.json();
}

export async function addComment(eventId, mediaId, userId, userName, userHandle, text) {
  const res = await fetch(`${API_BASE}/events/${eventId}/media/${mediaId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, user_name: userName, user_handle: userHandle, text }),
  });
  if (!res.ok) throw new Error(`addComment ${res.status}`);
  return res.json();
}

export async function listComments(eventId, mediaId) {
  const res = await fetch(`${API_BASE}/events/${eventId}/media/${mediaId}/comments`);
  if (!res.ok) throw new Error(`listComments ${res.status}`);
  return res.json();
}

export async function advanceMatchState(eventId, action, data = {}) {
  const res = await fetch(`${API_BASE}/events/${eventId}/match-state`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, ...data }),
  });
  if (!res.ok) throw new Error(`advanceMatchState ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// FEST-04: AI-generated event recap
// ---------------------------------------------------------------------------

export async function fetchRecap(eventId, tone = 'emocionante', slideCount = 4) {
  const res = await fetch(`${API_BASE}/events/${eventId}/recap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tone, slide_count: slideCount }),
  });
  if (!res.ok) throw new Error(`fetchRecap ${res.status}`);
  return res.json();
}

export async function fetchPastEvents() {
  const res = await fetch(`${API_BASE}/events?status=past`);
  if (!res.ok) throw new Error(`fetchPastEvents ${res.status}`);
  return res.json();
}
