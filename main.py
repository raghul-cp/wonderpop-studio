"""
WonderPop YouTube AI Agent — daily pipeline orchestrator.

Usage:
    python -m src.main                     # generate content, obey config.yaml for upload/assembly
    python -m src.main --category ai_cartoon_comedy
    python -m src.main --no-upload         # force-skip upload even if config/env enables it
    python -m src.main --no-video          # skip image + video assembly, text/metadata only
    python -m src.main --dry-run           # generate everything but don't write files or upload

This is the single entry point GitHub Actions calls on a daily schedule
(see .github/workflows/daily_content.yml).
"""

import argparse
import sys
from pathlib import Path

from src import idea_generator, prompt_generator, script_writer, seo_generator, voiceover_generator
from src.config_loader import data_dir, get_config
from src.metadata_store import save_daily_package, update_upload_status


def run_pipeline(category: str = None, allow_upload: bool = True, allow_video: bool = True,
                  dry_run: bool = False) -> dict:
    cfg = get_config()
    print(f"[main] Content engine: {cfg['content_engine']}")

    # 1. Idea
    idea = idea_generator.generate_daily_idea(cfg, category_id=category)
    print(f"[main] Idea: {idea['title_seed']} ({idea['category_label']})")

    # 2. Script
    script = script_writer.generate_script(idea, cfg)
    print(f"[main] Script: {len(script['scenes'])} scenes, ~{script['total_duration_sec']}s")

    # 3. Image/video prompts (+ optional free image generation)
    scene_prompts = prompt_generator.generate_scene_prompts(script, idea, cfg)
    image_dir = data_dir("media", idea["id"], "images")
    if allow_video and not dry_run:
        scene_prompts = prompt_generator.generate_images(scene_prompts, image_dir, cfg)

    # 4. Voice-over script (+ optional free TTS audio)
    voiceover = voiceover_generator.generate_voiceover_script(script)
    audio_path = None
    if allow_video and not dry_run:
        audio_out = data_dir("media", idea["id"], "audio") / "voiceover.mp3"
        audio_path = voiceover_generator.synthesize_audio(voiceover, audio_out, cfg)

    # 5. SEO metadata
    seo = seo_generator.generate_seo(idea, script, cfg)
    print(f"[main] Title: {seo['title']}")

    if dry_run:
        print("[main] --dry-run set: skipping file writes, video assembly, and upload.")
        return {"idea": idea, "script": script, "scene_prompts": scene_prompts,
                "voiceover": voiceover, "seo": seo}

    # 6. Assemble video (free, local, optional)
    video_path = None
    if allow_video and cfg["video_assembly"]["enabled"]:
        from src import video_assembler
        video_out = data_dir("media", idea["id"]) / "short.mp4"
        video_path = video_assembler.assemble_short(scene_prompts, script, audio_path, video_out, cfg)
        if video_path:
            print(f"[main] Video assembled: {video_path}")

    # 7+8. Save scripts & metadata
    metadata = save_daily_package(idea, script, scene_prompts, voiceover, seo,
                                   video_path=video_path, audio_path=audio_path)
    print(f"[main] Saved package: data/metadata/{idea['id']}.json")

    # 9+10. Upload (optional — off by default; see config.yaml / SETUP.md)
    if allow_upload and cfg["upload"]["enabled"]:
        if not video_path:
            print("[main] Upload is enabled but no video was assembled — skipping upload.")
        else:
            from src import youtube_uploader
            try:
                result = youtube_uploader.upload_video(
                    video_path, seo["title"], seo["description"], seo["tags"], cfg,
                    category_id=cfg["channel"]["default_category_id"],
                )
                update_upload_status(idea["id"], result["video_id"], result["url"])
                print(f"[main] Uploaded: {result['url']}")
            except Exception as e:  # noqa: BLE001 — never let an upload failure kill a scheduled run silently
                print(f"[main] Upload failed: {e}", file=sys.stderr)
    else:
        print("[main] Upload disabled (set upload.enabled: true in config.yaml once YouTube OAuth is configured).")

    return metadata


def _parse_args():
    parser = argparse.ArgumentParser(description="WonderPop YouTube AI Agent daily pipeline")
    parser.add_argument("--category", default=None, help="Force a specific category id instead of weighted-random")
    parser.add_argument("--no-upload", action="store_true", help="Skip upload even if enabled in config")
    parser.add_argument("--no-video", action="store_true", help="Skip image generation, TTS, and video assembly")
    parser.add_argument("--dry-run", action="store_true", help="Generate everything but write nothing to disk")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_pipeline(
        category=args.category,
        allow_upload=not args.no_upload,
        allow_video=not args.no_video,
        dry_run=args.dry_run,
    )
