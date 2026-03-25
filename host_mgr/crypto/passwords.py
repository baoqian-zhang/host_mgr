from __future__ import annotations

import secrets
import string


def generate_root_password(length: int = 24) -> str:
    """
    Generate a random password suitable for root rotation.

    Avoid ambiguous characters and whitespace to reduce operational friction.
    """

    if length < 16:
        raise ValueError("length must be >= 16")

    alphabet = (
        string.ascii_letters
        + string.digits
        + "!@#$%^&*()-_=+[]{};:,.?"
    )

    # Ensure at least one from common categories
    picks = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()-_=+[]{};:,.?"),
    ]
    picks += [secrets.choice(alphabet) for _ in range(length - len(picks))]
    secrets.SystemRandom().shuffle(picks)
    return "".join(picks)

