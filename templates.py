"""
Template banks for the zero-cost "template" content engine.

These are plain Python data structures (lists/dicts) combined with
`random` at generation time. No network calls, no API keys, no cost.
This is the DEFAULT engine for the whole project — everything here
can run with nothing but `pip install -r requirements.txt`.

If you later plug in Ollama or the Anthropic API (see src/llm_client.py),
these banks are still used as a fallback whenever the LLM call fails,
so the pipeline never breaks a scheduled run.
"""

import random

# ---------------------------------------------------------------------------
# Characters & settings, grouped by category id (must match config.yaml)
# ---------------------------------------------------------------------------

CHARACTERS = {
    "ai_animal_adventures": [
        "a curious baby elephant", "a brave little fox", "a clumsy young panda",
        "a tiny determined turtle", "an adventurous baby penguin",
        "a shy but clever raccoon", "a bold little lion cub",
    ],
    "ai_cartoon_comedy": [
        "a panicky cartoon chicken", "an overconfident cartoon squirrel",
        "a dramatic cartoon cat", "a grumpy cartoon snail",
        "a hyperactive cartoon puppy", "a deadpan cartoon duck",
    ],
    "magical_fantasy_stories": [
        "a young dragon who can't breathe fire yet", "a forest fairy who lost her wings' glow",
        "a small wizard cat learning its first spell", "a star that fell into a sleepy village",
        "a tiny knight made of twigs and courage", "a moonlit unicorn foal",
    ],
    "mini_moral_stories": [
        "a hardworking ant", "a boastful young rabbit", "a kind but overlooked mouse",
        "two squabbling sparrow siblings", "a sheep who always copies others",
        "a small tortoise who never gives up",
    ],
    "funny_animal_shorts": [
        "a dramatic pug", "a sneaky cat burglar (of treats)", "an over-it housecat",
        "a goat who loves chaos", "a pigeon with main-character energy",
        "a very judgmental parrot",
    ],
}

SETTINGS = {
    "ai_animal_adventures": [
        "a sun-drenched savanna", "a misty mountain trail", "a bustling jungle river",
        "an icy arctic shoreline", "a quiet bamboo forest", "a windswept coastal cliff",
    ],
    "ai_cartoon_comedy": [
        "a chaotic backyard barbecue", "a too-small cardboard box fort",
        "a busy kitchen counter", "a suburban front lawn", "a messy kids' playroom",
        "a sleepy small-town street",
    ],
    "magical_fantasy_stories": [
        "a glowing enchanted forest", "a floating castle above the clouds",
        "a village under a giant friendly tree", "a crystal cave full of soft light",
        "a meadow where the stars come down to visit", "a riverbank lit by fireflies",
    ],
    "mini_moral_stories": [
        "a small farming village", "a cozy forest clearing", "a shared garden",
        "a riverside meeting spot", "a quiet schoolyard", "a warm family barn",
    ],
    "funny_animal_shorts": [
        "a suburban living room", "a sunny backyard", "a quiet home office gone wrong",
        "a kitchen at 2am", "a car ride that goes sideways", "a neighborhood park",
    ],
}

HOOKS = [
    "What {char} did next left everyone speechless...",
    "Nobody expected {char} to do THIS.",
    "{char} had ONE job. It didn't go as planned.",
    "This is the story of {char} and the biggest mistake of the day.",
    "You won't believe what happened when {char} found a mysterious {object}.",
    "{char} thought it was a normal day. It was not.",
    "Watch what happens when {char} meets {char2}.",
]

OBJECTS = [
    "glowing stone", "shiny red button", "mysterious old map", "talking seed",
    "tiny golden key", "strange floating feather", "cracked magic egg",
    "unopened box with no label", "half-eaten sandwich", "lost balloon",
]

MORALS = [
    "Kindness always finds its way back to you.",
    "Real courage means trying again after you fall.",
    "The smallest friend can make the biggest difference.",
    "Slow and steady really does win the race.",
    "It's okay to ask for help — that's not weakness, that's wisdom.",
    "What looks different on the outside can be a true friend on the inside.",
    "A little patience turns a disaster into a good story.",
]

GAGS = [
    "a dramatic slow-motion fail", "a surprise twist nobody saw coming",
    "an over-the-top double-take", "a classic banana-peel style stumble",
    "an unexpected team-up with the last creature you'd expect",
    "a perfectly timed sneeze that ruins everything",
    "a staring contest that escalates way too far",
]

TITLE_FORMULAS = [
    "{char} vs The {object} 😱 | WonderPop Studio",
    "This {category} Short Will Make Your Day 🥹",
    "{char} Had NO IDEA This Would Happen 😂",
    "The Tiny Hero Nobody Believed In 🐾",
    "Wholesome {category} Moment You Didn't Expect ✨",
    "POV: {char} Just Wanted a Normal Day 🤣",
    "A {category} Story About {theme}",
]

CTA_LINES = [
    "Subscribe for a brand-new WonderPop story every day! 🌟",
    "Follow WonderPop Studio for more magical shorts! ✨",
    "Which character was your favorite? Comment below! 💬",
    "Tap follow — tomorrow's story might be even wilder. 🐾",
]

CATEGORY_LABELS = {
    "ai_animal_adventures": "AI Animal Adventures",
    "ai_cartoon_comedy": "AI Cartoon Comedy",
    "magical_fantasy_stories": "Magical Fantasy Stories",
    "mini_moral_stories": "Mini Moral Stories",
    "funny_animal_shorts": "Funny Animal Shorts",
}

VISUAL_STYLES = {
    "ai_animal_adventures": "warm natural lighting, painterly realism blended with soft 3D animation",
    "ai_cartoon_comedy": "bold flat-shaded cartoon style, exaggerated expressions, bright saturated colors",
    "magical_fantasy_stories": "dreamy soft-focus fantasy illustration, glowing particles, pastel palette",
    "mini_moral_stories": "gentle storybook illustration style, warm earthy tones",
    "funny_animal_shorts": "punchy modern 3D cartoon style, exaggerated poses, high contrast lighting",
}


def pick_category(categories_cfg):
    """Weighted-random category pick from config's content_categories list."""
    ids = [c["id"] for c in categories_cfg]
    weights = [c.get("weight", 1) for c in categories_cfg]
    return random.choices(ids, weights=weights, k=1)[0]


def pick(seq):
    return random.choice(seq)
