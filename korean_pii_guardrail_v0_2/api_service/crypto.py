"""Operator-key encryption helpers for optional local raw-log retention."""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


ENCRYPTION_VERSION = "aesgcm-pbkdf2-sha256-v1"
KDF_ITERATIONS = 390_000
SALT_BYTES = 16
NONCE_BYTES = 12
KEY_BYTES = 32


class DecryptionError(ValueError):
    """Raised when an encrypted raw log cannot be decrypted with the supplied key."""


@dataclass(frozen=True)
class EncryptedRawText:
    envelope: dict[str, Any]
    key_hint: str | None


def encrypt_raw_text(
    raw_text: str,
    *,
    operator_key: str,
    request_id: str,
    key_hint: str | None = None,
) -> EncryptedRawText:
    _validate_operator_key(operator_key)
    salt = secrets.token_bytes(SALT_BYTES)
    nonce = secrets.token_bytes(NONCE_BYTES)
    key = _derive_key(operator_key, salt=salt)
    ciphertext = AESGCM(key).encrypt(
        nonce,
        raw_text.encode("utf-8"),
        _associated_data(request_id),
    )
    return EncryptedRawText(
        envelope={
            "version": ENCRYPTION_VERSION,
            "kdf": "pbkdf2-sha256",
            "iterations": KDF_ITERATIONS,
            "salt_b64": _b64encode(salt),
            "nonce_b64": _b64encode(nonce),
            "ciphertext_b64": _b64encode(ciphertext),
            "aad": "request_id",
        },
        key_hint=_sanitize_key_hint(key_hint),
    )


def decrypt_raw_text(
    envelope: dict[str, Any],
    *,
    operator_key: str,
    request_id: str,
) -> str:
    _validate_operator_key(operator_key)
    if envelope.get("version") != ENCRYPTION_VERSION:
        raise DecryptionError("지원하지 않는 암호화 버전입니다.")
    try:
        salt = _b64decode(str(envelope["salt_b64"]))
        nonce = _b64decode(str(envelope["nonce_b64"]))
        ciphertext = _b64decode(str(envelope["ciphertext_b64"]))
        iterations = int(envelope.get("iterations", KDF_ITERATIONS))
    except (KeyError, TypeError, ValueError) as exc:
        raise DecryptionError("암호화 로그 형식이 올바르지 않습니다.") from exc
    key = _derive_key(operator_key, salt=salt, iterations=iterations)
    try:
        plaintext = AESGCM(key).decrypt(
            nonce,
            ciphertext,
            _associated_data(request_id),
        )
    except InvalidTag as exc:
        raise DecryptionError("복호화 키가 맞지 않습니다.") from exc
    return plaintext.decode("utf-8")


def _derive_key(
    operator_key: str,
    *,
    salt: bytes,
    iterations: int = KDF_ITERATIONS,
) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_BYTES,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(operator_key.encode("utf-8"))


def _associated_data(request_id: str) -> bytes:
    return f"korean-pii-guardrail-log:{request_id}".encode("utf-8")


def _validate_operator_key(operator_key: str) -> None:
    if not operator_key or len(operator_key.strip()) < 8:
        raise ValueError("암호화/복호화 키는 8자 이상이어야 합니다.")


def _sanitize_key_hint(key_hint: str | None) -> str | None:
    if key_hint is None:
        return None
    normalized = key_hint.strip()
    if not normalized:
        return None
    return normalized[:80]


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))
