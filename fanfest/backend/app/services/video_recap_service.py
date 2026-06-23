"""FanFest adapter: maps FanFest domain data into the video recap pipeline."""

from __future__ import annotations

from datetime import timezone
from pathlib import Path
from urllib.parse import unquote

from app.core.config import settings
from app.db.database import get_session
from app.db.models import EventModel
from app.schemas.events import VideoRecapResponse
from app.services import match_state as match_state_service
from app.services import photos_service

from .video_recap.config import RecapConfig
from .video_recap.models import (
    ChampionshipContext,
    EventDetail as PipelineEventDetail,
    EventImage,
    EventInput,
    EventSummary as PipelineEventSummary,
    MatchState as PipelineMatchState,
    MediaComment,
    MediaItem,
)
from .video_recap.pipeline import run_from_input

_LOCAL_URL_PREFIX = "http://localhost:8000/"
MEDIA_ROOT = Path("media")


def _url_to_local_path(url: str) -> str | None:
    """Convert http://localhost:8000/media/... → media/... (relative path).

    URL-decodes percent-encoded characters (e.g. %20 → space) so the path
    matches the actual filename on disk. Returns None for external URLs.
    """
    if url.startswith(_LOCAL_URL_PREFIX):
        return unquote(url[len(_LOCAL_URL_PREFIX):])
    if url.startswith("/media/"):
        return unquote(url[1:])
    return None


def _ensure_utc(dt) -> object:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _resolve_local_image(p) -> str | None:
    """Local filesystem path for a photo, fetching from S3 if needed.

    The moviepy renderer reads images off disk, so in s3 mode each source
    photo is downloaded to a local temp dir before rendering.
    """
    local_path = _url_to_local_path(p.url)
    if local_path is not None:
        return local_path
    if settings.media_storage_backend == "s3":
        from app.services import s3_storage

        key = s3_storage.key_from_url(p.url)
        if key:
            dest = MEDIA_ROOT / "_recap_src" / key
            try:
                s3_storage.download_to(key, dest)
                return str(dest)
            except Exception:
                return None
    return None


def _build_event_input(event: EventModel, state, photos: list) -> EventInput:
    home = event.home_team
    away = event.away_team
    competition = event.competition or "Copa"

    if state.home_score > state.away_score:
        result_label = f"{home} {state.home_score} - {state.away_score} {away}"
    elif state.away_score > state.home_score:
        result_label = f"{away} {state.away_score} - {state.home_score} {home}"
    else:
        result_label = f"Empate {state.home_score} - {state.away_score}"

    media_items = []
    event_images = []

    for p in photos:
        local_path = _resolve_local_image(p)

        media_items.append(
            MediaItem(
                id=p.id,
                url=p.url,
                uploaded_at=_ensure_utc(p.uploaded_at),
                media_type=getattr(p, "media_type", "photo"),
                caption=getattr(p, "caption", None),
                likes_count=getattr(p, "likes_count", 0),
                comments=[
                    MediaComment(text=c.text if hasattr(c, "text") else str(c))
                    for c in (getattr(p, "comments", []) or [])
                ],
                uploader_name=getattr(p, "uploader_name", ""),
            )
        )

        if local_path is None:
            continue
        if getattr(p, "media_type", "photo") != "photo":
            continue

        event_images.append(
            EventImage(
                image_ref=local_path,
                date_time=_ensure_utc(p.uploaded_at),
                event_name=f"{home} vs {away}",
                event_description=getattr(p, "caption", None) or f"Fan photo from {event.venue_name}",
                place_location=event.venue_name,
                comments=[
                    c.text if hasattr(c, "text") else str(c)
                    for c in (getattr(p, "comments", []) or [])
                ],
                likes=getattr(p, "likes_count", 0),
            )
        )

    return EventInput(
        event_id=event.id,
        event_summary=PipelineEventSummary(
            id=event.id,
            home_team=home,
            away_team=away,
            home_score=state.home_score,
            away_score=state.away_score,
            kickoff_iso=event.kickoff_iso,
            status=state.status,
            photo_count=len(event_images),
        ),
        event_detail=PipelineEventDetail(
            id=event.id,
            home_team=home,
            away_team=away,
            venue_name=event.venue_name,
            venue_address=event.venue_address,
            organizer=event.organizer,
            kickoff_iso=event.kickoff_iso,
        ),
        match_state=PipelineMatchState(
            event_id=event.id,
            home_team=home,
            away_team=away,
            home_score=state.home_score,
            away_score=state.away_score,
            status=state.status,
            venue=event.venue_name,
        ),
        championship_context=ChampionshipContext(
            club=home,
            competition=competition,
            result_label=result_label,
            historical_angle=None,
            recap_angle=None,
        ),
        media=media_items,
        event_images=event_images,
    )


def get_video_recap(event_id: str) -> VideoRecapResponse | None:
    with get_session() as session:
        event = session.get(EventModel, event_id)
        if event is None or not event.recap_video_url:
            return None
        return VideoRecapResponse(event_id=event_id, video_url=event.recap_video_url)


def generate_video_recap(event_id: str) -> VideoRecapResponse:
    with get_session() as session:
        event = session.get(EventModel, event_id)
        if event is None:
            raise ValueError(f"Event {event_id} not found")
        if event.recap_video_url:
            return VideoRecapResponse(event_id=event_id, video_url=event.recap_video_url)

        state = match_state_service.get_state(event_id)
        photos = photos_service.list_photos(event_id)

        event_input = _build_event_input(event, state, photos)

        if not event_input.event_images:
            raise ValueError(
                "No renderable local photos found for this event. "
                "Upload photos via the Hype Wall first."
            )

        out_dir = MEDIA_ROOT / "recap" / event_id
        config = RecapConfig(
            output_dir=out_dir,
            base_dir=Path("."),
            language="es",
            provider="auto",
        )

        run_from_input(event_input, config)

        local_video = out_dir / "recap-video.mp4"
        if settings.media_storage_backend == "s3":
            from app.services import s3_storage

            key = f"media/recap/{event_id}/recap-video.mp4"
            video_url = s3_storage.upload_file(key, "video/mp4", local_video)
        else:
            video_url = f"/media/recap/{event_id}/recap-video.mp4"
        event.recap_video_url = video_url

    return VideoRecapResponse(event_id=event_id, video_url=video_url)
