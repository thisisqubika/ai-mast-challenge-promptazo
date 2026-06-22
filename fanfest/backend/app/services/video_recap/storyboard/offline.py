"""Deterministic, offline storyboard generator.

Used when no Claude API key is available (or ``provider=offline``). Guarantees the
pipeline always produces a video without any external API call.
"""

from __future__ import annotations

from ..config import RecapConfig
from ..models import (
    EventInput,
    OverlayText,
    Storyboard,
    StoryboardMeta,
    StoryboardScene,
    TimelineScene,
    Transition,
    VisualTreatment,
)
from .base import StoryboardGenerator
from .draft import opening_context_line

_SUBTITLES = {
    "arrival": {
        "en": "{home} fans flood the streets on the way to the final.",
        "es": "La hinchada de {home} copa las calles camino a la final.",
    },
    "buildup": {
        "en": "The stands fill before kickoff at {venue}.",
        "es": "La tribuna se llena antes del pitazo en {venue}.",
    },
    "peak": {
        "en": "{result} - {home} are champions of {competition}!",
        "es": "{result} - {home} campeon del {competition}!",
    },
    "closing": {
        "en": "The celebration rolls on into the night.",
        "es": "La fiesta sigue toda la noche.",
    },
}

_BUILDUP_SUBTITLES = {
    "en": [
        "The stands fill before kickoff at {venue}.",
        "Flags, drums and smoke take over the terraces.",
        "The crowd roars as the team comes out.",
        "Not an empty seat left as the noise keeps building.",
    ],
    "es": [
        "La tribuna se llena antes del pitazo en {venue}.",
        "Banderas, bombos y humo coparon la popular.",
        "La gente explota cuando el equipo sale a la cancha.",
        "No queda un lugar vacio mientras crece el aguante.",
    ],
}

_SCRIPTS = {
    "arrival": {
        "en": "It begins in the streets: {home} supporters march toward {venue}.",
        "es": "Todo empieza en la calle: los hinchas de {home} marchan hacia {venue}.",
    },
    "buildup": {
        "en": "The crowd takes over the stadium waiting for kickoff.",
        "es": "El estadio se copa mientras la gente espera el pitazo inicial.",
    },
    "peak": {
        "en": "{result}. {home} lift their {competition} title.",
        "es": "{result}. {home} levanta el titulo del {competition}.",
    },
    "closing": {
        "en": "The party carries on through the night.",
        "es": "La fiesta continua toda la noche.",
    },
}

_OVERLAY_EVENT = {
    "en": "{home} - {competition} Champions",
    "es": "{home} campeon del {competition}",
}

_OPENING_TITLE = {"en": "{home}: the final", "es": "{home}: la final"}
_PEAK_TITLE = {"en": "Champions!", "es": "Campeones!"}
_CLOSING_TITLE = {"en": "A historic night", "es": "Una noche historica"}

_KEY_MOMENT = {
    "en": "Top moment - {likes} likes",
    "es": "Momento top - {likes} likes",
}

_TREATMENTS = [
    ("ken_burns", "in"),
    ("ken_burns", "out"),
    ("ken_burns", "left"),
    ("ken_burns", "right"),
]


def _lang(table: dict, phase: str, language: str) -> str:
    options = table[phase]
    return options.get(language, options["en"])


def _round_half(value: float) -> float:
    return round(value * 2) / 2


def _scale_duration(score: int, lo: int, hi: int, cfg: RecapConfig) -> float:
    if hi <= lo:
        return _round_half((cfg.min_scene_seconds + cfg.max_scene_seconds) / 2)
    frac = (score - lo) / (hi - lo)
    dur = cfg.min_scene_seconds + frac * (cfg.max_scene_seconds - cfg.min_scene_seconds)
    return _round_half(dur)


class OfflineStoryboardGenerator(StoryboardGenerator):
    name = "offline"

    def generate(
        self, event: EventInput, scenes: list[TimelineScene], config: RecapConfig
    ) -> Storyboard:
        lang = config.language
        home = event.match_state.home_team
        away = event.match_state.away_team
        result = event.championship_context.result_label
        competition = event.championship_context.competition
        venue = event.event_detail.venue_name or "el estadio"
        city = (event.event_detail.venue_address or "la ciudad").split(",")[0].strip()

        fmt = dict(home=home, away=away, result=result, competition=competition, venue=venue, city=city)

        scores = [s.social_score for s in scenes]
        lo, hi = min(scores), max(scores)

        sb_scenes: list[StoryboardScene] = []
        buildup_idx = 0
        for i, scene in enumerate(scenes):
            effect, direction = _TREATMENTS[i % len(_TREATMENTS)]
            is_highlight = scene.phase == "peak"
            duration = _scale_duration(scene.social_score, lo, hi, config)

            if scene.phase == "buildup":
                variants = _BUILDUP_SUBTITLES.get(lang, _BUILDUP_SUBTITLES["en"])
                subtitle = variants[buildup_idx % len(variants)].format(**fmt)
                buildup_idx += 1
            else:
                subtitle = _lang(_SUBTITLES, scene.phase, lang).format(**fmt)

            event_title = None
            championship = None
            key_moment = None
            datetime_line = None
            if scene.scene_index == 1:
                event_title = _OPENING_TITLE.get(lang, _OPENING_TITLE["en"]).format(**fmt)
                datetime_line = opening_context_line(event, scene)
            elif is_highlight:
                event_title = _PEAK_TITLE.get(lang, _PEAK_TITLE["en"])
                championship = result
                key_moment = _KEY_MOMENT.get(lang, _KEY_MOMENT["en"]).format(likes=scene.likes)
            elif scene.phase == "closing":
                event_title = _CLOSING_TITLE.get(lang, _CLOSING_TITLE["en"])
                championship = result

            overlay = OverlayText(
                event=event_title,
                datetime=datetime_line,
                place=None,
                championship=championship,
                key_moment=key_moment,
            )

            sb_scenes.append(
                StoryboardScene(
                    scene_id=scene.source_id,
                    source_image=scene.image_ref,
                    chronological_position=scene.scene_index,
                    source_timestamp=scene.date_time.isoformat(),
                    scene_title=f"{scene.phase.capitalize()} - {scene.place}",
                    scene_description=scene.description,
                    script_text=_lang(_SCRIPTS, scene.phase, lang).format(**fmt),
                    subtitle_text=subtitle,
                    visual_treatment=VisualTreatment(effect=effect, direction=direction, fill="blurred"),
                    transition=Transition(
                        type="fade" if i == 0 else "crossfade",
                        duration=config.transition_seconds,
                    ),
                    duration=duration,
                    overlay_text=overlay,
                    highlight="peak" if is_highlight else None,
                    social_summary=f"{scene.likes} likes, {len(scene.comments)} comments. \"{scene.description}\"",
                )
            )

        title = _OVERLAY_EVENT.get(lang, _OVERLAY_EVENT["en"]).format(**fmt)
        meta = StoryboardMeta(
            event_id=event.event_id,
            title=title,
            language=lang,
            total_duration=round(sum(s.duration for s in sb_scenes), 2),
            generated_by=self.name,
            model=None,
        )
        return Storyboard(meta=meta, scenes=sb_scenes)
