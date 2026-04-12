"""
Dice roller plugin.
Trigger: "roll NdN" (case-insensitive), e.g. "roll 2d6", "roll 1d20"
Response: individual roll results and total.
"""

import random
import re

PATTERN = re.compile(r"^roll\s+(\d+)d(\d+)$", re.IGNORECASE)

MAX_DICE = 100
MAX_SIDES = 1000


def handle(text: str, sender: dict, space: str) -> str | None:
    match = PATTERN.match(text.strip())
    if not match:
        return None

    num_dice = int(match.group(1))
    num_sides = int(match.group(2))

    if num_dice < 1 or num_dice > MAX_DICE:
        return f"I can roll between 1 and {MAX_DICE} dice."
    if num_sides < 2 or num_sides > MAX_SIDES:
        return f"Dice must have between 2 and {MAX_SIDES} sides."

    rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(rolls)

    if num_dice == 1:
        return f"🎲 {total}"

    roll_str = ", ".join(str(r) for r in rolls)
    return f"🎲 [{roll_str}] = {total}"
