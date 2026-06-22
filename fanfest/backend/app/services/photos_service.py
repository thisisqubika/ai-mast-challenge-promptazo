"""Photo/media upload, listing, likes, and comments service."""

import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.data.seed import PHOTOS as _SEED_PHOTOS
from app.db.database import get_session
from app.db.models import PhotoModel
from app.schemas.events import CommentOut, LikeResponse, Photo


def _derive_handle(name: str) -> str:
    return "@" + name.lower().replace(" ", "_")


def _seed_photos() -> dict[str, list[Photo]]:
    result: dict[str, list[Photo]] = {}
    for p in _SEED_PHOTOS:
        handle = p.uploader_handle or _derive_handle(p.uploader_name)
        result.setdefault(p.event_id, []).append(
            Photo(
                id=p.id,
                url=p.url,
                uploader_id=p.uploader_id,
                uploader_name=p.uploader_name,
                uploader_handle=handle,
                uploaded_at=p.uploaded_at,
                media_type=p.media_type,
                caption=p.caption,
            )
        )
    return result


_photos: dict[str, list[Photo]] = _seed_photos()


# ---------------------------------------------------------------------------
# Legacy /photos endpoint — DB-backed
# ---------------------------------------------------------------------------


def upload_photo(
    event_id: str,
    file_bytes: bytes,
    filename: str,
    uploader_id: str,
    uploader_name: str,
) -> Photo:
    if settings.drive_enabled:
        return _upload_to_drive(event_id, file_bytes, filename, uploader_id, uploader_name)
    return _upload_mock(event_id, filename, uploader_id, uploader_name)


def list_photos(event_id: str) -> list[Photo]:
    with get_session() as db:
        rows = db.query(PhotoModel).filter_by(event_id=event_id).all()
        return [
            Photo(
                id=r.id,
                url=r.url,
                uploader_name=r.uploader_name,
                uploaded_at=r.uploaded_at,
            )
            for r in rows
        ]


def _upload_mock(
    event_id: str, filename: str, uploader_id: str, uploader_name: str
) -> Photo:
    photo_id = str(uuid.uuid4())
    url = f"/mock-photos/{event_id}/{filename}"
    now = datetime.now(timezone.utc)
    with get_session() as db:
        db.add(
            PhotoModel(
                id=photo_id,
                event_id=event_id,
                url=url,
                uploader_id=uploader_id,
                uploader_name=uploader_name,
                uploaded_at=now,
            )
        )
    return Photo(id=photo_id, url=url, uploader_name=uploader_name, uploaded_at=now)


# ---------------------------------------------------------------------------
# New /media endpoints — in-memory (likes/comments not in ORM schema)
# ---------------------------------------------------------------------------


def upload_media(
    event_id: str,
    file_bytes: bytes,
    content_type: str,
    filename: str,
    uploader_id: str,
    uploader_name: str,
    uploader_handle: str = "",
    caption: str | None = None,
) -> Photo:
    handle = uploader_handle or _derive_handle(uploader_name)
    if settings.media_storage_backend == "local":
        return _upload_local(
            event_id, file_bytes, content_type, uploader_id, uploader_name, handle, caption
        )
    if settings.media_storage_backend == "drive":
        return _upload_to_drive(event_id, file_bytes, filename, uploader_id, uploader_name)
    return _upload_mock_media(
        event_id, content_type, filename, uploader_id, uploader_name, handle, caption
    )


def list_media(event_id: str) -> list[Photo]:
    posts = _photos.get(event_id)
    if not posts:
        # Rebuild from DB after a server restart
        db_photos = list_photos(event_id)
        if db_photos:
            posts = [
                Photo(
                    id=p.id,
                    url=p.url,
                    uploader_id="",
                    uploader_name=p.uploader_name,
                    uploader_handle="",
                    uploaded_at=p.uploaded_at,
                )
                for p in db_photos
            ]
            _photos[event_id] = posts
    return sorted(posts or [], key=lambda p: p.uploaded_at, reverse=True)


