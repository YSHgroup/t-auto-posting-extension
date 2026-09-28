from __future__ import annotations

import hashlib
import uuid

LEGACY_INSTALLATION_ID = "legacy"


def installation_key(installation_id: str) -> int:
    """Return a stable positive integer key for per-installation singleton rows."""
    if installation_id == LEGACY_INSTALLATION_ID:
        return 1
    digest = hashlib.sha256(installation_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFFFFFFFFFF or 1


def normalize_installation_id(value: str) -> str:
    return str(uuid.UUID(value))


def installation_key_for_session(session) -> int:
    return installation_key(session.info.get("installation_id", LEGACY_INSTALLATION_ID))
