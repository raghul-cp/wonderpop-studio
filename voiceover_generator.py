"""
Step 4 of the pipeline: build the voice-over script (narration + dialogue,
merged into a single read-aloud track) and optionally synthesize it to an
mp3 using gTTS (free, no API key, needs internet).
"""

from pathlib import Path


def generate_voiceover_script(script: dict) -> dict:
    """
    Returns:
    {
        "full_text": str,                 # the complete read-aloud script
        "lines": [{"scene_number": int, "speaker": str, "text": str}, ...]
    }
    """
    lines = []
    for scene in script["scenes"]:
        if scene.get("narration"):
            lines.append({
                "scene_number": scene["scene_number"],
                "speaker": "Narrator",
                "text": scene["narration"],
            })
        for d in scene.get("dialogue", []):
            lines.append({
                "scene_number": scene["scene_number"],
                "speaker": d["speaker"],
                "text": d["line"],
            })

    full_text = "\n".join(f"[{l['speaker']}] {l['text']}" for l in lines)
    plain_text = " ".join(l["text"] for l in lines)  # for TTS, no speaker tags

    return {"full_text": full_text, "lines": lines, "plain_text": plain_text}


def synthesize_audio(voiceover: dict, out_path: Path, cfg: dict) -> str | None:
    """Generate an mp3 of the voice-over using gTTS. Returns the path, or None if skipped/failed."""
    if not cfg["voiceover_audio"]["enabled"]:
        return None

    try:
        from gtts import gTTS  # imported lazily so the rest of the pipeline works without it installed
    except ImportError:
        print("[voiceover_generator] gTTS not installed — run `pip install gTTS` or disable voiceover_audio in config.")
        return None

    text = voiceover["plain_text"].strip()
    if not text:
        return None

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tts = gTTS(text=text, lang=cfg["voiceover_audio"]["language"])
        tts.save(str(out_path))
        return str(out_path)
    except Exception as e:  # noqa: BLE001
        print(f"[voiceover_generator] TTS synthesis failed: {e}")
        return None


if __name__ == "__main__":
    import json as _json

    from src.config_loader import get_config
    from src.idea_generator import generate_daily_idea
    from src.script_writer import generate_script

    _cfg = get_config()
    _idea = generate_daily_idea(_cfg)
    _script = generate_script(_idea, _cfg)
    print(_json.dumps(generate_voiceover_script(_script), indent=2))
