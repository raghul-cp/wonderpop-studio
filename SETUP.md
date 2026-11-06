# Setup Guide (Beginner-Friendly)

This walks you from "empty GitHub account" to "WonderPop Studio automatically
generates a Short every day." Follow it top to bottom the first time.

Estimated time: 20-30 minutes for content generation only; +20 minutes if you
also set up YouTube uploads.

---

## Part 1 — Get the project onto your computer and GitHub

### 1.1 Prerequisites
- A GitHub account (free) — [github.com](https://github.com)
- Python 3.10 or newer installed — check with `python3 --version`
- Git installed — check with `git --version`
- (Only if you want uploads) A Google account that owns/manages your WonderPop
  Studio YouTube channel

### 1.2 Create the GitHub repository
1. Go to [github.com/new](https://github.com/new).
2. Repository name: `wonderpop-youtube-ai-agent` (or anything you like).
3. Choose **Public** or **Private** — either works. Private is fine and keeps
   your generated scripts out of public view if you prefer.
4. Don't initialize with a README (we already have one) — just click **Create repository**.

### 1.3 Push this project to it
From inside this project's folder on your computer:

```bash
git init
git add .
git commit -m "Initial commit: WonderPop YouTube AI Agent"
git branch -M main
git remote add origin https://github.com/<your-username>/wonderpop-youtube-ai-agent.git
git push -u origin main
```

(Replace `<your-username>` with your actual GitHub username.)

---

## Part 2 — Run it locally first (recommended before automating)

```bash
cd wonderpop-youtube-ai-agent
python -m venv venv
source venv/bin/activate        # Windows (PowerShell): venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Also install **ffmpeg** (needed only for the video-assembly step — skip this if
you only want ideas/scripts/SEO text for now):
- **Mac:** `brew install ffmpeg`
- **Windows:** `winget install ffmpeg` (or download from ffmpeg.org)
- **Linux:** `sudo apt install ffmpeg`

Now test it:

```bash
# Generates everything, prints progress, writes nothing to disk — safest first test
python -m src.main --dry-run

# Full run: writes scripts + metadata to data/, skips images/video/upload
python -m src.main --no-video

# Full run including free image generation, free TTS audio, and local video assembly
python -m src.main

# Run the offline test suite
pytest
```

Open `data/scripts/<today's-id>.md` to read the generated script, and
`data/metadata/<today's-id>.json` for the full SEO package. If you enabled
video assembly, check `data/media/<id>/short.mp4`.

Everything above runs with **zero API keys** using the built-in `template`
content engine — this is the default and costs nothing.

---

## Part 3 — (Optional) Better scripts with a free or paid AI engine

The default `template` engine produces structured, varied scripts using
hand-written banks of characters/settings/hooks/morals. It's free and
reliable, but a real language model will write more natural dialogue.

**Option A — stay free, use a local model via Ollama:**
1. Install [Ollama](https://ollama.com).
2. `ollama pull llama3.2:1b` (a small, fast, free model — or use a larger one
   if your machine can handle it).
3. `ollama serve` (leave it running).
4. In `.env`, set `CONTENT_ENGINE=ollama`.
5. Re-run `python -m src.main --dry-run` and check the output quality.

**Option B — pay for the best quality, use the Claude API:**
1. Get an API key from [console.anthropic.com](https://console.anthropic.com).
2. In `.env`, set `CONTENT_ENGINE=anthropic` and `ANTHROPIC_API_KEY=sk-ant-...`.
3. This is a **paid, per-token service** — monitor usage in the Anthropic console.

Both are entirely optional. Skip this section to stay on the free default.

---

## Part 4 — (Optional) Connect YouTube for scheduled uploads

Skip this whole part if you just want the agent to generate content for you
to review and upload manually — that's a completely valid way to use this
project.

### 4.1 Create a Google Cloud project
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project (e.g. "WonderPop Agent").
2. In the search bar, find **"YouTube Data API v3"** and click **Enable**.

### 4.2 Configure the OAuth consent screen
1. Go to **APIs & Services → OAuth consent screen**.
2. User type: **External** (unless you have a Google Workspace org).
3. Fill in the required app name/contact fields. You don't need to submit for
   verification — a personal/unverified app works fine as long as you add
   yourself as a test user (next step), since you're the only person using it.
4. Under **Test users**, add the Google account email that owns your YouTube channel.

### 4.3 Create an OAuth Client ID
1. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Desktop app**.
3. Name it anything (e.g. "WonderPop Agent Desktop").
4. Click **Create**, then **Download JSON**.
5. Rename the downloaded file to `client_secret.json` and place it in this
   project's root folder. (It's already in `.gitignore` — it will never be committed.)

### 4.4 Generate your refresh token (one-time, local only)
```bash
python -m src.get_youtube_token
```
A browser window opens. Sign in with the account that owns your channel and
approve access. The script prints three values:

```
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...
```

Keep this terminal output private — these let the holder upload to your channel.

### 4.5 Add them as GitHub Secrets
In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**.
Add each of these three (and, only if you're using the paid Claude engine, a
fourth):

| Secret name | Value |
|---|---|
| `YOUTUBE_CLIENT_ID` | from step 4.4 |
| `YOUTUBE_CLIENT_SECRET` | from step 4.4 |
| `YOUTUBE_REFRESH_TOKEN` | from step 4.4 |
| `ANTHROPIC_API_KEY` | *(optional, only if `CONTENT_ENGINE=anthropic`)* |

### 4.6 Turn uploads on
In `config/config.yaml`, set:
```yaml
upload:
  enabled: true
  privacy_status: "private"   # start with private or unlisted until you trust the output!
```
**Strongly recommended:** keep `privacy_status: "private"` (or `"unlisted"`)
for at least your first week of runs. Review each generated video in YouTube
Studio and manually flip it to public yourself until you're confident in the
pipeline's output quality.

---

## Part 5 — Turn on the daily automation

The workflow at `.github/workflows/daily_content.yml` is already configured
to run every day at **01:30 UTC** (edit the `cron:` line to change this —
[crontab.guru](https://crontab.guru) helps write cron expressions) and to:
1. Install dependencies + ffmpeg on a fresh GitHub-hosted runner.
2. Run the full pipeline.
3. Commit the generated scripts/metadata back into your repo.
4. Upload the generated video/audio as a 7-day workflow artifact (so you can
   download and review it even if `upload.enabled` is still `false`).

Once you've pushed this repo to GitHub (Part 1), the workflow is already
active — no extra step needed. You can also trigger it manually any time:

1. Go to your repo's **Actions** tab.
2. Click **WonderPop Daily Content** in the left sidebar.
3. Click **Run workflow**. You can optionally force a specific category or
   turn uploads on for just that run.

### Where to find results
- **Scripts & SEO metadata:** committed into `data/scripts/` and `data/metadata/` in your repo — browse them on GitHub directly.
- **Generated images/audio/video:** attached to each workflow run as a downloadable artifact (Actions tab → the run → Artifacts section), kept for 7 days.
- **Uploaded videos:** in your YouTube Studio, under Content (as private/unlisted/scheduled depending on your config).

---

## Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your activated venv. |
| Video assembly fails silently | ffmpeg isn't installed, or ImageMagick isn't installed (captions only — video still renders without captions). |
| `invalid_grant` on upload | Your refresh token was revoked (e.g. you changed your Google account password, or 6 months of inactivity for unverified/testing apps). Re-run `python -m src.get_youtube_token` and update the GitHub Secret. |
| `quotaExceeded` on upload | The YouTube Data API's free daily quota (10,000 units) is used up — an upload costs ~1,600 units, so roughly 6 uploads/day max. Wait until the next day (resets at midnight Pacific Time). |
| Images don't generate | Pollinations.ai had a transient failure or rate-limited you — the pipeline logs a warning and continues without that scene's image rather than failing the whole run. Just re-run. |
| GitHub Action can't push | Make sure the workflow has `permissions: contents: write` (already set in the provided workflow file) and that branch protection rules on `main` allow the `github-actions` bot to push, if you've added any. |
| Workflow doesn't run on schedule | GitHub disables scheduled workflows on repos with no activity for 60 days — push any commit, or trigger manually, to keep it alive. |

---

## What this project intentionally does NOT do

- It does not generate full AI-animated video frames (that requires paid
  video-generation models). The free video assembler instead creates a
  motion slideshow from AI-generated still images + voice-over — a solid
  first draft, not a finished animated short. Treat its output as a base to
  polish in a free editor (CapCut, DaVinci Resolve, Shotcut) if you want a
  more produced look.
- It does not pick your content's "made for kids" status or synthetic-media
  disclosure for you — both are legal/policy judgment calls, so the config
  defaults to the safer `false`/manual-review options and links you to
  YouTube's own guidance (see the README's Compliance section).
- It does not bypass any YouTube quota, verification, or policy requirement.
