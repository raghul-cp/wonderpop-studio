"""
Step 5 of the pipeline: SEO-friendly titles, description, tags, hashtags.
"""

import templates as T
from src import llm_client


def generate_seo(idea: dict, script: dict, cfg: dict) -> dict:
    llm_seo = _try_llm(idea, script, cfg)
    if llm_seo:
        seo = llm_seo
    else:
        seo = _template_seo(idea, script, cfg)

    # Always enforce the hard limits regardless of which engine produced the text.
    seo["title"] = seo["title"][: cfg["seo"]["title_max_chars"]]
    seo["description"] = seo["description"][: cfg["seo"]["description_max_chars"]]
    seo["tags"] = seo["tags"][: cfg["seo"]["max_tags"]]
    return seo


def _template_seo(idea: dict, script: dict, cfg: dict) -> dict:
    char = idea["character"].title()
    obj = idea["object"].title()
    category_label = idea["category_label"]
    theme = idea.get("moral") or idea.get("gag") or "an unforgettable adventure"

    title_formula = T.pick(T.TITLE_FORMULAS)
    title = title_formula.format(char=char, object=obj, category=category_label, theme=theme)

    description_lines = [
        script.get("title", idea["title_seed"]),
        "",
        idea["logline"],
        "",
        f"🎬 A {category_label} short from WonderPop Studio — new AI-animated stories daily!",
        "",
        T.pick(T.CTA_LINES),
        "",
        " ".join(cfg["seo"]["base_hashtags"] + _hashtags_for_category(idea["category_id"])),
    ]
    description = "\n".join(description_lines)

    tags = list(dict.fromkeys(
        cfg["seo"]["channel_keywords"]
        + [category_label, char.lower(), obj.lower(), "shorts", "ai animation", "kids story", "wonderpop studio"]
    ))

    hashtags = cfg["seo"]["base_hashtags"] + _hashtags_for_category(idea["category_id"])

    return {"title": title, "description": description, "tags": tags, "hashtags": hashtags}


def _hashtags_for_category(category_id: str) -> list[str]:
    mapping = {
        "ai_animal_adventures": ["#AnimalAdventure", "#AIAnimals"],
        "ai_cartoon_comedy": ["#CartoonComedy", "#FunnyShorts"],
        "magical_fantasy_stories": ["#FantasyStory", "#MagicalShorts"],
        "mini_moral_stories": ["#MoralStory", "#KidsStory"],
        "funny_animal_shorts": ["#FunnyAnimals", "#PetComedy"],
    }
    return mapping.get(category_id, [])


def _try_llm(idea: dict, script: dict, cfg: dict):
    if cfg.get("content_engine") == "template":
        return None

    system = (
        "You are a YouTube SEO specialist for a family-friendly AI-animated Shorts channel. "
        "Respond with ONLY valid JSON, no prose, no markdown fences."
    )
    prompt = f"""Write SEO metadata for this YouTube Short.

Title seed: {idea['title_seed']}
Category: {idea['category_label']}
Logline: {idea['logline']}
Script title: {script.get('title', '')}

Return JSON:
{{
  "title": "under {cfg['seo']['title_max_chars']} chars, punchy, curiosity-driven, no clickbait lies",
  "description": "2-4 short paragraphs, includes a call to subscribe, includes hashtags at the end",
  "tags": ["up to {cfg['seo']['max_tags']} relevant keyword tags"],
  "hashtags": ["3-6 hashtags including #Shorts"]
}}"""

    raw = llm_client.get_completion(prompt, system=system, cfg=cfg)
    parsed = llm_client.parse_json_safely(raw)
    if not parsed or "title" not in parsed:
        return None
    return parsed


if __name__ == "__main__":
    import json as _json

    from src.config_loader import get_config
    from src.idea_generator import generate_daily_idea
    from src.script_writer import generate_script

    _cfg = get_config()
    _idea = generate_daily_idea(_cfg)
    _script = generate_script(_idea, _cfg)
    print(_json.dumps(generate_seo(_idea, _script, _cfg), indent=2))
