# FEST-08: Hype Wall — Media Upload with Caption, Likes & Comments

## User Story

**As a** fan attending a FanFest event  
**I want** to upload photos or videos with a caption and interact with other fans' posts  
**So that** I can share my experience in real time and feel connected to the fan community

---

## Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Product Owner | FanFest HQ | Acceptance, scope |
| Developer | Paula Canepa | Implementation |
| End User | Fan attendees | Upload, like, comment |

---

## Success Criteria

1. A checked-in fan can upload a photo or video with an optional caption from the event detail view.
2. All fans can see the feed of posts for an event, ordered by most recent.
3. Any fan can like/unlike a post; like count is visible on the card.
4. Any fan can add a text comment to a post; comments are listed below the post.
5. Uploader identity is shown: display name, @handle, and avatar initial/color.
6. In local dev, media files are persisted to disk (`fanfest/backend/media/`) and served via a static URL.
7. `ruff check .` passes; all existing tests pass; new tests cover the added routes.

---

## Acceptance Criteria

### Scenario 1: Happy path — upload photo with caption

```gherkin
Given a checked-in fan with user_id "user_003" and handle "@carlos_fan"
And an active event "evt-004"
When the fan POSTs to /api/v1/events/evt-004/media with a JPEG file and caption "¡Llegando al fan fest! El ambiente está increíble 🔥"
Then the response status is 201
And the response body includes the media URL, caption, uploader handle, and uploaded_at
And the media file is saved to fanfest/backend/media/evt-004/{uuid}.jpg
And subsequent GET /api/v1/events/evt-004/media returns the new post in the feed
```

### Scenario 2: Like and unlike a post

```gherkin
Given a media post "media-001" in event "evt-004" with 0 likes
When any fan POSTs to /api/v1/events/evt-004/media/media-001/likes with {"user_id": "user_005"}
Then the response is 200 with likes_count: 1
When the same fan POSTs again (toggle)
Then the response is 200 with likes_count: 0
```

### Scenario 3: Add a comment

```gherkin
Given a media post "media-001" in event "evt-004"
When a fan POSTs to /api/v1/events/evt-004/media/media-001/comments with {"user_id": "user_002", "text": "¡Qué fotos! 🙌"}
Then the response is 201 with the comment id, text, user handle, and created_at
And GET /api/v1/events/evt-004/media/media-001/comments returns the new comment
```

### Scenario 4: Upload rejected — user not checked in

```gherkin
Given a fan with user_id "user_999" who is NOT checked in
When they attempt to POST a file to /api/v1/events/evt-004/media
Then the response status is 403
And the body detail is "User is not checked in"
```

### Scenario 5: Upload rejected — unsupported file type

```gherkin
Given a checked-in fan
When they upload a .pdf file to /api/v1/events/evt-004/media
Then the response status is 415
And the body detail is "Unsupported media type. Only JPEG, PNG, GIF, MP4, MOV allowed."
```

### Scenario 6: Caption validation

```gherkin
Given a checked-in fan uploading a photo
When the caption exceeds 280 characters
Then the response status is 422
And the body contains a validation error for the "caption" field
```

### Scenario 7: Video upload (local dev)

```gherkin
Given a checked-in fan
When they POST an MP4 file to /api/v1/events/evt-004/media
Then the response status is 201
And media_type is "video"
And the URL points to the locally served static file
```

---

## Technical Context

### Current State

- `Photo` entity (`app/models/entities.py`): `id`, `event_id`, `url`, `uploader_id`, `uploader_name`, `uploaded_at` — no caption, no likes, no comments, no handle.
- `POST /events/{id}/photos` (multipart): saves to local mock URL or Google Drive. 403 if not checked-in.
- `GET /events/{id}/photos`: returns flat list of photos.
- `photos_service.py`: two backends (`_upload_mock` for local, `_upload_to_drive` for Drive). Google Drive is already wired via service account.
- No video support. No social interactions.

### Proposed Changes

