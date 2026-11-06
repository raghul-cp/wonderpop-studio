"""
Step 1 of the pipeline: generate a daily viral video idea.

Produces a dict:
{
    "id": "2026-11-01-ai_animal_adventures-7f3a",
    "date": "2026-11-01",
    "category_id": "ai_animal_adventures",
    "category_label": "AI Animal Adventures",
    "title_seed": str,
    "character": str,
    "setting": str,
    "object": str,
    "hook": str,
    "logline": str,
    "moral": str | None,
    "target_duration_sec": int,
}
"""

import random
import uuid
from datetime import date

from prompts import templates as T
from src import llm_client


def generate_daily_idea(cfg: dict, category_id: str = None) -> dict:
    category_id = category_id or T.pick_category(cfg["content_categories"])
    category_label = T.CATEGORY_LABELS[category_id]
    today = date.today().isoformat()
    uid = uuid.uuid4().hex[:4]

    llm_idea = _try_llm(cfg, category_id, category_label)
    if llm_idea:
        idea = llm_idea
    else:
        idea = _template_idea(category_id, category_label)

    idea.update({
        "id": f"{today}-{category_id}-{uid}",
        "date": today,
        "category_id": category_id,
        "category_label": category_label,
        "target_duration_sec": cfg["video"]["target_duration_sec"],
    })
    return idea


def _template_idea(category_id: str, category_label: str) -> dict:
    character = T.pick(T.CHARACTERS[category_id])
    character2 = T.pick([c for c in T.CHARACTERS[category_id] if c != character])
    setting = T.pick(T.SETTINGS[category_id])
    obj = T.pick(T.OBJECTS)
    hook_template = T.pick(T.HOOKS)
    hook = hook_template.format(char=character.capitalize(), char2=character2, object=obj)

    moral = T.pick(T.MORALS) if category_id == "mini_moral_stories" else None
    gag = T.pick(T.GAGS) if category_id in ("ai_cartoon_comedy", "funny_animal_shorts") else None

    logline_bits = [f"{character.capitalize()} is in {setting} when a {obj} changes everything."]
    if gag:
        logline_bits.append(f"Expect {gag} along the way.")
    if moral:
        logline_bits.append(f"By the end, everyone learns: {moral}")

    return {
        "title_seed": f"{character.title()} and the {obj.title()}",
        "character": character,
        "character_secondary": character2,
        "setting": setting,
        "object": obj,
        "hook": hook,
        "logline": " ".join(logline_bits),
        "moral": moral,
        "gag": gag,
    }


def _try_llm(cfg: dict, category_id: str, category_label: str):
    if cfg.get("content_engine") == "template":
        return None

    system = (
        "You are a viral short-form video idea generator for a family-friendly, "
        "AI-animated YouTube Shorts channel. Respond with ONLY valid JSON, no prose, "
        "no markdown fences."
    )
    prompt = f"""Generate ONE original video idea for the category "{category_label}".

Return JSON with exactly these keys:
{{
  "title_seed": "short working title, no emojis",
  "character": "one main character description, lowercase, no name",
  "character_secondary": "a second character description",
  "setting": "where it takes place",
  "object": "a key object or event that drives the plot",
  "hook": "a one-sentence hook for the first 2 seconds of the video",
  "logline": "2-3 sentence plot summary",
  "moral": "the lesson learned, or null if not applicable",
  "gag": "the comedic beat, or null if not applicable"
}}

Keep it wholesome, under {cfg['video']['target_duration_sec']} seconds of story, and original (not based on existing copyrighted characters or franchises)."""

    raw = llm_client.get_completion(prompt, system=system, cfg=cfg)
    parsed = llm_client.parse_json_safely(raw)
    if not parsed or "character" not in parsed:
        return None
    return parsed


if __name__ == "__main__":
    from src.config_loader import get_config
    import json as _json

    print(_json.dumps(generate_daily_idea(get_config()), indent=2))
