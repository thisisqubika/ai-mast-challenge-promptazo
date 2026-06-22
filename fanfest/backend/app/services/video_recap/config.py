"""Runtime configuration for a video recap render."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Provider = Literal["auto", "anthropic", "openai", "offline"]

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


@dataclass
class RecapConfig:
    output_dir: Path = field(default_factory=lambda: Path("media/recap"))
    base_dir: Path = field(default_factory=Path.cwd)

    language: str = "es"
    provider: Provider = "auto"
    model: str = DEFAULT_MODEL
    openai_model: str = DEFAULT_OPENAI_MODEL

    width: int = 1080
    height: int = 1920
    fps: int = 30

    min_scene_seconds: float = 3.0
    max_scene_seconds: float = 6.0
    transition_seconds: float = 0.6

    include_excluded: bool = False

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.base_dir = Path(self.base_dir)
