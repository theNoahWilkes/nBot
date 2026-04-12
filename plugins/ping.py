"""
Ping plugin — smoke test to verify the bot is alive.
Trigger: message is exactly "ping" (case-insensitive)
Response: "pong"
"""


def handle(text: str, sender: dict, space: str) -> str | None:
    if text.lower() == "ping":
        return "pong"
    return None
