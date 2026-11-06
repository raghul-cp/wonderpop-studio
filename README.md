# WonderPop YouTube AI Agent

An automated content pipeline for **WonderPop Studio** that, once a day, generates
a complete YouTube Short package — idea → script → scene-by-scene AI image/video
prompts → voice-over → SEO metadata → (optionally) an assembled vertical video →
(optionally) a scheduled YouTube upload — and commits everything it makes back
into this repository so you have a running archive.

Content pillars: **AI Animal Adventures · AI Cartoon Comedy · Magical Fantasy
Stories · Mini Moral Stories · Funny Animal Shorts**.

➡️ **First time here? Read [SETUP.md](SETUP.md)** for the full beginner-friendly,
step-by-step configuration guide. This file is the project overview.

## What it does, daily

```
 1. Idea Generator        -> picks a category + a fresh story idea
 2. Script Writer         -> 6-scene script with dialogue, narration, camera notes
 3. Prompt Generator      -> an image prompt + a motion prompt per scene
                             (+ optionally generates the actual images, free, via Pollinations.ai)
 4. Voice-over Generator  -> a full read-aloud script
                             (+ optionally synthesizes mp3 audio, free, via gTTS)
 5. SEO Generator         -> title, description, tags, hashtags
 6. Video Assembler       -> stitches images + audio into a 1080x1920 (9:16) mp4
                             (free, local, via moviepy/ffmpeg)
 7. Metadata Store        -> saves everything to data/ as JSON + Markdown
 8. YouTube Uploader      -> optional scheduled upload via the YouTube Data API
```

Steps 3's image generation, 4's audio synthesis, 6, and 8 are **off by default
upload-wise** and can each be toggled independently in `config/config.yaml` —
you can run this as a pure "idea + script + prompts + SEO" generator with zero
external calls at all if you prefer.

## Cost: free by default

| Component | Default | Cost |
|---|---|---|
| Idea / script / SEO generation | `template` engine | **$0** — offline, no API key |
| Image generation | Pollinations.ai | **$0** — no API key |
| Voice-over audio | gTTS | **$0** — no API key |
| Video assembly | moviepy + ffmpeg | **$0** — runs locally / on the Actions runner |
| YouTube upload | YouTube Data API | **$0** — free quota (10,000 units/day, ~6 uploads/day) |
| GitHub Actions | public repo | **$0** — 2,000 free minutes/month on a free account |

Two **optional, opt-in upgrades** cost money if you choose to turn them on:
- `CONTENT_ENGINE=anthropic` for higher-quality scripts via the paid Claude API.
- A paid image/video generation service, if you swap one in for Pollinations.ai.
Neither is required, and neither is on by default.

## Project structure

```
wonderpop-youtube-ai-agent/
├── config/config.yaml        # all settings: channel info, categories, video specs, toggles
├── prompts/templates.py      # the free offline template banks (characters, hooks, morals, SEO formulas)
├── src/
│   ├── main.py                # orchestrator / CLI entry point
│   ├── config_loader.py       # loads config.yaml + .env
│   ├── llm_client.py          # pluggable template / Ollama / Anthropic backend
│   ├── idea_generator.py      # step 1
│   ├── script_writer.py       # step 2
│   ├── prompt_generator.py    # step 3 (+ Pollinations.ai image generation)
│   ├── voiceover_generator.py # step 4 (+ gTTS audio)
│   ├── seo_generator.py       # step 5
│   ├── video_assembler.py     # step 6 (moviepy)
│   ├── metadata_store.py      # step 7
│   ├── youtube_uploader.py    # step 8 (YouTube Data API)
│   └── get_youtube_token.py   # one-time local OAuth setup helper
├── data/                      # generated output (scripts/metadata are git-tracked; media is gitignored)
├── tests/test_basic.py        # offline smoke tests (no API keys needed)
└── .github/workflows/daily_content.yml  # the daily automation
```

## Quick start (local)

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m src.main --dry-run          # generates everything, writes nothing, no upload
python -m src.main --no-video         # full run, text/metadata only, writes to data/
pytest                                # run the offline test suite
```

Full setup (GitHub repo, Secrets, YouTube OAuth, scheduling) is in **[SETUP.md](SETUP.md)**.

## Compliance note (read before scheduling public uploads)

- This tool generates **original** stories/characters — it never names or imitates
  existing copyrighted franchises, and you should keep it that way when editing
  `prompts/templates.py` or your LLM prompts.
- YouTube has a `status.containsSyntheticMedia` field for disclosing **realistic**
  altered/synthetic content (e.g. a real person appearing to say something they
  didn't). Stylized cartoon/animated content like WonderPop's generally isn't
  what that flag targets, but policies evolve — check
  [YouTube's current A/S content policy](https://support.google.com/youtube/answer/14328491)
  yourself before you start publishing at scale, and set
  `upload.contains_synthetic_media` in `config/config.yaml` accordingly.
- `channel.made_for_kids` in `config/config.yaml` defaults to `false`. Whether your
  content legally counts as "made for kids" (COPPA) is your call to make, not
  something this tool decides for you — see
  [YouTube's made-for-kids guidance](https://support.google.com/youtube/answer/9528076).
- The generated video is a simple first-draft slideshow-with-motion, not a
  polished animation. Review it before publishing, and feel free to pull the
  images/audio into CapCut, DaVinci Resolve, or another free editor to finish it.
