const API_BASE = 'http://localhost:8000/api/v1';

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
  form.append('file', file);
  form.append('uploader_id', uploaderId);
  form.append('uploader_name', uploaderName);
  const res = await fetch(`${API_BASE}/events/${eventId}/photos`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(`uploadPhoto ${res.status}`);
  return res.json();
}

export async function advanceMatchState(eventId, action, data = {}) {
  const res = await fetch(`${API_BASE}/events/${eventId}/match-state`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, ...data }),
  });
  if (!res.ok) throw new Error(`advanceMatchState ${res.status}`);
  return res.json();
}
