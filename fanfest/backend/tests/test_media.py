"""Tests for FEST-08: /media endpoints — upload, feed, likes, comments."""

import io

from fastapi.testclient import TestClient

from app.main import app

EVENT_ID = "evt-004"
OTHER_USER = "user_005"  # not checked in for evt-004 per seed, but in registry

client = TestClient(app)


def _upload_photo(event_id: str = EVENT_ID, user_id: str = "user_003", caption: str | None = None):
    data = {"uploader_id": user_id, "uploader_name": "Carlos", "uploader_handle": "@carlos_fan"}
    if caption is not None:
        data["caption"] = caption
    return client.post(
        f"/api/v1/events/{event_id}/media",
        data=data,
        files={"file": ("shot.jpg", io.BytesIO(b"fake-image-data"), "image/jpeg")},
    )


# ---------------------------------------------------------------------------
# Scenario 1: upload photo with caption → 201
# ---------------------------------------------------------------------------


def test_upload_photo_returns_201():
    resp = _upload_photo(caption="¡Llegando al fan fest! El ambiente está increíble 🔥")
    assert resp.status_code == 201
    data = resp.json()
    assert data["media_type"] == "photo"
    assert data["uploader_handle"] == "@carlos_fan"
    assert data["caption"] == "¡Llegando al fan fest! El ambiente está increíble 🔥"
    assert "url" in data
    assert "uploaded_at" in data
    assert "id" in data


def test_upload_photo_appears_in_feed():
    _upload_photo(caption="Foto de prueba")
    resp = client.get(f"/api/v1/events/{EVENT_ID}/media")
    assert resp.status_code == 200
    media = resp.json()["media"]
    assert len(media) == 1
    assert media[0]["caption"] == "Foto de prueba"


def test_feed_ordered_newest_first():
    _upload_photo(caption="First")
    _upload_photo(caption="Second")
    resp = client.get(f"/api/v1/events/{EVENT_ID}/media")
    media = resp.json()["media"]
    assert media[0]["caption"] == "Second"


# ---------------------------------------------------------------------------
# Scenario 2: video upload → 201 with media_type "video"
# ---------------------------------------------------------------------------


def test_upload_video_returns_201():
    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media",
        data={"uploader_id": "user_003", "uploader_name": "Carlos"},
        files={"file": ("clip.mp4", io.BytesIO(b"fake-video-data"), "video/mp4")},
    )
    assert resp.status_code == 201
    assert resp.json()["media_type"] == "video"


# ---------------------------------------------------------------------------
# Scenario 4: upload rejected — user not checked in → 403
# ---------------------------------------------------------------------------


def test_upload_not_checked_in_returns_403():
    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media",
        data={"uploader_id": "user_999", "uploader_name": "Stranger"},
        files={"file": ("shot.jpg", io.BytesIO(b"data"), "image/jpeg")},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "User is not checked in"


# ---------------------------------------------------------------------------
# Scenario 5: upload rejected — unsupported file type → 415
# ---------------------------------------------------------------------------


def test_upload_unsupported_type_returns_415():
    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media",
        data={"uploader_id": "user_003", "uploader_name": "Carlos"},
        files={"file": ("doc.pdf", io.BytesIO(b"data"), "application/pdf")},
    )
    assert resp.status_code == 415
    assert "JPEG" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Scenario 6: caption > 280 chars → 422
# ---------------------------------------------------------------------------


def test_upload_caption_too_long_returns_422():
    long_caption = "a" * 281
    resp = _upload_photo(caption=long_caption)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Scenario 2: like toggle
# ---------------------------------------------------------------------------


def test_like_toggle_increments_and_decrements():
    upload_resp = _upload_photo()
    media_id = upload_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media/{media_id}/likes",
        json={"user_id": OTHER_USER},
    )
    assert resp.status_code == 200
    assert resp.json()["likes_count"] == 1
    assert resp.json()["liked_by_me"] is True

    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media/{media_id}/likes",
        json={"user_id": OTHER_USER},
    )
    assert resp.status_code == 200
    assert resp.json()["likes_count"] == 0
    assert resp.json()["liked_by_me"] is False


def test_like_unknown_media_returns_404():
    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media/no-such-id/likes",
        json={"user_id": OTHER_USER},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Scenario 3: add comment
# ---------------------------------------------------------------------------


def test_add_comment_returns_201():
    upload_resp = _upload_photo()
    media_id = upload_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media/{media_id}/comments",
        json={"user_id": "user_002", "user_name": "Bob", "user_handle": "@bob_ftw", "text": "¡Qué fotos! 🙌"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["text"] == "¡Qué fotos! 🙌"
    assert data["user_handle"] == "@bob_ftw"
    assert "id" in data
    assert "created_at" in data


def test_list_comments_returns_added_comment():
    upload_resp = _upload_photo()
    media_id = upload_resp.json()["id"]

    client.post(
        f"/api/v1/events/{EVENT_ID}/media/{media_id}/comments",
        json={"user_id": "user_002", "text": "Primer comentario"},
    )
    resp = client.get(f"/api/v1/events/{EVENT_ID}/media/{media_id}/comments")
    assert resp.status_code == 200
    comments = resp.json()
    assert len(comments) == 1
    assert comments[0]["text"] == "Primer comentario"


def test_comment_on_unknown_media_returns_404():
    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media/no-such-id/comments",
        json={"user_id": "user_002", "text": "Hola"},
    )
    assert resp.status_code == 404


def test_list_comments_unknown_media_returns_404():
    resp = client.get(f"/api/v1/events/{EVENT_ID}/media/no-such-id/comments")
    assert resp.status_code == 404


def test_comment_handle_derived_when_missing():
    upload_resp = _upload_photo()
    media_id = upload_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media/{media_id}/comments",
        json={"user_id": "user_002", "user_name": "Ana López", "text": "Buenísimo!"},
    )
    assert resp.status_code == 201
    assert resp.json()["user_handle"] == "@ana_lópez"


def test_empty_comment_text_returns_422():
    upload_resp = _upload_photo()
    media_id = upload_resp.json()["id"]

    resp = client.post(
        f"/api/v1/events/{EVENT_ID}/media/{media_id}/comments",
        json={"user_id": "user_002", "text": ""},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Liked_by not exposed in media list response
# ---------------------------------------------------------------------------


def test_liked_by_not_in_media_response():
    upload_resp = _upload_photo()
    media_id = upload_resp.json()["id"]
    client.post(
        f"/api/v1/events/{EVENT_ID}/media/{media_id}/likes",
        json={"user_id": OTHER_USER},
    )
    resp = client.get(f"/api/v1/events/{EVENT_ID}/media")
    media = resp.json()["media"]
    assert "liked_by" not in media[0]
