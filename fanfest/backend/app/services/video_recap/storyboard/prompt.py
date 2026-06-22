"""Build the language-aware prompt sent to Claude."""

from __future__ import annotations

import json

from ..config import RecapConfig
from ..models import EventInput, TimelineScene

_LANGUAGE_NAMES = {"en": "English", "es": "Spanish"}


def language_name(code: str) -> str:
    return _LANGUAGE_NAMES.get(code, code)


def build_system_prompt(config: RecapConfig) -> str:
    lang = language_name(config.language)
    return (
        "You are a storyboard director for short, vertical social-media football recap "
        "videos (like a Google Photos or Instagram Reels recap). You receive a club event "
        "and its chronological fan photos with social signals (likes, comments), and you "
        "design a coherent, emotional recap.\n\n"
        f"Write ALL human-readable text (title, scene_title, scene_description, script_text, "
        f"subtitle_text, overlay fields) in {lang}. Keep proper nouns (team names, venue, "
        "city) in their original form.\n\n"
        "On-screen layout (what each field becomes):\n"
        "- subtitle_text -> a caption band at the BOTTOM, shown on every scene. This is the "
        "main running narration; ONE short line (<= ~80 characters), present tense, punchy.\n"
        "- overlay.event -> a BIG title at the TOP. overlay.championship -> a smaller result/"
        "score label under it. overlay.key_moment -> a small highlight badge.\n\n"
        "Overlay discipline (important - avoid clutter):\n"
        "- A photo is often worth more than words. Leave overlay.event, overlay.championship, "
        "and overlay.key_moment NULL on ordinary scenes so the image can breathe.\n"
        "- Use overlay.event ONLY for high-impact beats: the opening scene, the peak, and the "
        "closing. Keep it very short and punchy (<= ~22 chars).\n"
        "- Set overlay.championship (the score/result) ONLY on the peak and the closing.\n"
        "- Set overlay.key_moment ONLY on the single highlight scene (a short badge).\n"
        "- Do NOT repeat the same title or the score on every scene.\n\n"
        "Other rules:\n"
        "- Build a clear arc across the photos: arrival -> build-up -> peak -> closing.\n"
        "- script_text is a slightly longer narration line for future voiceover.\n"
        f"- duration is in seconds, between {config.min_scene_seconds} and "
        f"{config.max_scene_seconds}. Give higher-engagement moments longer durations.\n"
        "- Mark the single strongest moment with highlight set to \"peak\"; others null.\n"
        "- visual_treatment.effect is one of: ken_burns; direction one of: in, out, left, right.\n"
        "- transition.type is one of: fade, crossfade; transition.duration ~0.4-0.8s.\n"
        "- Return one scene object per input scene, echoing its index."
    )


def _scene_payload(scene: TimelineScene) -> dict:
    return {
        "index": scene.scene_index,
        "timestamp": scene.date_time.isoformat(),
        "phase_hint": scene.phase,
        "description": scene.description,
        "place": scene.place,
        "likes": scene.likes,
        "comments": scene.comments,
        "social_score": scene.social_score,
    }


def build_user_prompt(event: EventInput, scenes: list[TimelineScene], config: RecapConfig) -> str:
    cc = event.championship_context
    context = {
        "event_id": event.event_id,
        "club": cc.club,
        "competition": cc.competition,
        "result_label": cc.result_label,
        "historical_angle": cc.historical_angle,
        "recap_angle": cc.recap_angle,
        "home_team": event.match_state.home_team,
        "away_team": event.match_state.away_team,
        "venue": event.event_detail.venue_name,
        "location": event.event_detail.venue_address,
        "language": config.language,
        "scenes": [_scene_payload(s) for s in scenes],
    }
    return (
        "Design the recap storyboard for this event. Context and chronological scenes:\n\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )
