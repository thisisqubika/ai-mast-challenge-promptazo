import unicodedata

from fastapi import APIRouter, Form, HTTPException, Query, UploadFile

from app.schemas.events import (
    AttendeeOut,
    CheckinRequest,
    CheckinResponse,
    EventDetail,
    EventSummary,
    MatchState,
    MatchStateUpdate,
    Photo,
    PhotoList,
    PredictionRequest,
    PredictionResponse,
    RecapRequest,
    RecapResponse,
)
from app.services import events_service
from app.services import match_state as match_state_service
from app.services import photos_service
from app.services import recap_service
from app.services import registry


def _abbr(name: str) -> str:
    """3-char uppercase abbreviation stripping diacritics (e.g. 'México' → 'MEX')."""
    nfd = unicodedata.normalize("NFD", name)
    ascii_only = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return ascii_only[:3].upper()

router = APIRouter(prefix="/events", tags=["events"])


# ---------------------------------------------------------------------------
# Events list (must be before /{event_id} to avoid path-param capture)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[EventSummary])
def list_events(status: str | None = Query(default=None)) -> list[EventSummary]:
    """Return events, optionally filtered by status ('future', 'live', 'past').

    For past events the final score and photo count are joined from match-state
    and photos services so the client can render recap cards without extra calls.
    """
    raw_events = events_service.list_events(status)
    result: list[EventSummary] = []
    for e in raw_events:
        home_score = None
        away_score = None
        photo_count = 0
        recap_id: str | None = e.get("recap_event_id")
        if recap_id:
            try:
                state = match_state_service.get_state(recap_id)
                home_score = state.home_score
                away_score = state.away_score
            except HTTPException:
                pass
            photo_count = len(photos_service.list_photos(e["id"]))
        result.append(
            EventSummary(
                id=e["id"],
                home_team=e["home_team"],
                home_flag=e["home_flag"],
                home_abbr=_abbr(e["home_team"]),
                away_team=e["away_team"],
                away_flag=e["away_flag"],
                away_abbr=_abbr(e["away_team"]),
                kickoff_iso=e["kickoff_iso"],
                status=e.get("status", "future"),
                recap_event_id=recap_id,
                home_score=home_score,
                away_score=away_score,
                photo_count=photo_count,
            )
        )
    return result


# ---------------------------------------------------------------------------
# FEST-02: Event detail, predictions, check-in
# ---------------------------------------------------------------------------


@router.get("/{event_id}", response_model=EventDetail)
def get_event_detail(event_id: str) -> EventDetail:
    """Return full detail for a single event."""
    event = events_service.get_event(event_id)

    attendee_set = events_service._attendees.get(event_id, set())
    attendees = [
        AttendeeOut(user_id=uid, name=uid, checked_in=True)
        for uid in attendee_set
    ]

    return EventDetail(
        id=event["id"],
        home_team=event["home_team"],
        home_flag=event["home_flag"],
        away_team=event["away_team"],
        away_flag=event["away_flag"],
        kickoff_iso=event["kickoff_iso"],
        match_start_time=event["match_start_time"],
        venue_name=event["venue_name"],
        venue_address=event["venue_address"],
        organizer=event["organizer"],
        attendees=attendees,
        invite_link=event["invite_link"],
        calendar_link=event["calendar_link"],
        maps_link=event["maps_link"],
    )


@router.post("/{event_id}/predictions", response_model=PredictionResponse)
def create_prediction(event_id: str, body: PredictionRequest) -> PredictionResponse:
    """Submit or overwrite a score prediction for an event."""
    if not body.user_id or not body.user_id.strip():
        raise HTTPException(status_code=400, detail="User identity required")

    result = events_service.upsert_prediction(
        event_id=event_id,
        user_id=body.user_id,
        name=body.name,
        home_score=body.home_score,
        away_score=body.away_score,
    )
    return PredictionResponse(**result)


@router.post("/{event_id}/checkin", response_model=CheckinResponse)
def create_checkin(event_id: str, body: CheckinRequest) -> CheckinResponse:
    """Check a user into an event (idempotent)."""
    if not body.user_id or not body.user_id.strip():
        raise HTTPException(status_code=400, detail="User identity required")

    name = body.name or body.user_id
    result = events_service.checkin_user(
        event_id=event_id,
        user_id=body.user_id,
        name=name,
    )
    return CheckinResponse(**result)


# ---------------------------------------------------------------------------
# FEST-03: Live match state, Hype Wall photos
# ---------------------------------------------------------------------------


@router.get("/{event_id}/match-state", response_model=MatchState)
async def get_match_state(event_id: str) -> MatchState:
    return match_state_service.get_state(event_id)


@router.post("/{event_id}/match-state", response_model=MatchState)
async def update_match_state(event_id: str, body: MatchStateUpdate) -> MatchState:
    if body.action == "goal":
        if not body.player or not body.team or body.minute is None:
            raise HTTPException(
                status_code=422,
                detail="goal action requires player, team, minute",
            )
        return match_state_service.score_goal(
            event_id, body.player, body.team, body.minute
        )
    if body.action == "end":
        return match_state_service.end_match(event_id)
    if body.action == "reset":
        return match_state_service.reset(event_id)
    raise HTTPException(status_code=422, detail="Unknown action")


@router.post("/{event_id}/photos", response_model=Photo, status_code=201)
async def create_photo(
    event_id: str,
    file: UploadFile,
    uploader_id: str = Form(...),
    uploader_name: str = Form(...),
) -> Photo:
    if not registry.is_checked_in(uploader_id):
        raise HTTPException(status_code=403, detail="User is not checked in")
    file_bytes = await file.read()
    return photos_service.upload_photo(
        event_id=event_id,
        file_bytes=file_bytes,
        filename=file.filename or "photo.jpg",
        uploader_id=uploader_id,
        uploader_name=uploader_name,
    )


@router.get("/{event_id}/photos", response_model=PhotoList)
async def list_photos(event_id: str) -> PhotoList:
    photos = photos_service.list_photos(event_id)
    return PhotoList(photos=photos)


# ---------------------------------------------------------------------------
# FEST-04: AI-generated event recap
# ---------------------------------------------------------------------------


@router.get("/{event_id}/recap", response_model=RecapResponse)
async def get_recap(event_id: str) -> RecapResponse:
    """Return a previously generated recap. 404 if none exists yet."""
    recap = recap_service.get_recap(event_id)
    if recap is None:
        raise HTTPException(status_code=404, detail="No recap found for this event")
    return recap


@router.post("/{event_id}/recap", response_model=RecapResponse)
async def create_recap(event_id: str, body: RecapRequest) -> RecapResponse:
    state = match_state_service.get_state(event_id)
    if state.status != "ended":
        raise HTTPException(
            status_code=409,
            detail="Recap is only available after the match ends",
        )
    photos = photos_service.list_photos(event_id)
    return recap_service.generate_recap(event_id, state, photos, body.tone, body.slide_count)
