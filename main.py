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


def chat_reply(text: str) -> dict:
    return {
        "hostAppDataAction": {
            "chatDataAction": {
                "createMessageAction": {
                    "message": {"text": text}
                }
            }
        }
    }


def build_reply(response) -> dict:
    if isinstance(response, dict) and "message" in response:
        return {
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": response["message"]
                    }
                }
            }
        }
    return chat_reply(str(response))


@app.post("/webhook")
async def webhook(request: Request):
    verify_request(request)

    event = await request.json()
    chat = event.get("chat", {})
    logger.info("Received event keys: %s", list(chat.keys()))

    if "addedToSpacePayload" in chat:
        space = chat.get("addedToSpacePayload", {}).get("space", {}).get("name", "unknown space")
        logger.info("Bot added to %s", space)
        return chat_reply("hey, I'm nBot. say 'ping' or 'roll 2d6'.")

    if "removedFromSpacePayload" in chat:
        logger.info("Bot removed from space")
        return {}

    if "messagePayload" in chat:
        payload = chat["messagePayload"]
        message = payload.get("message", {})
        text = message.get("text", "").strip()
        sender = message.get("sender", {})
        space = payload.get("space", {}).get("name", "")

        response = dispatch(text, sender, space)
        if response is not None:
            return build_reply(response)
        return {}

    # Unknown event shape — log and acknowledge
    logger.warning("Unrecognized event shape: %s", list(event.keys()))
    return {}
