const BASE_URL = "http://localhost:8000";

async function getEventDetail(eventId) {
  const response = await fetch(`${BASE_URL}/api/v1/events/${eventId}`);
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
  const response = await fetch(`${BASE_URL}/api/v1/events/${eventId}/predictions`, {
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
  const response = await fetch(`${BASE_URL}/api/v1/events/${eventId}/checkin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      name: name,
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
