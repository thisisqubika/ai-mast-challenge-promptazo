"""AI-generated event recap service using the Anthropic Claude API."""

import json

import anthropic

from app.core.config import settings
from app.data.seed import RECAPS
from app.schemas.events import MatchState, Photo, RecapHighlight, RecapResponse

# Cache keyed by "event_id:tone:slide_count" so each combination is stored
# independently — changing tone or slide count triggers a fresh generation.
# Seeded recaps are stored under "event_id:seed" as an API fallback only.
_store: dict[str, RecapResponse] = {
    f"{r.event_id}:seed": RecapResponse(
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
    return _store.get(f"{event_id}:seed")


def generate_recap(
    event_id: str,
    state: MatchState,
    photos: list[Photo],
    tone: str,
    slide_count: int,
) -> RecapResponse:
    """Generate a narrative recap for a completed match.

    Cache key includes tone + slide_count so each combination produces its own
    AI-generated content. Falls back to seed data if the API is unavailable.
    Always returns HTTP 200.
    """
    cache_key = f"{event_id}:{tone}:{slide_count}"
    if cache_key in _store:
        return _store[cache_key]

    if not settings.anthropic_api_key:
        result = _fallback_recap(event_id, state, photos, fallback=True, slide_count=slide_count)
        _store[cache_key] = result
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
        _store[cache_key] = result
        return result
    except Exception:
        result = _fallback_recap(event_id, state, photos, fallback=True, slide_count=slide_count)
        _store[cache_key] = result
        return result


def _build_context(state: MatchState, photos: list[Photo]) -> dict:
    home_goals = [
        {"player": g.player, "minute": g.minute}
        for g in state.goals
        if g.team == state.home_team
    ]
    away_goals = [
        {"player": g.player, "minute": g.minute}
        for g in state.goals
        if g.team == state.away_team
    ]
    return {
        "venue": state.venue,
        "home_team": state.home_team,
        "away_team": state.away_team,
        "home_score": state.home_score,
        "away_score": state.away_score,
        "home_goals": home_goals,   # goals scored BY home team (use as highlight anchors)
        "away_goals": away_goals,   # goals scored against the home fans
        "photo_count": len(photos),
    }


def _build_prompt(context: dict, tone: str, slide_count: int) -> str:
    home_team  = context.get("home_team", "el equipo local")
    away_team  = context.get("away_team", "el equipo visitante")
    home_goals = context.get("home_goals", [])
    home_score = context.get("home_score", 0)

    # Explain the highlight strategy to the model explicitly
    if home_goals:
        goal_lines = "\n".join(
            f"  - Gol {i + 1}: {g['player']}, minuto {g['minute']}"
            for i, g in enumerate(home_goals)
        )
        highlight_instruction = (
            f"Genera EXACTAMENTE {slide_count} highlights. "
            f"Cada highlight debe estar anclado en uno de los goles de {home_team} "
            f"(listados abajo), en orden cronológico. "
            f"Si hay menos goles que highlights pedidos, completa los restantes con "
            f"momentos positivos del ambiente en el bar (cantos, abrazos, emoción colectiva). "
            f"Goles de {home_team}:\n{goal_lines}"
        )
    else:
        highlight_instruction = (
            f"Genera EXACTAMENTE {slide_count} highlights. "
            f"{home_team} no convirtió goles en este partido. "
            f"Enfócate en momentos positivos de los hinchas en el bar: el aguante, "
            f"la unión, los cánticos y la actitud de no bajar los brazos."
        )

    return (
        f"Eres el narrador de una fan bar app. Los hinchas de este bar apoyan a {home_team}.\n\n"
        f"{highlight_instruction}\n\n"
        "Devuelve SOLO un objeto JSON válido con exactamente dos claves:\n"
        f'- "highlights": array de exactamente {slide_count} objetos, cada uno con:\n'
        f'  - "label": título en MAYÚSCULAS (3-6 palabras en español), evocador y específico al momento\n'
        f'  - "description": 1-2 oraciones en tono {tone} en español, '
        f"desde la perspectiva de los hinchas de {home_team} en el bar. "
        f"Celebra los goles propios con emoción. "
        f"Para momentos sin gol, transmite esperanza, aguante o euforia colectiva según el tono.\n"
        f'- "narrative": párrafo en tono {tone} en español (3-4 oraciones) '
        f"sobre el arco emocional completo de los hinchas de {home_team} durante la noche.\n\n"
        f"Contexto completo:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


_ATMOSPHERE_HIGHLIGHTS = [
    ("EL ESTADIO EN PIE", "Los hinchas no pararon de cantar ni un segundo. La tribuna fue el jugador número doce de {team}."),
    ("UNIÓN Y CORAZÓN", "Cada jugada generó gritos y abrazos. El bar se transformó en una sola voz de aliento para {team}."),
    ("HASTA EL FINAL", "Con fe y aguante, los fanáticos de {team} empujaron al equipo hasta el último minuto del partido."),
    ("LA NOCHE MÁS LARGA", "Entre nervios y esperanza, los hinchas de {team} vivieron una montaña rusa de emociones únicas."),
    ("PASIÓN CELESTE", "La pasión por {team} se sintió en cada rincón del bar. Esta hinchada nunca baja los brazos."),
]


def _fallback_recap(
    event_id: str,
    state: MatchState,
    photos: list[Photo],
    fallback: bool,
    slide_count: int = 3,
) -> RecapResponse:
    score_line = f"{state.home_score}-{state.away_score}"
    narrative = (
        f"Una noche épica para los hinchas de {state.home_team} en {state.venue}. "
        f"El partido terminó {score_line} con {state.home_team} como protagonista. "
        "Los fanáticos vivieron cada momento con una intensidad única."
    )

    home_goals = [g for g in state.goals if g.team == state.home_team]

    highlights: list[RecapHighlight] = [
        RecapHighlight(
            label=f"¡GOL DE {g.player.split()[-1].upper()}! MIN {g.minute}",
            description=(
                f"El estadio explotó cuando {g.player} anotó el gol de {state.home_team} "
                f"en el minuto {g.minute}. Los hinchas enloquecieron de alegría."
            ),
        )
        for g in home_goals
    ]

    # Pad with atmosphere moments until we reach slide_count
    atm_idx = 0
    while len(highlights) < slide_count:
        label_tpl, desc_tpl = _ATMOSPHERE_HIGHLIGHTS[atm_idx % len(_ATMOSPHERE_HIGHLIGHTS)]
        highlights.append(RecapHighlight(
            label=label_tpl,
            description=desc_tpl.format(team=state.home_team),
        ))
        atm_idx += 1

    # Truncate if more goals than slides requested
    highlights = highlights[:slide_count]
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
