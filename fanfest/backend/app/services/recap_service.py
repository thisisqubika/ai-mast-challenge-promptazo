"""AI-generated event recap service using the Anthropic Claude API."""

import json

import anthropic

from app.core.config import settings
from app.data.seed import RECAPS
from app.schemas.events import MatchState, Photo, RecapHighlight, RecapResponse

# Seeded with pre-generated recaps for past events; new recaps are saved here
# on first generation so subsequent calls return the cached version.
_store: dict[str, RecapResponse] = {
    r.event_id: RecapResponse(
        event_id=r.event_id,
        narrative=r.narrative,
        highlights=[RecapHighlight(label=s.label, description=s.description) for s in r.slides],
        correct_predictors=r.correct_predictors,
        fallback=r.fallback,
        home_score=r.home_score,
        away_score=r.away_score,
        home_team=r.home_team,
        away_team=r.away_team,
        photo_count=r.photo_count,
    )
    for r in RECAPS
}


def get_recap(event_id: str) -> RecapResponse | None:
    """Return a stored recap or None if not yet generated."""
    return _store.get(event_id)


def generate_recap(
    event_id: str,
    state: MatchState,
    photos: list[Photo],
    tone: str,
    slide_count: int,
) -> RecapResponse:
    """Generate a narrative recap for a completed match.

    Returns a cached recap if one already exists. Otherwise generates via the
    Anthropic API (or a fallback template), saves the result, and returns it.
    Always returns HTTP 200.
    """
    if event_id in _store:
        return _store[event_id]

    if not settings.anthropic_api_key:
        result = _fallback_recap(event_id, state, photos, fallback=True)
        _store[event_id] = result
        return result

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        context = _build_context(state, photos)
        prompt = _build_prompt(context, tone, slide_count)

        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        data = json.loads(raw)

        highlights = [
            RecapHighlight(label=h["label"], description=h["description"])
            for h in data.get("highlights", [])[:slide_count]
        ]
        narrative = data.get("narrative", "")

        result = RecapResponse(
            event_id=event_id,
            narrative=narrative,
            highlights=highlights,
            correct_predictors=[],
            fallback=False,
            home_score=state.home_score,
            away_score=state.away_score,
            home_team=state.home_team,
            away_team=state.away_team,
            photo_count=len(photos),
        )
        _store[event_id] = result
        return result
    except Exception:
        result = _fallback_recap(event_id, state, photos, fallback=True)
        _store[event_id] = result
        return result


def _build_context(state: MatchState, photos: list[Photo]) -> dict:
    return {
        "venue": state.venue,
        "home_team": state.home_team,
        "away_team": state.away_team,
        "home_score": state.home_score,
        "away_score": state.away_score,
        "goals": [
            {"player": g.player, "team": g.team, "minute": g.minute}
            for g in state.goals
        ],
        "photo_count": len(photos),
    }


def _build_prompt(context: dict, tone: str, slide_count: int) -> str:
    return (
        "You are a sports event narrator. Given the following fan fest context, "
        "return ONLY a valid JSON object with exactly two keys:\n"
        f'- "highlights": an array of at most {slide_count} objects, each with '
        '"label" and "description" string fields\n'
        f'- "narrative": a short {tone} recap paragraph in Spanish\n\n'
        f"Context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def _fallback_recap(
    event_id: str,
    state: MatchState,
    photos: list[Photo],
    fallback: bool,
) -> RecapResponse:
    score_line = f"{state.home_score}-{state.away_score}"
    narrative = (
        f"El partido entre {state.home_team} y {state.away_team} finalizó "
        f"{score_line} en {state.venue}. "
        "Fue una jornada memorable para todos los fanáticos presentes."
    )
    highlights = [
        RecapHighlight(
            label="Resultado final",
            description=f"{state.home_team} {state.home_score} - {state.away_score} {state.away_team}",
        )
    ]
    for goal in state.goals:
        highlights.append(
            RecapHighlight(
                label=f"Gol de {goal.player}",
                description=f"{goal.team}, minuto {goal.minute}",
            )
        )
    return RecapResponse(
        event_id=event_id,
        narrative=narrative,
        highlights=highlights,
        correct_predictors=[],
        fallback=fallback,
        home_score=state.home_score,
        away_score=state.away_score,
        home_team=state.home_team,
        away_team=state.away_team,
        photo_count=len(photos),
    )
