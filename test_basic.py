"""
Smoke tests for the template engine (no API keys, no network required).
Run with: pytest
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config_loader import get_config
from src.idea_generator import generate_daily_idea
from src.script_writer import generate_script
from src.seo_generator import generate_seo
from src.prompt_generator import generate_scene_prompts
from src.voiceover_generator import generate_voiceover_script


def test_config_loads():
    cfg = get_config()
    assert cfg["channel"]["name"]
    assert len(cfg["content_categories"]) == 5


def test_idea_generation_all_categories():
    cfg = get_config()
    for cat in cfg["content_categories"]:
        idea = generate_daily_idea(cfg, category_id=cat["id"])
        assert idea["category_id"] == cat["id"]
        assert idea["title_seed"]
        assert idea["hook"]


def test_script_generation():
    cfg = get_config()
    idea = generate_daily_idea(cfg)
    script = generate_script(idea, cfg)
    assert len(script["scenes"]) == cfg["video"]["scenes_per_video"]
    assert script["total_duration_sec"] > 0
    for scene in script["scenes"]:
        assert "action" in scene
        assert "scene_number" in scene


def test_prompt_generation():
    cfg = get_config()
    idea = generate_daily_idea(cfg)
    script = generate_script(idea, cfg)
    prompts = generate_scene_prompts(script, idea, cfg)
    assert len(prompts) == len(script["scenes"])
    for p in prompts:
        assert p["image_prompt"]
        assert p["video_motion_prompt"]


def test_voiceover_generation():
    cfg = get_config()
    idea = generate_daily_idea(cfg)
    script = generate_script(idea, cfg)
    vo = generate_voiceover_script(script)
    assert vo["full_text"]
    assert vo["plain_text"]


def test_seo_generation_respects_limits():
    cfg = get_config()
    idea = generate_daily_idea(cfg)
    script = generate_script(idea, cfg)
    seo = generate_seo(idea, script, cfg)
    assert len(seo["title"]) <= cfg["seo"]["title_max_chars"]
    assert len(seo["tags"]) <= cfg["seo"]["max_tags"]
    assert "#Shorts" in " ".join(seo["hashtags"])
