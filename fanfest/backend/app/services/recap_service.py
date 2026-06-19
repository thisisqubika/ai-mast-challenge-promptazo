"""AI-generated event recap service using the Anthropic Claude API."""

import json

import anthropic

from app.core.config import settings
from app.schemas.events import MatchState, Photo, RecapHighlight, RecapResponse


def generate_recap(
    event_id: str,
    state: MatchState,
    photos: list[Photo],
    tone: str,
    slide_count: int,
) -> RecapResponse:
    """Generate a narrative recap for a completed match.

    Falls back to a templated summary when the Anthropic API key is absent
    or any API or parse error occurs, always returning HTTP 200.
    """
    if not settings.anthropic_api_key:
        return _fallback_recap(event_id, state, photos, fallback=True)

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

        return RecapResponse(
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
    except Exception:
        return _fallback_recap(event_id, state, photos, fallback=True)


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
