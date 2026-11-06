"""
Step 3 of the pipeline: turn each scene into a ready-to-use AI image prompt
and a short video-motion prompt (for tools like Runway/Pika/Kling, or for
manual use in any image/video generator).

Also optionally *generates* the actual images using Pollinations.ai
(https://pollinations.ai) — a free, keyless image generation API — so the
pipeline can produce real assets end-to-end without any paid service.
Set image_generation.enabled: false in config.yaml to skip the network
call and only produce the text prompts.
"""

import urllib.parse
from pathlib import Path

import requests

from prompts import templates as T

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"


def generate_scene_prompts(script: dict, idea: dict, cfg: dict) -> list[dict]:
    style = T.VISUAL_STYLES.get(idea["category_id"], "vibrant 3D animated style")
    style_suffix = cfg["image_generation"]["style_suffix"]

    prompts = []
    for scene in script["scenes"]:
        characters = ", ".join(scene.get("characters", []))
        base_desc = scene.get("action", "")
        image_prompt = (
            f"{base_desc}. Characters: {characters}. Setting: {scene.get('setting', '')}. "
            f"Style: {style}, {style_suffix}."
        )
        video_motion_prompt = (
            f"{scene.get('camera_notes', 'steady shot')}; subtle idle animation on characters; "
            f"gentle environmental motion (wind, light particles); vertical 9:16 framing."
        )
        prompts.append({
            "scene_number": scene["scene_number"],
            "image_prompt": image_prompt,
            "video_motion_prompt": video_motion_prompt,
            "style_tags": [style, "vertical 9:16", "family-friendly", "high detail"],
        })
    return prompts


def generate_images(prompts: list[dict], out_dir: Path, cfg: dict) -> list[dict]:
    """
    Download one image per scene prompt from Pollinations.ai (free, no API key).
    Returns the prompt list with an added "image_path" (or None on failure).
    Network failures are caught per-image so one bad request doesn't kill the run.
    """
    if not cfg["image_generation"]["enabled"]:
        return prompts

    width = cfg["video"]["width"]
    height = cfg["video"]["height"]
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in prompts:
        encoded = urllib.parse.quote(p["image_prompt"][:800])
        url = f"{POLLINATIONS_BASE}{encoded}?width={width}&height={height}&nologo=true"
        out_path = out_dir / f"scene_{p['scene_number']:02d}.png"
        try:
            resp = requests.get(url, timeout=90)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)
            p["image_path"] = str(out_path)
        except Exception as e:  # noqa: BLE001
            print(f"[prompt_generator] Image generation failed for scene {p['scene_number']}: {e}")
            p["image_path"] = None

    return prompts


if __name__ == "__main__":
    import json as _json

    from src.config_loader import get_config, data_dir
    from src.idea_generator import generate_daily_idea
    from src.script_writer import generate_script

    _cfg = get_config()
    _idea = generate_daily_idea(_cfg)
    _script = generate_script(_idea, _cfg)
    _prompts = generate_scene_prompts(_script, _idea, _cfg)
    print(_json.dumps(_prompts, indent=2))
