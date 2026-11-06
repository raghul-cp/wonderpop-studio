"""
Step 8 of the pipeline (requirement: "Save generated scripts and video
metadata"). Writes everything the pipeline produced to disk in a
predictable, git-friendly structure:

  data/ideas/<id>.json
  data/scripts/<id>.json        (machine-readable)
  data/scripts/<id>.md          (human-readable, easy to review in a PR diff)
  data/metadata/<id>.json       (seo + prompts + status, the "upload package")
  data/metadata/index.json      (running log of every package ever generated)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.config_loader import data_dir


def save_daily_package(idea: dict, script: dict, scene_prompts: list, voiceover: dict,
                        seo: dict, video_path: str | None = None, audio_path: str | None = None) -> dict:
    pkg_id = idea["id"]

    _write_json(data_dir("ideas") / f"{pkg_id}.json", idea)
    _write_json(data_dir("scripts") / f"{pkg_id}.json", script)
    _write_script_markdown(data_dir("scripts") / f"{pkg_id}.md", idea, script, voiceover)

    metadata = {
        "id": pkg_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "idea": idea,
        "seo": seo,
        "scene_prompts": scene_prompts,
        "voiceover_text": voiceover["full_text"],
        "audio_path": audio_path,
        "video_path": video_path,
        "status": {
            "script_generated": True,
            "images_generated": any(p.get("image_path") for p in scene_prompts),
            "audio_generated": audio_path is not None,
            "video_assembled": video_path is not None,
            "uploaded": False,
            "youtube_video_id": None,
            "youtube_url": None,
        },
    }
    metadata_path = data_dir("metadata") / f"{pkg_id}.json"
    _write_json(metadata_path, metadata)
    _append_index(pkg_id, idea, metadata_path)
    return metadata


def update_upload_status(pkg_id: str, youtube_video_id: str, youtube_url: str) -> None:
    path = data_dir("metadata") / f"{pkg_id}.json"
    if not path.exists():
        print(f"[metadata_store] No metadata found for {pkg_id}, cannot record upload status.")
        return
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["status"]["uploaded"] = True
    metadata["status"]["youtube_video_id"] = youtube_video_id
    metadata["status"]["youtube_url"] = youtube_url
    _write_json(path, metadata)


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_script_markdown(path: Path, idea: dict, script: dict, voiceover: dict) -> None:
    lines = [
        f"# {script.get('title', idea['title_seed'])}",
        "",
        f"**Category:** {idea['category_label']}  ",
        f"**Date:** {idea['date']}  ",
        f"**Target duration:** {script.get('total_duration_sec', '?')}s",
        "",
        f"> {idea['logline']}",
        "",
        "## Scenes",
        "",
    ]
    for scene in script["scenes"]:
        lines.append(f"### Scene {scene['scene_number']} — {scene.get('duration_sec', '?')}s")
        lines.append(f"**Setting:** {scene.get('setting', '')}  ")
        lines.append(f"**Characters:** {', '.join(scene.get('characters', []))}  ")
        lines.append(f"**Camera:** {scene.get('camera_notes', '')}")
        lines.append("")
        lines.append(f"Action: {scene.get('action', '')}")
        lines.append("")
        if scene.get("narration"):
            lines.append(f"*Narration:* {scene['narration']}")
        for d in scene.get("dialogue", []):
            lines.append(f"**{d['speaker']}:** {d['line']}")
        lines.append("")
    lines.append("## Full Voice-over Script")
    lines.append("")
    lines.append(voiceover["full_text"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _append_index(pkg_id: str, idea: dict, metadata_path: Path) -> None:
    index_path = data_dir("metadata") / "index.json"
    index = []
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = []
    index.append({
        "id": pkg_id,
        "date": idea["date"],
        "category_id": idea["category_id"],
        "title_seed": idea["title_seed"],
        "metadata_path": str(metadata_path.relative_to(metadata_path.parent.parent.parent)),
    })
    _write_json(index_path, index)
