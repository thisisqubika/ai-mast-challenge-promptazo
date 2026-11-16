#!/usr/bin/env python3
"""Reset the "Club Cultural 2026 · Year Recap" event to its demo starting point.

End state:
  - Event exists (recreated if missing) and is LIVE
  - Score Cba Team 9 - 0 2026, one goal per month (Marzo ... Noviembre),
    each with its timeline label (Bowling, Bingo Musical, ...)
  - Paula (user_003) is checked in, so the upload button shows
  - No photos, no generated recap video (pass --keep-photos to keep photos)

Run from fanfest/backend/ with the backend running (uvicorn --reload):
    /Users/paulacanepa/miniconda3/bin/python reset_club_cultural.py [--keep-photos]

The script restarts the backend (by touching app/main.py, which uvicorn
--reload watches) to clear in-memory caches, then loads the goals through the
API, which also saves them in the database.
"""

import argparse
import json
import shutil
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.db import database  # noqa: E402
from app.db import models  # noqa: E402

EVENT_ID = "8ecc6687-a3d2-423e-b57e-90e9d82e57f3"
API = "http://localhost:8000/api/v1"
HOME_TEAM = "Cba Team"
GOALS = [  # (player, minute, timeline label)
    ("Marzo", 10, "Bowling"),
    ("Abril", 20, "Bingo Musical"),
    ("Mayo", 30, "Desakta2"),
    ("Junio", 40, "Trivia"),
    ("Julio", 50, "Qubika Awards"),
    ("Agosto", 60, "Escape Room"),
    ("Septiembre", 70, "Trekking"),
    ("Octubre", 80, "Pabellon Tornu"),
    ("Noviembre", 90, "Cine & Cena"),
]
USER_ID, USER_NAME = "user_003", "Paula"
AMENITIES = [["🍷", "Vino"], ["🎶", "Música"]]  # tags shown on the event card


def reset_db(keep_photos: bool) -> None:
    database.init_db(settings.database_url)
    models.Base.metadata.create_all(database._engine)
    now = datetime.now(timezone.utc)

    with database.get_session() as db:
        event = db.get(models.EventModel, EVENT_ID)
        if event is None:
            event = models.EventModel(
                id=EVENT_ID,
                home_team=HOME_TEAM,
                home_flag="💙",
                away_team="2026",
                away_flag="🎉",
                venue_name="Club Cultural",
                venue_address="Córdoba",
                organizer="Club Cultural",
                kickoff_iso="2026-11-16T20:00:00Z",
                match_start_time=datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc),
                invite_link="",
                calendar_link="",
                maps_link="",
                competition="Club Cultural 2026 · Year Recap",
                amenities="[]",
            )
            db.add(event)
            print("✓ Event recreated")
        event.status = "live"
        event.home_score = len(GOALS)
        event.away_score = 0
        event.recap_video_url = None
        event.amenities = json.dumps(AMENITIES, ensure_ascii=False)

        reg = (
            db.query(models.RegistrationModel)
            .filter_by(event_id=EVENT_ID, user_id=USER_ID)
            .first()
        )
        if reg is None:
            reg = models.RegistrationModel(
                user_id=USER_ID, event_id=EVENT_ID, user_name=USER_NAME, registered_at=now
            )
            db.add(reg)
        reg.user_name = USER_NAME
        reg.checked_in = True
        reg.checked_in_at = reg.checked_in_at or now

        if not keep_photos:
            n = db.query(models.PhotoModel).filter_by(event_id=EVENT_ID).delete()
            c = db.query(models.PhotoCommentModel).filter_by(event_id=EVENT_ID).delete()
            print(f"✓ Deleted {n} photo row(s) and {c} comment(s)")

    media = BACKEND_DIR / "media"
    shutil.rmtree(media / "recap" / EVENT_ID, ignore_errors=True)
    if not keep_photos:
        shutil.rmtree(media / EVENT_ID, ignore_errors=True)
    print("✓ Event set to live, Paula checked in, recap video cleared")


def restart_backend() -> None:
    """Clear in-memory state (photos cache, match state, recap cache)."""
    (BACKEND_DIR / "app" / "main.py").touch()
    time.sleep(3)
    for _ in range(30):
        try:
            urllib.request.urlopen(f"{API}/events/{EVENT_ID}", timeout=2)
            print("✓ Backend restarted")
            return
        except Exception:
            time.sleep(1)
    sys.exit("✗ Backend did not come back on :8000 — is uvicorn running with --reload?")


def post_match_state(body: dict) -> dict:
    req = urllib.request.Request(
        f"{API}/events/{EVENT_ID}/match-state",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as res:
        return json.load(res)


def load_goals() -> None:
    post_match_state({"action": "reset"})
    for player, minute, label in GOALS:
        state = post_match_state(
            {"action": "goal", "player": player, "team": HOME_TEAM, "minute": minute,
             "label": label}
        )
    print(
        f"✓ {state['home_team']} {state['home_score']}-{state['away_score']} "
        f"{state['away_team']} ({state['status']}), {len(state['goals'])} goals"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--keep-photos", action="store_true", help="don't delete photos")
    args = parser.parse_args()
    reset_db(args.keep_photos)
    restart_backend()
    load_goals()


if __name__ == "__main__":
    main()