def get_media(event_id: str, media_id: str) -> Photo | None:
    for photo in _photos.get(event_id, []):
        if photo.id == media_id:
            return photo
    return None


def like_media(event_id: str, media_id: str, user_id: str) -> LikeResponse:
    photo = get_media(event_id, media_id)
    if photo is None:
        return None  # type: ignore[return-value]
    if user_id in photo.liked_by:
        photo.liked_by.remove(user_id)
    else:
        photo.liked_by.append(user_id)
    photo.likes_count = len(photo.liked_by)
    return LikeResponse(likes_count=photo.likes_count, liked_by_me=user_id in photo.liked_by)


def add_comment(
    event_id: str,
    media_id: str,
    user_id: str,
    user_name: str,
    user_handle: str,
    text: str,
) -> CommentOut | None:
    photo = get_media(event_id, media_id)
    if photo is None:
        return None
    comment = CommentOut(
        id=str(uuid.uuid4()),
        user_id=user_id,
        user_name=user_name,
        user_handle=user_handle,
        text=text,
        created_at=datetime.now(timezone.utc),
    )
    photo.comments.append(comment)
    return comment


def list_comments(event_id: str, media_id: str) -> list[CommentOut] | None:
    photo = get_media(event_id, media_id)
    if photo is None:
        return None
    return list(photo.comments)


# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------


def _upload_mock_media(
    event_id: str,
    content_type: str,
    filename: str,
    uploader_id: str,
    uploader_name: str,
    uploader_handle: str,
    caption: str | None,
) -> Photo:
    media_type = "video" if content_type.startswith("video/") else "photo"
    photo = Photo(
        id=str(uuid.uuid4()),
        url=f"/mock-media/{event_id}/{filename}",
        uploader_id=uploader_id,
        uploader_name=uploader_name,
        uploader_handle=uploader_handle,
        uploaded_at=datetime.now(timezone.utc),
        media_type=media_type,
        caption=caption,
    )
    _photos.setdefault(event_id, []).append(photo)
    return photo


def _upload_local(
    event_id: str,
    file_bytes: bytes,
    content_type: str,
    uploader_id: str,
    uploader_name: str,
    uploader_handle: str,
    caption: str | None,
) -> Photo:
    from app.services import media_storage

    media_type = media_storage.media_type_for(content_type)
    _, url = media_storage.save_file(event_id, content_type, file_bytes)
    photo_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    photo = Photo(
        id=photo_id,
        url=url,
        uploader_id=uploader_id,
        uploader_name=uploader_name,
        uploader_handle=uploader_handle,
        uploaded_at=now,
        media_type=media_type,
        caption=caption,
    )
    _photos.setdefault(event_id, []).append(photo)
    # Persist to DB so photos survive server restarts
    try:
        from app.db.database import get_session
        from app.db.models import PhotoModel
        with get_session() as db:
            db.add(PhotoModel(
                id=photo_id,
                event_id=event_id,
                url=url,
                uploader_id=uploader_id,
                uploader_name=uploader_name,
                uploaded_at=now,
            ))
            db.commit()
    except Exception:
        pass
    return photo


def _upload_to_drive(
    event_id: str,
    file_bytes: bytes,
    filename: str,
    uploader_id: str,
    uploader_name: str,
) -> Photo:
    import io

    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload

    credentials = service_account.Credentials.from_service_account_file(
        settings.google_service_account_file,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    drive = build("drive", "v3", credentials=credentials)
    metadata = {
        "name": filename,
        "parents": [settings.google_drive_folder_id],
        "description": f"uploader_id:{uploader_id} uploader_name:{uploader_name}",
    }
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="image/jpeg")
    result = (
        drive.files()
        .create(body=metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )
    photo_id = result["id"]
    url = result.get("webViewLink", "")
    now = datetime.now(timezone.utc)
    with get_session() as db:
        db.add(
            PhotoModel(
                id=photo_id,
                event_id=event_id,
                url=url,
                uploader_id=uploader_id,
                uploader_name=uploader_name,
                uploaded_at=now,
            )
        )
    return Photo(id=photo_id, url=url, uploader_name=uploader_name, uploaded_at=now)
