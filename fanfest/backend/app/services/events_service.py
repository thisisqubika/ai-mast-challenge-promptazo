import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.db.database import get_session
from app.db.models import EventModel, PredictionModel, RegistrationModel
from app.schemas.events import EventCreate

_TEAM_FLAGS: dict[str, str] = {
    "argentina": "🇦🇷",
    "brasil": "🇧🇷",
    "brazil": "🇧🇷",
    "uruguay": "🇺🇾",
    "chile": "🇨🇱",
    "colombia": "🇨🇴",
    "peru": "🇵🇪",
    "perú": "🇵🇪",
    "ecuador": "🇪🇨",
    "paraguay": "🇵🇾",
    "bolivia": "🇧🇴",
    "venezuela": "🇻🇪",
    "mexico": "🇲🇽",
    "méxico": "🇲🇽",
    "estados unidos": "🇺🇸",
    "usa": "🇺🇸",
    "canada": "🇨🇦",
    "canadá": "🇨🇦",
    "españa": "🇪🇸",
    "spain": "🇪🇸",
    "france": "🇫🇷",
    "francia": "🇫🇷",
    "germany": "🇩🇪",
    "alemania": "🇩🇪",
    "england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "portugal": "🇵🇹",
    "italia": "🇮🇹",
    "italy": "🇮🇹",
    "netherlands": "🇳🇱",
    "países bajos": "🇳🇱",
    "holanda": "🇳🇱",
    "belgium": "🇧🇪",
    "bélgica": "🇧🇪",
    "croatia": "🇭🇷",
    "croacia": "🇭🇷",
    "morocco": "🇲🇦",
    "marruecos": "🇲🇦",
    "japan": "🇯🇵",
    "japón": "🇯🇵",
    "south korea": "🇰🇷",
    "corea del sur": "🇰🇷",
    "australia": "🇦🇺",
    "senegal": "🇸🇳",
    "nigeria": "🇳🇬",
    "ghana": "🇬🇭",
    "cameroon": "🇨🇲",
    "camerún": "🇨🇲",
    "switzerland": "🇨🇭",
    "suiza": "🇨🇭",
    "denmark": "🇩🇰",
    "dinamarca": "🇩🇰",
    "sweden": "🇸🇪",
    "suecia": "🇸🇪",
    "poland": "🇵🇱",
    "polonia": "🇵🇱",
    "austria": "🇦🇹",
    "ukraine": "🇺🇦",
    "ucrania": "🇺🇦",
    "turkey": "🇹🇷",
    "turquía": "🇹🇷",
    "costa rica": "🇨🇷",
    "panama": "🇵🇦",
    "panamá": "🇵🇦",
    "honduras": "🇭🇳",
    "guatemala": "🇬🇹",
    "scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "escocia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "gales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "egypt": "🇪🇬",
    "egipto": "🇪🇬",
    "saudi arabia": "🇸🇦",
    "arabia saudita": "🇸🇦",
}


def _flag_for(team_name: str) -> str:
    return _TEAM_FLAGS.get(team_name.lower().strip(), "⚽")


def _event_to_dict(e: EventModel) -> dict:
    return {
        "id": e.id,
        "home_team": e.home_team,
        "home_flag": e.home_flag,
        "away_team": e.away_team,
        "away_flag": e.away_flag,
        "venue_name": e.venue_name,
        "venue_address": e.venue_address,
        "venue_distance": e.venue_distance or "",
        "competition": e.competition or "",
        "amenities": json.loads(e.amenities) if e.amenities else [],
        "organizer": e.organizer,
        "kickoff_iso": e.kickoff_iso,
        "match_start_time": e.match_start_time,
        "invite_link": e.invite_link,
        "calendar_link": e.calendar_link,
        "maps_link": e.maps_link,
        "status": e.status,
        "recap_event_id": e.recap_event_id,
        "recap_video_url": e.recap_video_url,
    }


def list_events(status: str | None = None) -> list[dict]:
    with get_session() as db:
        query = db.query(EventModel)
        if status:
            query = query.filter(EventModel.status == status)
        return [_event_to_dict(e) for e in query.all()]


