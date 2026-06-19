"""Photo upload/listing service with in-memory mock and optional Google Drive backend."""

import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.data.seed import PHOTOS as _SEED_PHOTOS
from app.schemas.events import Photo


def _seed_photos() -> dict[str, list[Photo]]:
    result: dict[str, list[Photo]] = {}
    for p in _SEED_PHOTOS:
        result.setdefault(p.event_id, []).append(
            Photo(id=p.id, url=p.url, uploader_name=p.uploader_name, uploaded_at=p.uploaded_at)
        )
    return result


_photos: dict[str, list[Photo]] = _seed_photos()


def upload_photo(
    event_id: str,
    file_bytes: bytes,
    filename: str,
    uploader_id: str,
    uploader_name: str,
) -> Photo:
    if settings.drive_enabled:
        return _upload_to_drive(event_id, file_bytes, filename, uploader_id, uploader_name)
    return _upload_mock(event_id, filename, uploader_name)


def list_photos(event_id: str) -> list[Photo]:
    if settings.drive_enabled:
        return _list_from_drive(event_id)
    return _photos.get(event_id, [])


def _upload_mock(event_id: str, filename: str, uploader_name: str) -> Photo:
    photo = Photo(
        id=str(uuid.uuid4()),
        url=f"/mock-photos/{event_id}/{filename}",
        uploader_name=uploader_name,
        uploaded_at=datetime.now(timezone.utc),
    )
    _photos.setdefault(event_id, []).append(photo)
    return photo


def _upload_to_drive(
    event_id: str,
    file_bytes: bytes,
    filename: str,
    uploader_id: str,
    uploader_name: str,
) -> Photo:
    import io

    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2 import service_account

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
    result = drive.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
    photo = Photo(
        id=result["id"],
        url=result.get("webViewLink", ""),
        uploader_name=uploader_name,
        uploaded_at=datetime.now(timezone.utc),
    )
    _photos.setdefault(event_id, []).append(photo)
    return photo


def _list_from_drive(event_id: str) -> list[Photo]:
    return _photos.get(event_id, [])
