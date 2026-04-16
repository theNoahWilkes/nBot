import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException

load_dotenv()
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dispatcher import dispatch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BOT_PUBLIC_URL = os.getenv("BOT_PUBLIC_URL", "").rstrip("/")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Reused across requests — caches Google's public keys after the first fetch.
_google_transport = google_requests.Request()


def verify_request(request: Request) -> None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = auth_header.removeprefix("Bearer ")

    if not BOT_PUBLIC_URL:
        logger.error("BOT_PUBLIC_URL is not set — cannot verify request audience")
        raise HTTPException(status_code=500, detail="Bot misconfigured")

    try:
        id_token.verify_oauth2_token(
            token,
            _google_transport,
            audience=f"{BOT_PUBLIC_URL}/webhook",
        )
    except Exception as e:
        logger.warning("Request verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Unauthorized")


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


@app.get("/")
async def index():
    from fastapi.responses import Response
    return Response(status_code=204)


@app.post("/webhook")
async def webhook(request: Request):
    verify_request(request)

    event = await request.json()
    chat = event.get("chat", {})
    logger.info("Received event keys: %s", list(chat.keys()))

    if "addedToSpacePayload" in chat:
        space = chat.get("addedToSpacePayload", {}).get("space", {}).get("name", "unknown space")
        logger.info("Bot added to %s", space)
        return chat_reply("👋 Hey, I'm *nBot* — a bot for your friend group chat. I can roll dice, find Simpsons and Futurama scenes, and preview tweets. Type *help* to see all commands.")

    if "removedFromSpacePayload" in chat:
        logger.info("Bot removed from space")
        return {}

    if "messagePayload" in chat:
        payload = chat["messagePayload"]
        message = payload.get("message", {})
        text = message.get("argumentText", message.get("text", "")).strip()
        sender = message.get("sender", {})
        space = payload.get("space", {}).get("name", "")

        response = dispatch(text, sender, space)
        if response is not None:
            return build_reply(response)
        return {}

    # Unknown event shape — log and acknowledge
    logger.warning("Unrecognized event shape: %s", list(event.keys()))
    return {}
