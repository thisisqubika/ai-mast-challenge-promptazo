"""Image preparation and clip-building helpers for the MoviePy renderer."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from moviepy import ImageClip, TextClip
from PIL import Image, ImageFilter

from ..errors import RenderError

_FONT_BOLD = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_FONT_REGULAR = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


@lru_cache(maxsize=2)
def find_font(bold: bool) -> str:
    for candidate in (_FONT_BOLD if bold else _FONT_REGULAR):
        if Path(candidate).exists():
            return candidate
    raise RenderError(
        "No usable TTF font found. Install one of: "
        + ", ".join(_FONT_BOLD if bold else _FONT_REGULAR)
    )


def _open_rgb(path: str) -> Image.Image:
    try:
        return Image.open(path).convert("RGB")
    except OSError as exc:
        raise RenderError(f"Could not open image for rendering: {path} ({exc})") from exc


def _cover(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    iw, ih = im.size
    scale = max(tw / iw, th / ih)
    resized = im.resize((max(1, round(iw * scale)), max(1, round(ih * scale))), Image.LANCZOS)
    left = (resized.width - tw) // 2
    top = (resized.height - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def _contain(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    iw, ih = im.size
    scale = min(tw / iw, th / ih)
    return im.resize((max(1, round(iw * scale)), max(1, round(ih * scale))), Image.LANCZOS)


def background_clip(path: str, size: tuple[int, int], duration: float,
                    blur: int = 22, darken: float = 0.45) -> ImageClip:
    im = _cover(_open_rgb(path), size).filter(ImageFilter.GaussianBlur(blur))
    im = Image.eval(im, lambda p: int(p * darken))
    return ImageClip(np.array(im)).with_duration(duration)


def foreground_clip(path: str, size: tuple[int, int], duration: float, direction: str = "in",
                    zoom: float = 0.08, w_frac: float = 0.92, h_frac: float = 0.60) -> ImageClip:
    w, h = size
    fitted = _contain(_open_rgb(path), (int(w * w_frac), int(h * h_frac)))
    clip = ImageClip(np.array(fitted)).with_duration(duration)

    zoom_out = direction in ("out", "right", "down")
    if zoom_out:
        clip = clip.resized(lambda t: 1 + zoom * (1 - t / duration))
    else:
        clip = clip.resized(lambda t: 1 + zoom * (t / duration))
    return clip.with_position("center")


def text_clip(text: str, *, bold: bool, font_px: int, box_w: int, color: str = "white",
              bg_color=None, stroke: int = 0, duration: float, position) -> TextClip:
    return TextClip(
        font=find_font(bold),
        text=text,
        font_size=font_px,
        color=color,
        bg_color=bg_color,
        stroke_color="black" if stroke else None,
        stroke_width=stroke,
        method="caption",
        size=(box_w, None),
        text_align="center",
    ).with_duration(duration).with_position(position)
