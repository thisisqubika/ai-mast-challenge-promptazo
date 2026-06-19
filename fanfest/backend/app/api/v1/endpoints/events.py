from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.schemas.events import MatchState, MatchStateUpdate, Photo, PhotoList, RecapRequest, RecapResponse
from app.services import match_state as match_state_service
from app.services import photos_service
from app.services import recap_service
from app.services import registry

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/{event_id}/match-state", response_model=MatchState)
async def get_match_state(event_id: str) -> MatchState:
    return match_state_service.get_state(event_id)


@router.post("/{event_id}/match-state", response_model=MatchState)
async def update_match_state(event_id: str, body: MatchStateUpdate) -> MatchState:
    if body.action == "goal":
        if not body.player or not body.team or body.minute is None:
            raise HTTPException(status_code=422, detail="goal action requires player, team, minute")
        return match_state_service.score_goal(event_id, body.player, body.team, body.minute)
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
