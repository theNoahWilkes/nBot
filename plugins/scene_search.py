"""
scene_search plugin — meme screenshots from Frinkiac, Morbotron, and friends.

Each site runs the same API stack, so one plugin handles all of them.
To add a new site, add an entry to SITES.

Triggers:
    frink / frinkiac <query>   → Simpsons (frinkiac.com)
    morb / morbotron <query>   → Futurama (morbotron.com)
    rick <query>               → Rick and Morty (masterofallscience.com)
"""

import base64
import json
import logging
import math
import re
from random import choice, choices

import requests

logger = logging.getLogger(__name__)

SITES = [
    {
        "pattern": re.compile(r"^frin(?:k|kiac)?\s+(.+)", re.IGNORECASE),
        "base_url": "https://frinkiac.com",
        "weighted": True,
    },
    {
        "pattern": re.compile(r"^morb(?:o|otron)?\s+(.+)", re.IGNORECASE),
        "base_url": "https://morbotron.com",
        "weighted": True,
    },

]


def _weighted_choice(results: list) -> dict:
    lm = max(1, int(len(results) * 0.16))
    weights = [((math.e ** -lm) * lm ** i) / math.factorial(i) for i in range(len(results))]
    return choices(results, weights=weights)[0]


def _fetch_meme(query: str, site: dict) -> str | None:
    base = site["base_url"]

    results = requests.get(f"{base}/api/search", params={"q": query}, timeout=10).json()
    if not results:
        return None

    pick = _weighted_choice(results) if site["weighted"] else choice(results)
    ep, ts = pick["Episode"], pick["Timestamp"]

    try:
        caption_data = requests.get(f"{base}/api/caption?e={ep}&t={ts}", timeout=10).json()
        caption = " ".join(s["Content"] for s in caption_data["Subtitles"]).strip()
    except Exception:
        logger.warning("caption fetch failed for %s, using empty caption", base)
        caption = ""

    overlays = [{"t": caption, "f": "akbar", "s": 0, "c": "ffffffff", "x": 50, "y": 97, "a": "c", "b": 0, "d": 0, "u": 1}] if caption else []
    panels = [{"e": ep, "ts": ts, "o": overlays}]
    b64 = base64.urlsafe_b64encode(json.dumps(panels, separators=(',', ':')).encode()).decode()
    return f"{base}/comic/img?b64={b64}"


def handle(text: str, sender: dict, space: str):
    for site in SITES:
        m = site["pattern"].match(text.strip())
        if not m:
            continue

        query = m.group(1).strip()
        logger.info("scene_search: querying %s for %r", site["base_url"], query)

        try:
            meme_url = _fetch_meme(query, site)
        except Exception:
            logger.exception("scene_search request failed")
            return "couldn't reach the search API, try again"

        if meme_url is None:
            return "Nothing found. Try again, for glayvin out loud!"

        return {
            "message": {
                "cardsV2": [{
                    "cardId": "scene-meme",
                    "card": {
                        "sections": [{"widgets": [{
                            "image": {
                                "imageUrl": meme_url,
                                "altText": query,
                                "onClick": {"openLink": {"url": meme_url}},
                            }
                        }]}]
                    }
                }]
            }
        }

    return None
