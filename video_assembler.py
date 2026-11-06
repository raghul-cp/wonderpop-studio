"""
Optional step: assemble the generated scene images + voice-over audio into
an actual vertical (9:16) mp4 using moviepy + ffmpeg — both free and local,
no paid rendering service involved.

This produces a simple "Ken Burns" style slideshow (slow pan/zoom per
image) with the voice-over as the audio track. It is intentionally basic —
good enough for a first-draft Short you can review, trim, and polish in
any free video editor (e.g. CapCut, DaVinci Resolve) before publishing,
or to post as-is for simple narration-driven formats.

Captions are attempted via moviepy's TextClip (needs ImageMagick). If
ImageMagick isn't available, captions are silently skipped rather than
crashing the whole pipeline — the video is still produced without them.
"""

from pathlib import Path


def assemble_short(scene_prompts: list, script: dict, audio_path: str | None,
                    out_path: Path, cfg: dict) -> str | None:
    if not cfg["video_assembly"]["enabled"]:
        return None

    images = [p.get("image_path") for p in scene_prompts if p.get("image_path")]
    if not images:
        print("[video_assembler] No scene images available — skipping video assembly.")
        return None

    try:
        from moviepy.editor import (AudioFileClip, CompositeVideoClip, ImageClip,
                                     TextClip, concatenate_videoclips)
    except ImportError:
        print("[video_assembler] moviepy not installed — run `pip install moviepy` or disable video_assembly in config.")
        return None

    width, height = cfg["video"]["width"], cfg["video"]["height"]
    scenes = script["scenes"]
    clips = []

    for i, scene in enumerate(scenes):
        if i >= len(images):
            break
        duration = scene.get("duration_sec", 5)
        img_clip = (
            ImageClip(images[i])
            .set_duration(duration)
            .resize(height=height)
        )
        # Simple slow zoom-in ("Ken Burns") for visual motion without any paid animation tool.
        img_clip = img_clip.resize(lambda t, d=duration: 1 + 0.04 * (t / d))
        img_clip = img_clip.set_position(("center", "center"))

        layers = [img_clip]
        caption_text = scene.get("narration") or (scene["dialogue"][0]["line"] if scene.get("dialogue") else None)
        if caption_text:
            try:
                txt_clip = (
                    TextClip(caption_text, fontsize=58, color="white", font="DejaVu-Sans-Bold",
                             stroke_color="black", stroke_width=2, method="caption", size=(width - 100, None))
                    .set_duration(duration)
                    .set_position(("center", "bottom"))
                )
                layers.append(txt_clip)
            except Exception as e:  # noqa: BLE001 — ImageMagick missing or similar; skip captions, keep the video
                print(f"[video_assembler] Caption rendering skipped (likely missing ImageMagick): {e}")

        scene_clip = CompositeVideoClip(layers, size=(width, height))
        clips.append(scene_clip)

    if not clips:
        return None

    final = concatenate_videoclips(clips, method="compose")

    if audio_path and Path(audio_path).exists():
        audio_clip = AudioFileClip(audio_path)
        # Match video length to the longer of (planned scene durations) vs (actual narration length)
        # so the voice-over is never cut off.
        if audio_clip.duration > final.duration:
            final = final.set_duration(audio_clip.duration)
        final = final.set_audio(audio_clip.set_duration(final.duration))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        final.write_videofile(
            str(out_path), fps=cfg["video"]["fps"], codec="libx264", audio_codec="aac",
            threads=2, logger=None,
        )
        return str(out_path)
    except Exception as e:  # noqa: BLE001 — e.g. ffmpeg missing
        print(f"[video_assembler] Video rendering failed (is ffmpeg installed?): {e}")
        return None
