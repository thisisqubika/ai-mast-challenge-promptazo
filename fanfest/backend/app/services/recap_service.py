"""AI-generated event recap service using the Anthropic Claude API."""

import json
import logging

import anthropic

from app.core.config import settings
from app.data.seed import RECAPS
from app.services import gemini_client
from app.schemas.events import MatchState, Photo, RecapHighlight, RecapResponse

logger = logging.getLogger("uvicorn.error")

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

    provider, model = _active_provider()
    if provider is None:
        logger.warning("AI recap: no GEMINI_API_KEY or ANTHROPIC_API_KEY configured — using fallback recap")
        return _fallback_recap(event_id, state, photos, fallback=True, slide_count=slide_count)

    try:
        context = _build_context(state, photos)
        prompt = _build_prompt(context, tone, slide_count)
        raw = _call_gemini(prompt) if provider == "gemini" else _call_anthropic(prompt)
        data = json.loads(_strip_code_fences(raw))

        highlights = _attach_photos(
            [
                RecapHighlight(
                    label=h["label"],
                    description=h["description"],
                    goal_number=h.get("goal_number"),
                    photo_id=h.get("photo_id"),
                )
                for h in data.get("highlights", [])[:slide_count]
            ],
            state,
            photos,
        )
        narrative = data.get("narrative", "")

        result = RecapResponse(
            event_id=event_id,
            narrative=narrative,
            highlights=highlights,
            correct_predictors=[],
            fallback=False,
            headline=_short(data.get("headline")),
            stats_title=_short(data.get("stats_title")),
            closing_title=_short(data.get("closing_title")),
            closing_text=_short(data.get("closing_text"), 220),
            home_score=state.home_score,
            away_score=state.away_score,
            home_team=state.home_team,
            away_team=state.away_team,
            photo_count=len(photos),
        )
        logger.info("AI recap generated with %s (%s)", provider, model)
        _store[cache_key] = result
        return result
    except Exception as exc:
        # Not cached, so the next request retries the AI instead of reusing the fallback
        logger.warning(
            "AI recap failed (%s, model=%s): %s: %s — using fallback recap",
            provider, model, type(exc).__name__, str(exc)[:300],
        )
        return _fallback_recap(event_id, state, photos, fallback=True, slide_count=slide_count)


def _short(value, limit: int = 60) -> str | None:
    text = (value or "").strip() if isinstance(value, str) else ""
    return text[:limit] or None


def _home_goals(state: MatchState) -> list:
    return [g for g in state.goals if g.team == state.home_team]


def _attach_photos(
    highlights: list[RecapHighlight], state: MatchState, photos: list[Photo]
) -> list[RecapHighlight]:
    """Make each slide's photo match the moment it talks about.

    Keeps the AI's photo_id only if it exists and belongs to the highlight's goal;
    otherwise picks an unused photo of that goal. Highlights without a goal get no
    photo here (the frontend falls back to a general photo).
    """
    goals = _home_goals(state)
    photo_ids = {p.id for p in photos}
    used: set[str] = set()

    def goal_for(h: RecapHighlight):
        if h.goal_number and 1 <= h.goal_number <= len(goals):
            return goals[h.goal_number - 1]
        return None

    result = []
    for h in highlights:
        goal = goal_for(h)
        goal_photos = [p for p in photos if goal and p.goal_id == goal.id]
        chosen = None
        if h.photo_id in photo_ids and (not goal or any(p.id == h.photo_id for p in goal_photos)):
            chosen = h.photo_id
        if chosen is None or chosen in used:
            spare = [p.id for p in goal_photos if p.id not in used]
            chosen = spare[0] if spare else (chosen if goal_photos else None)
        if chosen:
            used.add(chosen)
        result.append(h.model_copy(update={
            "photo_id": chosen,
            "goal_number": h.goal_number if goal else None,
        }))
    return result


def _active_provider() -> tuple[str | None, str | None]:
    """Gemini wins when its key is set; otherwise Claude; otherwise no AI."""
    if settings.gemini_api_key:
        return "gemini", settings.gemini_model
    if settings.anthropic_api_key:
        return "anthropic", settings.anthropic_model
    return None, None


def _strip_code_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().split("```")[0].strip()
    return raw


def _call_anthropic(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_gemini(prompt: str) -> str:
    return gemini_client.generate_json(prompt)


def _build_context(state: MatchState, photos: list[Photo]) -> dict:
    home_goals = [
        {"player": g.player, "minute": g.minute, **({"moment": g.label} if g.label else {})}
        for g in state.goals
        if g.team == state.home_team
    ]
    goal_moment = {g.id: (g.label or g.player) for g in state.goals if g.id is not None}
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
        # What fans wrote: the uploader's caption + comments others left on the photo.
        # Primary source of the real moments of the event.
        "fan_photos": [
            {
                "photo_id": p.id,
                "uploader": p.uploader_name,
                "uploaded_at": p.uploaded_at.isoformat(),
                "caption": (p.caption or "").strip() or None,
                # Which goal/moment of the event the photo belongs to (e.g. "Bowling")
                "moment": goal_moment.get(p.goal_id),
                "comments": [
                    {"by": c.user_name or c.user_handle, "text": c.text} for c in p.comments
                ],
            }
            for p in sorted(photos, key=lambda p: p.uploaded_at)
            if (p.caption and p.caption.strip()) or p.comments or p.goal_id in goal_moment
        ],
    }