def get_event(event_id: str) -> dict:
    with get_session() as db:
        event = db.query(EventModel).filter_by(id=event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_dict(event)


def count_registrations(event_id: str) -> int:
    with get_session() as db:
        return db.query(RegistrationModel).filter_by(event_id=event_id).count()


def get_attendees(event_id: str) -> list[dict]:
    with get_session() as db:
        rows = (
            db.query(RegistrationModel)
            .filter_by(event_id=event_id, checked_in=True)
            .all()
        )
        return [{"user_id": r.user_id, "name": r.user_name or r.user_id} for r in rows]


def upsert_prediction(
    event_id: str,
    user_id: str,
    name: str,
    home_score: int,
    away_score: int,
) -> dict:
    event = get_event(event_id)

    now = datetime.now(tz=timezone.utc)
    match_start = event["match_start_time"]
    if match_start.tzinfo is None:
        match_start = match_start.replace(tzinfo=timezone.utc)
    if now >= match_start:
        raise HTTPException(
            status_code=409,
            detail="Predictions are closed (match has started)",
        )

    with get_session() as db:
        pred = (
            db.query(PredictionModel)
            .filter_by(user_id=user_id, event_id=event_id)
            .first()
        )
        if pred is None:
            pred = PredictionModel(
                user_id=user_id,
                event_id=event_id,
                user_name=name,
                home_score=home_score,
                away_score=away_score,
                submitted_at=datetime.now(timezone.utc),
            )
            db.add(pred)
        else:
            pred.home_score = home_score
            pred.away_score = away_score
            pred.user_name = name
            pred.submitted_at = datetime.now(timezone.utc)

    return {
        "user_id": user_id,
        "event_id": event_id,
        "name": name,
        "home_score": home_score,
        "away_score": away_score,
    }


def checkin_user(event_id: str, user_id: str, name: str) -> dict:
    get_event(event_id)  # raises 404 if missing

    with get_session() as db:
        reg = (
            db.query(RegistrationModel)
            .filter_by(user_id=user_id, event_id=event_id)
            .first()
        )
        now = datetime.now(timezone.utc)
        if reg is None:
            db.add(
                RegistrationModel(
                    user_id=user_id,
                    event_id=event_id,
                    user_name=name,
                    registered_at=now,
                    checked_in=True,
                    checked_in_at=now,
                )
            )
        else:
            reg.checked_in = True
            reg.checked_in_at = now
            reg.user_name = name

    return {"user_id": user_id, "event_id": event_id, "checked_in": True}


# ── Test helpers ──────────────────────────────────────────────────────────────

def has_prediction(user_id: str, event_id: str) -> bool:
    with get_session() as db:
        return (
            db.query(PredictionModel)
            .filter_by(user_id=user_id, event_id=event_id)
            .count()
            > 0
        )


def is_attendee(event_id: str, user_id: str) -> bool:
    with get_session() as db:
        return (
            db.query(RegistrationModel)
            .filter_by(event_id=event_id, user_id=user_id, checked_in=True)
            .count()
            > 0
        )


def count_predictions_for_user(user_id: str) -> int:
    with get_session() as db:
        return db.query(PredictionModel).filter_by(user_id=user_id).count()


def set_match_start_time(event_id: str, dt: datetime) -> None:
    with get_session() as db:
        event = db.query(EventModel).filter_by(id=event_id).first()
        if event:
            event.match_start_time = dt


def create_event(data: EventCreate) -> dict:
    event_id = str(uuid.uuid4())
    iso_norm = data.kickoff_iso.rstrip("Z")
    if "T" in iso_norm:
        date_p, time_p = iso_norm.split("T", 1)
        if time_p.count(":") == 1:
            iso_norm = f"{date_p}T{time_p}:00"
    try:
        match_start = datetime.fromisoformat(iso_norm)
        if match_start.tzinfo is None:
            match_start = match_start.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid kickoff_iso: {exc}") from exc

    home_flag = data.home_flag or _flag_for(data.home_team)
    away_flag = data.away_flag or _flag_for(data.away_team)

    # Ensure stored kickoff_iso always carries UTC designator so clients parse it correctly.
    kickoff_iso_stored = iso_norm + "Z" if iso_norm else data.kickoff_iso

    with get_session() as db:
        event = EventModel(
            id=event_id,
            home_team=data.home_team,
            home_flag=home_flag,
            away_team=data.away_team,
            away_flag=away_flag,
            venue_name=data.venue_name,
            venue_address=data.venue_address,
            organizer=data.organizer,
            kickoff_iso=kickoff_iso_stored,
            match_start_time=match_start,
            invite_link=data.invite_link,
            calendar_link=data.calendar_link,
            maps_link=data.maps_link,
            status="future",
            competition=data.competition,
            venue_distance=data.venue_distance,
            amenities=json.dumps(data.amenities),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return _event_to_dict(event)
