import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a film aesthetics curator. You analyze films based on \
their cinematography, color grading, pacing, and emotional \
atmosphere — not just their genre or plot. You return ONLY \
valid JSON. No preamble, no explanation, no markdown fences. \
Never hallucinate films that don't exist. Never hallucinate details."""


def get_film_titles(aura_query: str) -> list:
    user_message = f"""A user is looking for films that feel like: {aura_query}

Return a JSON array of exactly 5 real films that best match this aesthetic.
Only include films you are fully confident exist.

Each object must have exactly these fields:
- title (string — exact film title)
- year (integer)

Return nothing except the JSON array."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    raw = message.content[0].text
    print(f"Claude titles: {raw}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"Claude invalid JSON: {raw}")
        return []


def analyze_films(aura_query: str, films: list) -> list:
    film_list = "\n".join([
        f"- {film['title']} ({film['year']}): {film.get('overview', '')}"
        for film in films
    ])

    user_message = f"""A user is looking for films that feel like: {aura_query}

Analyze the aesthetic of each film below using the overview as factual context.
Only include films you can confidently describe.

Films:
{film_list}

Each object in the JSON array must have exactly these fields:
- title (string — must match exactly)
- color_palette (array of exactly 3 hex value strings representing dominant cinematography colors)
- tone (array of exactly 2 from: dark, playful, sincere, ironic, dreamlike, gritty, poetic, absurd, cold, warm)
- mood (array of exactly 2 from: joyful, melancholic, anxious, unsettling, romantic, lonely, hopeful, bleak, nostalgic, tense)
- pacing (exactly 1 from: relentless, slow burn, frenetic, meditative, rhythmic, jarring)
- aura_match (one sentence explaining the aesthetic match to the user's query)
- letterboxd_slug (url-formatted slug, e.g. blade-runner-2049)

Return nothing except the JSON array."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    raw = message.content[0].text
    print(f"Claude analysis: {raw}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"Claude invalid JSON: {raw}")
        return []


def get_similar_and_analyze(seed_film: dict) -> list:
    user_message = f"""This film has the following profile:

Title: {seed_film['title']} ({seed_film['year']})
Overview: {seed_film.get('overview', '')}
Director: {seed_film.get('director', '')}

Find exactly 5 real films with a similar aesthetic to this one.
Do not include {seed_film['title']} itself.
Analyze each film's aesthetic using your knowledge of its cinematography.

Return a JSON array where each object has exactly:
- title (string — exact film title)
- year (integer)
- color_palette (array of exactly 3 hex value strings)
- tone (array of exactly 2 from: dark, playful, sincere, ironic, dreamlike, gritty, poetic, absurd, cold, warm)
- mood (array of exactly 2 from: joyful, melancholic, anxious, unsettling, romantic, lonely, hopeful, bleak, nostalgic, tense)
- pacing (exactly 1 from: relentless, slow burn, frenetic, meditative, rhythmic, jarring)
- aura_match (one sentence explaining why it matches aesthetically)
- letterboxd_slug (url-formatted slug)

Return nothing except the JSON array."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    raw = message.content[0].text
    print(f"Claude similar+analyze: {raw}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"Claude invalid JSON: {raw}")
        return []