def _build_prompt(context: dict, tone: str, slide_count: int) -> str:
    home_team  = context.get("home_team", "el equipo local")
    home_goals = context.get("home_goals", [])

    # Explain the highlight strategy to the model explicitly
    if home_goals:
        goal_lines = "\n".join(
            f"  - goal_number {i + 1}: {g['player']}, minuto {g['minute']}"
            + (f" — momento: {g['moment']}" if g.get("moment") else "")
            for i, g in enumerate(home_goals)
        )
        highlight_instruction = (
            f"Genera EXACTAMENTE {slide_count} highlights. "
            f"Cada highlight debe estar anclado en uno de los goles de {home_team} "
            f"(listados abajo), en orden cronológico. "
            f"Si hay más goles que highlights, priorizá los goles que tienen fotos en "
            f"\"fan_photos\" (campo \"moment\"). "
            f"Si un gol tiene \"momento\", ese gol representa una actividad real con ese nombre "
            f"(por ejemplo un bowling o una trivia): el highlight debe hablar de ESA actividad, "
            f"no de un gol de fútbol literal, y su label debe reflejarla. "
            f"Si hay menos goles que highlights pedidos, completa los restantes con "
            f"momentos positivos del grupo (cantos, abrazos, emoción colectiva). "
            f"Goles de {home_team}:\n{goal_lines}"
        )
    else:
        highlight_instruction = (
            f"Genera EXACTAMENTE {slide_count} highlights. "
            f"{home_team} no convirtió goles en este partido. "
            f"Enfócate en momentos positivos de los hinchas en el bar: el aguante, "
            f"la unión, los cánticos y la actitud de no bajar los brazos."
        )

    captions_instruction = ""
    if context.get("fan_photos"):
        captions_instruction = (
            "Los hinchas subieron fotos con una descripción (\"caption\") y otros les dejaron "
            "comentarios (\"comments\"); ver \"fan_photos\" en el contexto. "
            "Usá esos textos como fuente principal: cada highlight y la narrativa deben "
            "referirse a momentos concretos que mencionan, parafraseándolos con su propio vocabulario. "
            "No inventes hechos que contradigan los comentarios. "
            "Para cada highlight elegí en \"photo_id\" una foto cuyo \"moment\" coincida con "
            "ese goal_number, y que la description sea coherente con el caption y los "
            "comentarios de ESA foto. Si no hay foto de ese momento, usá null.\n\n"
        )

    return (
        f"Eres el narrador de una fan bar app. Los hinchas de este bar apoyan a {home_team}.\n\n"
        f"{highlight_instruction}\n\n"
        f"{captions_instruction}"
        "Devuelve SOLO un objeto JSON válido con estas claves:\n"
        f'- "highlights": array de exactamente {slide_count} objetos, cada uno con:\n'
        f'  - "goal_number": número del gol en el que se basa (o null)\n'
        f'  - "photo_id": id de la foto de ese momento tomada de fan_photos (o null)\n'
        f'  - "label": título en MAYÚSCULAS (3-6 palabras en español), evocador y específico al momento\n'
        f'  - "description": 1-2 oraciones en tono {tone} en español, '
        f"desde la perspectiva de los hinchas de {home_team} en el bar. "
        f"Celebra los goles propios con emoción. "
        f"Para momentos sin gol, transmite esperanza, aguante o euforia colectiva según el tono.\n"
        f'- "narrative": párrafo en tono {tone} en español (3-4 oraciones) '
        f"sobre el arco emocional completo de los hinchas de {home_team}.\n"
        '- "headline": título de apertura (2-5 palabras, español), propio de este evento\n'
        '- "stats_title": título para la slide de números (2-5 palabras, español)\n'
        '- "closing_title": título de cierre para compartir (2-4 palabras, español)\n'
        f'- "closing_text": una oración de cierre en tono {tone} (español)\n\n'
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
            label=g.label.upper() if g.label else f"¡GOL DE {g.player.split()[-1].upper()}! MIN {g.minute}",
            description=(
                f"{g.label} ({g.player}): uno de los momentos que hicieron grande a {state.home_team}."
                if g.label else
                f"El estadio explotó cuando {g.player} anotó el gol de {state.home_team} "
                f"en el minuto {g.minute}. Los hinchas enloquecieron de alegría."
            ),
            goal_number=i + 1,
        )
        for i, g in enumerate(home_goals)
    ]
    # Prefer goals that have photos, keeping chronological order
    with_photos = {p.goal_id for p in photos if p.goal_id is not None}
    if with_photos:
        highlights.sort(key=lambda h: home_goals[h.goal_number - 1].id not in with_photos)
        highlights = sorted(highlights[:slide_count], key=lambda h: h.goal_number)

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
    highlights = _attach_photos(highlights[:slide_count], state, photos)
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
