from __future__ import annotations

import binascii

import pytest

from stablevoy import KeyCheck, check_api_key, check_webhook_secret

RANDOM = "aB3dE5gH7jK9mN1pQ3sT5vW7yZ9bC1"


def with_checksum(prefix: str) -> str:
    """Built independently of the SDK: CRC-32 (binascii) written as 6 base62 characters, as the API does."""
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    n = binascii.crc32((prefix + RANDOM).encode())
    out = ""
    for _ in range(6):
        out = alphabet[n % 62] + out
        n //= 62
    return prefix + RANDOM + out


def test_accepts_checksummed_and_older_formats() -> None:
    assert check_api_key(with_checksum("svk_live_")) is KeyCheck.OK
    assert check_api_key(with_checksum("svk_test_")) is KeyCheck.OK
    assert check_webhook_secret(with_checksum("svwhsec_")) is KeyCheck.OK
    assert check_api_key("sk_live_Xy3-Zq") is KeyCheck.OK
    assert check_api_key("sk_test_Xy3-Zq") is KeyCheck.OK
    assert check_webhook_secret("whsec_abc") is KeyCheck.OK


def test_says_mistyped_for_a_broken_checksummed_key() -> None:
    key = with_checksum("svk_live_")
    assert check_api_key(key[:-1] + ("b" if key.endswith("a") else "a")) is KeyCheck.MISTYPED
    assert check_api_key(key[:-1]) is KeyCheck.MISTYPED
    assert check_api_key(key + "x") is KeyCheck.MISTYPED
    assert check_api_key("svk_live_" + "-" * 36) is KeyCheck.MISTYPED
    assert check_webhook_secret(with_checksum("svwhsec_")[:-2]) is KeyCheck.MISTYPED


@pytest.mark.parametrize("value", ["", "pk_live_abc", "svk_prod_abc", "Bearer sk_live_abc"])
def test_says_not_a_key_for_anything_else(value: str) -> None:
    assert check_api_key(value) is KeyCheck.NOT_A_KEY


def test_secret_and_key_are_not_interchangeable() -> None:
    assert check_webhook_secret("sk_live_abc") is KeyCheck.NOT_A_KEY
    assert check_api_key(with_checksum("svwhsec_")) is KeyCheck.NOT_A_KEY
