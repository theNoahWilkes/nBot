"""
twitpic plugin — detects Twitter/X links and replies with a native Google Chat card.

Uses the fxtwitter API to fetch tweet data. No browser automation required.

Dependencies: requests
"""

import logging
import re

import requests

logger = logging.getLogger(__name__)

PATTERN = re.compile(
    r"https?://(?:www\.)?(?:twitter|x)\.com/([a-zA-Z0-9_]{1,15})/status/(\d+)",
    re.IGNORECASE,
)


def _fetch_tweet(user: str, tweet_id: str) -> dict:
    resp = requests.get(
        f"https://api.fxtwitter.com/{user}/status/{tweet_id}",
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise ValueError(f"fxtwitter returned code {data.get('code')}")
    return data["tweet"]


def _build_card(tweet: dict) -> dict:
    author = tweet["author"]

    subtitle = f"@{author['screen_name']}"
    if author.get("verification", {}).get("verified"):
        subtitle += " ✓"

    likes = f"{tweet['likes']:,}"
    retweets = f"{tweet['retweets']:,}"
    replies = f"{tweet['replies']:,}"

    widgets = [
        {"textParagraph": {"text": tweet["text"]}},
    ]

    # Link card preview image (e.g. article thumbnail)
    card_data = tweet.get("card")
    if card_data and card_data.get("image"):
        widgets.append({
            "image": {
                "imageUrl": card_data["image"]["url"],
                "altText": card_data.get("title", ""),
                "onClick": {"openLink": {"url": card_data["url"]}},
            }
        })

    # Inline media photos
    for photo in tweet.get("media", {}).get("photos", [])[:4]:
        widgets.append({
            "image": {
                "imageUrl": photo["url"],
                "altText": "photo",
                "onClick": {"openLink": {"url": tweet["url"]}},
            }
        })

    widgets.append({
        "textParagraph": {"text": f"❤️ {likes}   🔁 {retweets}   💬 {replies}"}
    })

    return {
        "message": {
            "cardsV2": [{
                "cardId": f"tweet-{tweet['id']}",
                "card": {
                    "header": {
                        "title": author["name"],
                        "subtitle": subtitle,
                        "imageUrl": author["avatar_url"],
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

    user, tweet_id = m.group(1), m.group(2)
    logger.info("twitpic: fetching @%s/status/%s", user, tweet_id)

    try:
        tweet = _fetch_tweet(user, tweet_id)
        return _build_card(tweet)
    except requests.HTTPError as e:
        logger.warning("fxtwitter request failed: %s", e)
        return "couldn't fetch that tweet (private or deleted?)"
    except Exception:
        logger.exception("twitpic failed for @%s/%s", user, tweet_id)
        return "couldn't fetch that tweet"