#### 1. Entity layer (`app/models/entities.py`)

```python
@dataclass
class Comment:
    id: str
    photo_id: str          # references MediaPost.id
    user_id: str
    user_name: str
    user_handle: str       # e.g. "@carlos_fan"
    text: str
    created_at: datetime

@dataclass
class Photo:               # renamed intention: MediaPost
    id: str
    event_id: str
    url: str
    media_type: str        # "photo" | "video"
    uploader_id: str
    uploader_name: str
    uploader_handle: str   # e.g. "@carlos_fan"
    uploader_avatar_url: str | None
    uploaded_at: datetime
    caption: str | None = None
    likes_count: int = 0
    liked_by: list[str] = field(default_factory=list)   # list of user_ids
    comments: list[Comment] = field(default_factory=list)
```

> **Note on naming**: keep the class name `Photo` for backwards compatibility with existing seed imports; semantically it now covers video too.

#### 2. Pydantic schemas (`app/schemas/events.py`)

Add:
- `CommentOut` — `id`, `user_id`, `user_name`, `user_handle`, `text`, `created_at`
- `CommentRequest` — `user_id`, `user_name`, `user_handle`, `text` (max 280 chars)
- `LikeRequest` — `user_id`
- `LikeResponse` — `likes_count`, `liked_by_me`
- Update `Photo` Pydantic schema to include `media_type`, `uploader_handle`, `caption`, `likes_count`, `comments: list[CommentOut]`

#### 3. Local dev storage (`app/services/media_storage.py` — new file)

```
fanfest/backend/media/
  {event_id}/
    {uuid}.jpg   ← photos
    {uuid}.mp4   ← videos
```

Mount via FastAPI static files in `main.py`:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/media", StaticFiles(directory="media"), name="media")
```

Served URL: `http://localhost:8000/media/{event_id}/{uuid}.{ext}`

Controlled by `MEDIA_STORAGE_BACKEND=local` env var (default). No new `requirements.txt` entry needed for local.

#### 4. New endpoints (`app/api/v1/endpoints/events.py`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events/{id}/media` | Upload photo or video with caption; multipart; 403 if not checked in; 415 on bad type |
| `GET` | `/events/{id}/media` | List all media posts for event (feed), newest first |
| `POST` | `/events/{id}/media/{media_id}/likes` | Toggle like for user; returns `likes_count` |
| `POST` | `/events/{id}/media/{media_id}/comments` | Add comment; returns created comment |
| `GET` | `/events/{id}/media/{media_id}/comments` | List comments for a post |

> Keep existing `/photos` endpoints unchanged (backwards compatibility with tests and frontend until migration).

#### 5. Service layer (`app/services/photos_service.py`)

- Add `like_media(event_id, media_id, user_id)` — toggle: adds user_id to `liked_by` if not present, removes if present.
- Add `add_comment(event_id, media_id, comment_data)` — appends to `comments` list.
- Add `list_comments(event_id, media_id)` — returns comment list.
- Extend `upload_photo` → `upload_media` accepting `media_type`, `caption`, `uploader_handle`, `uploader_avatar_url`.
- Add local filesystem storage branch (in addition to mock URL and Drive).

#### 6. Seed data (`app/data/seed.py`)

- Add `user_handle` and `caption` fields to the `PHOTOS` seed rows for evt-004 and evt-006.
- Add 2–3 seed `Comment` objects for demo richness.

#### 7. Frontend

- `index.html`: replace `POST /photos` form with media upload modal (file + caption text area).
- `api.js`: add `uploadMedia()`, `likeMedia()`, `addComment()`, `listComments()` functions.
- `main.js`: update Hype Wall render to show caption, like button + count, comment count, @handle.
- `main.css`: style like button (heart toggle), comment input, @handle chip.

### Constraints

