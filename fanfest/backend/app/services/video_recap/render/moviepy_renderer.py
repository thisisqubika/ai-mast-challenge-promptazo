"""Deterministic MoviePy renderer."""

from __future__ import annotations

from moviepy import ColorClip, CompositeVideoClip, vfx

from ..config import RecapConfig
from ..errors import RenderError
from ..models import Storyboard, StoryboardScene
from ..subtitles import storyboard_timings
from .base import Renderer
from .effects import background_clip, foreground_clip, text_clip


class MoviePyRenderer(Renderer):
    name = "moviepy"

    def render(
        self,
        storyboard: Storyboard,
        image_paths: dict[str, str],
        config: RecapConfig,
        out_path: str,
    ) -> str:
        size = (config.width, config.height)
        w, h = size
        box_w = int(w * 0.90)
        title_px = int(h * 0.032)
        meta_px = int(h * 0.020)
        sub_px = int(h * 0.026)

        timings = storyboard_timings(storyboard)
        scene_clips = []
        subtitle_clips = []

        for scene, tm in zip(storyboard.scenes, timings):
            if scene.source_image not in image_paths:
                raise RenderError(f"No resolved image path for {scene.source_image}")
            path = image_paths[scene.source_image]
            d = scene.duration
            is_highlight = bool(scene.highlight)

            bg = background_clip(path, size, d)
            fg = foreground_clip(
                path, size, d,
                direction=scene.visual_treatment.direction,
                zoom=0.16 if is_highlight else 0.08,
            )
            layers = [bg, fg]
            if is_highlight:
                flash_d = min(0.35, d / 2)
                flash = (ColorClip(size=size, color=(255, 255, 255))
                         .with_duration(flash_d).with_opacity(0.5)
                         .with_effects([vfx.FadeOut(flash_d)]))
                layers.append(flash)
            layers.extend(self._overlay_clips(scene, w, h, box_w, title_px, meta_px, d))

            scene_clip = CompositeVideoClip(layers, size=size).with_duration(d)
            scene_clip = scene_clip.with_start(tm.start)
            if tm.index == 0:
                scene_clip = scene_clip.with_effects([vfx.FadeIn(min(0.5, d / 2))])
            else:
                scene_clip = scene_clip.with_effects([vfx.CrossFadeIn(scene.transition.duration)])
            scene_clips.append(scene_clip)

            sub = text_clip(
                scene.subtitle_text, bold=False, font_px=sub_px, box_w=box_w,
                duration=max(0.1, tm.cue_end - tm.cue_start),
                position=("center", int(h * 0.80)),
            ).with_start(tm.cue_start)
            subtitle_clips.append(sub)

        total = timings[-1].end
        final = CompositeVideoClip([*scene_clips, *subtitle_clips], size=size).with_duration(total)

        try:
            final.write_videofile(
                out_path,
                fps=config.fps,
                codec="libx264",
                audio=False,
                threads=4,
                preset="medium",
                ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
                logger="bar",
            )
        except Exception as exc:
            raise RenderError(f"Video export failed: {exc}") from exc
        finally:
            final.close()
        return out_path

    def _overlay_clips(self, scene: StoryboardScene, w: int, h: int, box_w: int,
                       title_px: int, meta_px: int, duration: float):
        clips = []
        y = int(h * 0.05)
        gap = int(h * 0.008)

        overlay = scene.overlay_text

        def add(text: str, *, bold: bool, px: int, color: str = "white", stroke: int = 2):
            nonlocal y
            clip = text_clip(text, bold=bold, font_px=px, box_w=box_w, color=color,
                             stroke=stroke, duration=duration, position=("center", y))
            clips.append(clip)
            y += clip.h + gap

        if overlay.event:
            add(overlay.event, bold=True, px=title_px)
        if overlay.datetime:
            add(overlay.datetime, bold=False, px=meta_px, stroke=1)
        if overlay.championship:
            add(overlay.championship, bold=True, px=meta_px, stroke=1)
        if overlay.key_moment:
            add(f"* {overlay.key_moment} *", bold=True, px=meta_px, color="#ffd54a", stroke=1)
        return clips
