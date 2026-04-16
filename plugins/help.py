"""
help plugin — responds to "help" with a list of available commands.
Required by Google Workspace Marketplace review guidelines.
"""


HELP_TEXT = """*nBot* — a bot for your friend group chat.

*Commands*
• *ping* — check if nBot is alive
• *roll NdN* — roll dice (e.g. roll 2d6, roll 1d20)
• *frink <quote>* — find a Simpsons scene matching a quote
• *morb <quote>* — find a Futurama scene matching a quote
• paste any Twitter/X link — get a preview card of the tweet"""


def handle(text: str, sender: dict, space: str) -> str | None:
    if text.lower().strip() == "help":
        return HELP_TEXT
    return None