- Max file size: 50 MB (enforced at FastAPI middleware level via `content-length` check).
- Allowed MIME types: `image/jpeg`, `image/png`, `image/gif`, `video/mp4`, `video/quicktime`.
- Caption max: 280 characters (Pydantic `Field(max_length=280)`).
- Only checked-in fans can upload. Any fan (checked-in or not) can like and comment.
- Local dev: no cloud credentials required.

---

## Storage Strategy: Local Dev vs Production

### Local Development (required for this ticket)

Save files to `fanfest/backend/media/{event_id}/{uuid}.ext`.  
Serve via `app.mount("/media", StaticFiles(directory="media"), name="media")` in `main.py`.  
URL format: `http://localhost:8000/media/{event_id}/{filename}`  
No new dependencies. Works offline.

---

### Production Storage: Google Drive vs AWS S3

#### Option A: Google Drive (existing integration)

| | |
|---|---|
| **Pros** | Already wired (service account, `google-api-python-client`, `GOOGLE_DRIVE_FOLDER_ID`); no new SDK; re-uses existing auth pattern; familiar Google ecosystem |
| **Cons** | Not designed for app-served media — files need to be explicitly shared publicly to get a direct URL; Google Drive imposes per-user bandwidth quotas and rate limits that break under fan-upload bursts; no video streaming support; `webViewLink` opens Drive UI, not a raw media URL; no CDN path |
| **Verdict** | ✅ Low-effort shortcut. Use only as a transitional option for early demos where traffic is low and file access is manual. Not recommended for public fan-facing media serving. |

#### Option B: AWS S3 (recommended)

| | |
|---|---|
| **Pros** | Industry standard for app-managed media storage; designed for high-concurrency uploads; cheap (~$0.023/GB storage, $0.009/GB transfer); direct `https://{bucket}.s3.amazonaws.com/{key}` public URLs; CDN-ready (CloudFront adds global edge caching); supports presigned upload URLs (browser → S3 directly, no backend bandwidth); video served natively; IAM roles for fine-grained access |
| **Cons** | New AWS account + IAM setup required; new dependency: `boto3` (add to `requirements.txt`); new env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`, `AWS_REGION` |
| **Implementation sketch** | `boto3.client('s3').upload_fileobj(file, bucket, key)` → URL `https://{bucket}.s3.{region}.amazonaws.com/{event_id}/{uuid}.ext` |
| **Verdict** | ✅ **Recommended for production.** Scales with fan traffic, supports video, CDN-ready, standard across the industry. Add `boto3>=1.34.0` to `requirements.txt`. |

#### Switching between backends

Control via `MEDIA_STORAGE_BACKEND` env var:

```
MEDIA_STORAGE_BACKEND=local     # default — filesystem (dev)
MEDIA_STORAGE_BACKEND=drive     # Google Drive (legacy/demo)
MEDIA_STORAGE_BACKEND=s3        # AWS S3 (production)
```

Implement as a strategy pattern in `app/services/media_storage.py`; `photos_service.py` delegates to it based on the env var.

---

## Out of Scope

- Video transcoding or thumbnail generation (future ticket).
- Push notifications on new likes/comments.
- Moderation / content flagging.
- Pagination of the media feed (assume < 100 posts per event for now).
- AWS S3 implementation — this ticket only requires local dev storage. S3 and Drive are documented here for architecture planning; the production backend is a follow-on task.
- Authentication / JWT — not in scope for this project phase.

---

## Edge Cases & Error Handling

| Case | Behavior |
|------|----------|
| File too large (> 50 MB) | HTTP 413 `Payload Too Large` |
| Unsupported MIME type | HTTP 415 with allowed types listed |
| `media_id` not found for like/comment | HTTP 404 `Media not found` |
| Caption > 280 chars | HTTP 422 Pydantic validation error |
| Duplicate like (idempotent) | Toggle: second like removes the first → `likes_count` decremented |
| Empty comment text | HTTP 422 validation error |
| Video upload in local dev | Saved to disk, served as static file; no transcoding |
| `media/` directory does not exist on server start | Create on first upload (`os.makedirs(path, exist_ok=True)`) |

---

## Dependencies

