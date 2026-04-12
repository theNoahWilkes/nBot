import logging
from fastapi import FastAPI, Request, HTTPException
from dispatcher import dispatch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()


def verify_request(request: Request) -> None:
    """
    TODO: validate that the incoming request is actually from Google Chat.
    Google sends a signed Bearer JWT in the Authorization header.
    For now this is a no-op stub — do NOT leave this open in production.
    See: https://developers.google.com/chat/api/guides/message-formats/events#verifying_requests
    """
    pass


@app.post("/webhook")
async def webhook(request: Request):
    verify_request(request)

    event = await request.json()
    event_type = event.get("type")
    logger.info("Received event: type=%s", event_type)

    if event_type == "ADDED_TO_SPACE":
        space = event.get("space", {}).get("name", "unknown space")
        logger.info("Bot added to %s", space)
        return {"text": "hey, I'm nBot. say 'ping' or 'roll 2d6'."}

    if event_type == "REMOVED_FROM_SPACE":
        logger.info("Bot removed from space")
        return {}

    if event_type == "MESSAGE":
        message = event.get("message", {})
        text = message.get("text", "").strip()
        sender = message.get("sender", {})
        space = event.get("space", {}).get("name", "")

        response = dispatch(text, sender, space)
        if response is not None:
            return {"text": response}
        return {}

    # Unknown event type — acknowledge with empty 200
    return {}
