from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.schemas.events import (
    AttendeeOut,
    CheckinRequest,
    CheckinResponse,
    EventDetail,
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

router = APIRouter(prefix="/events", tags=["events"])


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