- **Depends on**: FEST-07 (Photo entity + seed data — already merged)
- **Related**: FEST-03 (check-in gate reused for upload authorization)
- **Follow-on**: AWS S3 backend implementation; video thumbnail generation

---

## Definition of Done

### Code Quality
- [ ] `ruff check .` passes (all imports at top of file, no E402)
- [ ] All new functions have type annotations
- [ ] `media/` directory gitignored

### Testing
- [ ] `tests/test_media.py` covers: upload photo (201), upload video (201), 403 not checked in, 415 bad type, 422 caption too long, like toggle, add comment, list comments, 404 unknown media
- [ ] `reset_services` fixture in `conftest.py` resets `_photos` and `_likes` and `_comments` stores
- [ ] External storage (Drive, S3) mocked in tests — no real API calls
- [ ] All 26 existing tests continue to pass

### Frontend
- [ ] Upload modal opens with file picker + caption textarea
- [ ] Feed shows: uploader @handle, time-ago, media (img or video), caption, ❤️ count, 💬 count
- [ ] Like button toggles optimistically
- [ ] All API calls routed through `api.js` (no bare `fetch()` in `main.js`)

### Documentation
- [ ] New env vars documented in `fanfest/backend/.env.example`
- [ ] Storage strategy (local/Drive/S3) documented in a `## Media Storage` section in `README.md` or `CLAUDE.md`

### Review
- [ ] Code reviewed and approved
- [ ] `ruff check .` confirmed in CI

---

## Implementation Notes

1. **Keep `/photos` endpoints** — the existing `POST /events/{id}/photos` and `GET /events/{id}/photos` stay in place. Add new `/media` routes alongside; migrate frontend to use `/media`. Mark `/photos` as deprecated in docstring only.

2. **`uploader_handle` derivation** — for now, derive from `uploader_name` if not provided explicitly (e.g. `"@" + uploader_name.lower().replace(" ", "_")`). Real handle registration is out of scope.

3. **`media/` gitignore** — add `fanfest/backend/media/` to `.gitignore` so test uploads don't pollute the repo.

4. **Like toggle semantics** — a single `POST /likes` call toggles: if the user already liked it, it removes the like. This avoids needing a `DELETE /likes` endpoint and simplifies the frontend.

5. **Static files mount order** — mount `/media` before `app.include_router(...)` calls to avoid path conflicts.

6. **`conftest.py` reset** — add `rs._photos = _seed_photos()` and clear likes/comments dicts in the `autouse` fixture.

---

## References

- UI mockup: screenshot provided (social feed with @handle, time-ago, media, ❤️ 24, 💬 3, "Subir foto / video" CTA)
- Existing service: `fanfest/backend/app/services/photos_service.py`
- Current entity: `fanfest/backend/app/models/entities.py:80` (Photo)
- AWS S3 Python SDK: `boto3` — `s3.upload_fileobj()` + public object URL pattern
- Google Drive already integrated via `google-api-python-client` + service account

---

## Wiki Evidence

- `docs/llm-wiki/wiki/services/backend.md` — existing photo upload flow, Drive integration, CORS config, service patterns
- `docs/llm-wiki/wiki/ARCHITECTURE.md` — single-repo structure, port assignments

## Graph Evidence

- Inspected `app/services/photos_service.py` — `_upload_mock`, `_upload_to_drive`, `list_photos`, `upload_photo` functions; Google Drive branch already wired
- Inspected `app/models/entities.py` — `Photo` dataclass at line 80; no `caption`, `likes_count`, `comments` fields
- Inspected `app/api/v1/endpoints/events.py` — existing `POST/GET /photos` routes at lines 176–198

---

**INVEST Validated**: ✅  
**Scope impact**: ~12 files, 1 service — within Small threshold  
**BDD Scenarios**: 7  
**Recommended split** (optional): FEST-08a = upload + caption + entity + local storage; FEST-08b = likes + comments + cloud storage docs  
**Priority**: High
