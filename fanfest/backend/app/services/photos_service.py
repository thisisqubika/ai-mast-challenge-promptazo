"""Photo upload/listing service backed by SQLite."""

import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.db.database import get_session
from app.db.models import PhotoModel
from app.schemas.events import Photo


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
