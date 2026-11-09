"""Stablevoy key formats (svk_live_ / svk_test_ and svwhsec_ with a checksum, older sk_live_ / sk_test_ / whsec_).

The checksum is CRC-32 of prefix and random part written as 6 base62 characters, so a typo or a cut copy shows without any
request. Keys and secrets made before the checksummed format keep working and are recognised by their prefix.
"""

from __future__ import annotations

import re
import zlib

from stablevoy.keys.key_check import KeyCheck

_BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BODY = re.compile(r"[0-9A-Za-z]{36}")
_API_KEY_PREFIXES = ("svk_live_", "svk_test_")
_WEBHOOK_SECRET_PREFIX = "svwhsec_"  # noqa: S105 - a public prefix, not a secret


def check_api_key(value: str) -> KeyCheck:
    for prefix in _API_KEY_PREFIXES:
        if value.startswith(prefix):
            return KeyCheck.OK if _has_valid_checksum(prefix, value) else KeyCheck.MISTYPED
    return KeyCheck.OK if value.startswith(("sk_live_", "sk_test_")) else KeyCheck.NOT_A_KEY


def check_webhook_secret(value: str) -> KeyCheck:
    if value.startswith(_WEBHOOK_SECRET_PREFIX):
        return KeyCheck.OK if _has_valid_checksum(_WEBHOOK_SECRET_PREFIX, value) else KeyCheck.MISTYPED
    return KeyCheck.OK if value.startswith("whsec_") else KeyCheck.NOT_A_KEY


def _has_valid_checksum(prefix: str, value: str) -> bool:
    body = value[len(prefix) :]
    if _BODY.fullmatch(body) is None:
        return False
    n = zlib.crc32((prefix + body[:30]).encode("ascii"))
    checksum = ""
    for _ in range(6):
        checksum = _BASE62[n % 62] + checksum
        n //= 62
    return body[30:] == checksum
