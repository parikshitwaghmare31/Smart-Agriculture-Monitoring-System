"""
Unit tests for authentication logic: password hashing and JWT tokens.
These don't require a database connection.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hash_and_verify_roundtrip():
    plain = "correct-horse-battery-staple"
    hashed = hash_password(plain)
    assert hashed != plain  # never store plaintext
    assert verify_password(plain, hashed) is True


def test_wrong_password_fails_verification():
    hashed = hash_password("the-real-password")
    assert verify_password("a-wrong-guess", hashed) is False


def test_same_password_produces_different_hashes():
    """bcrypt salts each hash uniquely, so two hashes of the same password
    should never match byte-for-byte even though both verify correctly."""
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2
    assert verify_password("same-password", h1) is True
    assert verify_password("same-password", h2) is True


def test_access_token_roundtrip():
    token = create_access_token(subject_email="farmer@example.com", role="farmer")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "farmer@example.com"
    assert payload["role"] == "farmer"


def test_tampered_token_is_rejected():
    token = create_access_token(subject_email="admin@example.com", role="admin")
    tampered = token[:-2] + "xx"  # corrupt the signature
    assert decode_access_token(tampered) is None


def test_admin_role_is_preserved_in_token():
    token = create_access_token(subject_email="admin@example.com", role="admin")
    payload = decode_access_token(token)
    assert payload["role"] == "admin"
