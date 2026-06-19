from fastapi import APIRouter, HTTPException

from app.schemas.events import (
    CheckinRequest,
    CheckinResponse,
    EventDetail,
    PredictionRequest,
    PredictionResponse,
    AttendeeOut,
)
from app.services import events_service

router = APIRouter(tags=["events"])


@router.get("/events/{event_id}", response_model=EventDetail)
def get_event_detail(event_id: str) -> EventDetail:
    """Return full detail for a single event."""
    event = events_service.get_event(event_id)

    # Build attendees list from the attendees set stored in service.
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


@router.post("/events/{event_id}/predictions", response_model=PredictionResponse)
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


@router.post("/events/{event_id}/checkin", response_model=CheckinResponse)
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
