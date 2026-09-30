from __future__ import annotations

import hashlib
import re

LEGACY_INSTALLATION_ID = "legacy"


def account_key(telegram_username: str) -> int:
    """Return a stable positive integer key for per-username singleton rows."""
    if telegram_username == LEGACY_INSTALLATION_ID:
        return 1
    digest = hashlib.sha256(telegram_username.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFFFFFFFFFF or 1


def normalize_telegram_username(value: str) -> str:
    username = value.strip().removeprefix("@").lower()
    if not re.fullmatch(r"[a-z0-9_]{5,32}", username):
        raise ValueError("Enter a valid Telegram username (5-32 letters, digits, or underscores)")
    return username


def account_key_for_session(session) -> int:
    return account_key(session.info.get("telegram_username", LEGACY_INSTALLATION_ID))
