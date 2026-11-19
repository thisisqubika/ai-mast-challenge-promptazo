"""Compile the AI Recap slides (rendered as PNGs in the browser) into an MP4."""

import io
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

MUSIC_DIR = Path(__file__).resolve().parents[2] / "assets" / "music"
# Recap tone → music file stem (accents dropped so file names stay simple)
_TONE_FILES = {
    "emocionante": "emocionante",
    "inspirador": "inspirador",
    "humorístico": "humoristico",
    "nostálgico": "nostalgico",
}
MAX_SLIDES = 25
MAX_FRAME_BYTES = 10 * 1024 * 1024
FPS = 24


def _even(n: int) -> int:
    # H.264 (yuv420p) needs even width/height
    return n - (n % 2)


def music_for_tone(tone: str | None) -> Path | None:
    """The background track for a tone, if one was added to assets/music/."""
    stem = _TONE_FILES.get((tone or "").strip().lower())
    if not stem:
        return None
    for ext in (".mp3", ".m4a", ".wav"):
        path = MUSIC_DIR / f"{stem}{ext}"
        if path.exists():
            return path
    return None


def _with_music(clip, track: Path):
    """Fit the track to the clip (trim or loop) with a short fade in/out."""
    from moviepy import AudioFileClip, afx

    audio = AudioFileClip(str(track))
    if audio.duration < clip.duration:
        audio = audio.with_effects([afx.AudioLoop(duration=clip.duration)])
    else:
        audio = audio.subclipped(0, clip.duration)
    audio = audio.with_effects([afx.AudioFadeIn(0.5), afx.AudioFadeOut(1.5)])
    return clip.with_audio(audio)


def build_slides_video(
    frames: list[bytes], seconds_per_slide: float = 2.0, tone: str | None = None
) -> Path:
    """Return the path of an MP4 showing each frame for `seconds_per_slide` seconds.

    Adds the tone's background music from assets/music/ when available.

    The caller is responsible for deleting the returned file.
    """
    from moviepy import ImageSequenceClip  # heavy import, only when needed

    if not frames:
        raise ValueError("No slides received")
    if len(frames) > MAX_SLIDES:
        raise ValueError(f"Too many slides (max {MAX_SLIDES})")

    images = []
    size = None
    for raw in frames:
        if len(raw) > MAX_FRAME_BYTES:
            raise ValueError("Slide image too large")
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        if size is None:
            size = (_even(img.width), _even(img.height))
        if img.size != size:
            img = img.resize(size, Image.LANCZOS)
        images.append(np.asarray(img))

    clip = ImageSequenceClip(images, durations=[seconds_per_slide] * len(images))
    track = music_for_tone(tone)
    if track:
        clip = _with_music(clip, track)
    out = Path(tempfile.mkstemp(suffix=".mp4", prefix="recap-slides-")[1])
    try:
        clip.write_videofile(
            str(out),
            fps=FPS,
            codec="libx264",
            audio=bool(track),
            audio_codec="aac",
            preset="veryfast",
            ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
            logger=None,
        )
    finally:
        clip.close()
    return out
