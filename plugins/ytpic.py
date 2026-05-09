"""
ytpic plugin — detects YouTube links and replies with a video preview card.

Uses the YouTube oEmbed API. No API key required.
"""

import logging
import re

import requests

logger = logging.getLogger(__name__)

PATTERN = re.compile(
    r"https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    re.IGNORECASE,
)


def handle(text: str, sender: dict, space: str):
    m = PATTERN.search(text)
    if not m:
        return None

    video_id = m.group(1)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info("ytpic: fetching metadata for %s", video_id)

    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": video_url, "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "message": {
                "cardsV2": [{
                    "cardId": f"yt-{video_id}",
                    "card": {
                        "header": {
                            "title": data["title"],
                            "subtitle": data["author_name"],
                        },
                        "sections": [{
                            "widgets": [{
                                "image": {
                                    "imageUrl": data["thumbnail_url"],
                                    "altText": data["title"],
                                    "onClick": {"openLink": {"url": video_url}},
                                }
                            }]
                        }]
                    }
                }]
            }
        }
    except (KeyError, ValueError) as e:
        logger.warning("ytpic: malformed oEmbed response for %s: %s", video_id, e)
        return "couldn't parse that video's metadata"
    except requests.HTTPError as e:
        logger.warning("YouTube oEmbed request failed: %s", e)
        return "couldn't fetch that video (private or deleted?)"
    except Exception:
        logger.exception("ytpic failed for %s", video_id)
        return "couldn't fetch that video"
