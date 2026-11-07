"""
Step 2 of the pipeline: turn an idea into a full scene-by-scene script
with dialogue, action, and per-scene timing.

Produces a dict:
{
    "idea_id": str,
    "title": str,
    "scenes": [
        {
            "scene_number": 1,
            "setting": str,
            "characters": [str, ...],
            "action": str,             # what happens, for the storyboard/image prompt
            "dialogue": [ {"speaker": str, "line": str}, ... ],
            "narration": str | None,   # third-person narration line, if any
            "duration_sec": int,
            "camera_notes": str,
        }, ...
    ],
    "total_duration_sec": int,
}
"""

import templates as T
from src import llm_client


def generate_script(idea: dict, cfg: dict) -> dict:
    llm_script = _try_llm(idea, cfg)
    if llm_script:
        script = llm_script
    else:
        script = _template_script(idea, cfg)

    script["idea_id"] = idea["id"]
    script.setdefault("title", idea["title_seed"])
    script["total_duration_sec"] = sum(s.get("duration_sec", 0) for s in script["scenes"])
    return script


# ---------------------------------------------------------------------------
# Template engine — a fixed 6-beat story structure, filled from the idea.
# ---------------------------------------------------------------------------

def _template_script(idea: dict, cfg: dict) -> dict:
    n_scenes = cfg["video"]["scenes_per_video"]
    target = cfg["video"]["target_duration_sec"]
    per_scene = max(4, target // n_scenes)

    char = idea["character"]
    char2 = idea.get("character_secondary", "a new friend")
    setting = idea["setting"]
    obj = idea["object"]
    moral = idea.get("moral")
    gag = idea.get("gag")

    beats = [
        {
            "scene_number": 1,
            "setting": setting,
            "characters": [char],
            "action": f"Open on {char} in {setting}, going about an ordinary moment. Establish the mood instantly.",
            "dialogue": [],
            "narration": idea["hook"],
            "camera_notes": "Wide establishing shot, slow push-in.",
        },
        {
            "scene_number": 2,
            "setting": setting,
            "characters": [char],
            "action": f"{char.capitalize()} notices the {obj} and reacts with surprise/curiosity.",
            "dialogue": [{"speaker": char.title(), "line": f"Wait... what IS that?"}],
            "narration": None,
            "camera_notes": "Close-up on character's face, quick zoom on the object.",
        },
        {
            "scene_number": 3,
            "setting": setting,
            "characters": [char, char2],
            "action": f"{char2.title()} shows up, and the two react to each other and the {obj}.",
            "dialogue": [
                {"speaker": char2.title(), "line": "Hey! Is that what I think it is?"},
                {"speaker": char.title(), "line": "Only one way to find out."},
            ],
            "narration": None,
            "camera_notes": "Two-shot, medium framing.",
        },
        {
            "scene_number": 4,
            "setting": setting,
            "characters": [char, char2],
            "action": (gag or "A small plan goes hilariously wrong, raising the stakes.") +
                      f" The {obj} does something unexpected.",
            "dialogue": [{"speaker": char.title(), "line": "Okay, THAT was not part of the plan!"}],
            "narration": None,
            "camera_notes": "Dynamic action framing, fast cuts.",
        },
        {
            "scene_number": 5,
            "setting": setting,
            "characters": [char, char2],
            "action": f"{char.capitalize()} and {char2} work together to resolve the situation with the {obj}.",
            "dialogue": [{"speaker": char2.title(), "line": "Together, we've got this."}],
            "narration": None,
            "camera_notes": "Medium shot, warm lighting shift signaling resolution.",
        },
        {
            "scene_number": 6,
            "setting": setting,
            "characters": [char, char2],
            "action": "Resolution beat. " + (f"Narration delivers the moral: {moral}" if moral else "A warm, satisfying final beat and a smile to camera."),
            "dialogue": [],
            "narration": (moral if moral else f"And that's how {char} and {char2} turned an ordinary day into one to remember."),
            "camera_notes": "Slow pull-back, soft fade.",
        },
    ]

    scenes = beats[:n_scenes] if n_scenes < len(beats) else beats
    for s in scenes:
        s["duration_sec"] = per_scene

    return {"scenes": scenes}


# ---------------------------------------------------------------------------
# LLM engine
# ---------------------------------------------------------------------------

def _try_llm(idea: dict, cfg: dict):
    if cfg.get("content_engine") == "template":
        return None

    system = (
        "You are a professional short-form video scriptwriter for a family-friendly "
        "AI-animated YouTube Shorts channel. Respond with ONLY valid JSON, no prose, "
        "no markdown fences."
    )
    n_scenes = cfg["video"]["scenes_per_video"]
    target = cfg["video"]["target_duration_sec"]

    prompt = f"""Write a {n_scenes}-scene video script for this idea:

Title: {idea['title_seed']}
Logline: {idea['logline']}
Main character: {idea['character']}
Secondary character: {idea.get('character_secondary', '')}
Setting: {idea['setting']}
Key object/event: {idea['object']}
Moral (if any): {idea.get('moral')}
Target total duration: {target} seconds across {n_scenes} scenes.

Return JSON with exactly this shape:
{{
  "title": "polished video title, no emojis",
  "scenes": [
    {{
      "scene_number": 1,
      "setting": "...",
      "characters": ["..."],
      "action": "what happens visually, for a storyboard artist",
      "dialogue": [{{"speaker": "...", "line": "..."}}],
      "narration": "third-person narration line, or null",
      "duration_sec": 8,
      "camera_notes": "shot type / camera movement"
    }}
  ]
}}

Keep dialogue short and punchy (Shorts pacing). Keep it wholesome and original."""

    raw = llm_client.get_completion(prompt, system=system, max_tokens=2000, cfg=cfg)
    parsed = llm_client.parse_json_safely(raw)
    if not parsed or "scenes" not in parsed or not parsed["scenes"]:
        return None
    return parsed


if __name__ == "__main__":
    import json as _json

    from src.config_loader import get_config
    from src.idea_generator import generate_daily_idea

    _cfg = get_config()
    _idea = generate_daily_idea(_cfg)
    print(_json.dumps(generate_script(_idea, _cfg), indent=2))
