"""
bluepic plugin — detects Bluesky post links and replies with a native Google Chat card.

Uses the Bluesky public API (no auth required for public posts).
"""

import logging
import re

import requests

logger = logging.getLogger(__name__)

PATTERN = re.compile(
    r"https?://bsky\.app/profile/([^/]+)/post/([a-zA-Z0-9]+)",
    re.IGNORECASE,
)


def _fetch_post(handle: str, rkey: str) -> dict:
    uri = f"at://{handle}/app.bsky.feed.post/{rkey}"
    resp = requests.get(
        "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread",
        params={"uri": uri, "depth": 0},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(data.get("message", "unknown error"))
    return data["thread"]["post"]


def _build_card(post: dict, rkey: str, post_url: str) -> dict:
    author = post["author"]
    record = post["record"]

    text = record.get("text", "")
    likes = f"{post.get('likeCount', 0):,}"
    reposts = f"{post.get('repostCount', 0):,}"
    replies = f"{post.get('replyCount', 0):,}"

    widgets = [
        {"textParagraph": {"text": text}},
    ]

    # Inline images
    embed = post.get("embed", {})
    if embed.get("$type") == "app.bsky.embed.images#view":
        for img in embed.get("images", [])[:4]:
            widgets.append({
                "image": {
                    "imageUrl": img.get("fullsize", img.get("thumb", "")),
                    "altText": img.get("alt", ""),
                    "onClick": {"openLink": {"url": post_url}},
                }
            })

    widgets.append({
        "textParagraph": {"text": f"❤️ {likes}   🔁 {reposts}   💬 {replies}"}
    })

    return {
        "message": {
            "cardsV2": [{
                "cardId": f"bsky-{rkey}",
                "card": {
                    "header": {
                        "title": author.get("displayName", author["handle"]),
                        "subtitle": f"@{author['handle']}",
                        "imageUrl": author.get("avatar", ""),
                        "imageType": "CIRCLE",
                    },
                    "sections": [{"widgets": widgets}],
                },
            }]
        }
    }


def handle(text: str, sender: dict, space: str):
    m = PATTERN.search(text)
    if not m:
        return None

    handle_str, rkey = m.group(1), m.group(2)
    logger.info("bluepic: fetching %s/post/%s", handle_str, rkey)

    try:
        post = _fetch_post(handle_str, rkey)
        return _build_card(post, rkey, m.group(0))
    except requests.HTTPError as e:
        logger.warning("Bluesky API request failed: %s", e)
        return "couldn't fetch that post (private or deleted?)"
    except Exception:
        logger.exception("bluepic failed for %s/%s", handle_str, rkey)
        return "couldn't fetch that post"
