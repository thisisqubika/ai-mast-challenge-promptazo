"""Renderer interface and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import RecapConfig
from ..models import Storyboard


class Renderer(ABC):
    name: str = "base"

    @abstractmethod
    def render(
        self,
        storyboard: Storyboard,
        image_paths: dict[str, str],
        config: RecapConfig,
        out_path: str,
    ) -> str:
        """Render the storyboard to a video file and return the output path."""


def get_renderer(config: RecapConfig) -> Renderer:
    from .moviepy_renderer import MoviePyRenderer

    return MoviePyRenderer()
