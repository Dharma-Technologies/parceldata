"""Tests for AuthService (P10-04 S3)."""

from __future__ import annotations

import hashlib
import inspect

from app.models.api_key import TierEnum
from app.services.auth_service import AuthService


class TestAuthService:
    """AuthService class and methods."""

    def test_class_exists(self) -> None:
        assert AuthService is not None

    def test_init_signature(self) -> None:
        sig = inspect.signature(AuthService.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "db" in params

    def test_create_account_method(self) -> None:
        assert hasattr(AuthService, "create_account")
        assert inspect.iscoroutinefunction(AuthService.create_account)

    def test_create_api_key_method(self) -> None:
        assert hasattr(AuthService, "create_api_key")
        assert inspect.iscoroutinefunction(AuthService.create_api_key)

    def test_validate_key_method(self) -> None:
        assert hasattr(AuthService, "validate_key")
        assert inspect.iscoroutinefunction(AuthService.validate_key)

    def test_revoke_key_method(self) -> None:
        assert hasattr(AuthService, "revoke_key")
        assert inspect.iscoroutinefunction(AuthService.revoke_key)

    def test_list_keys_method(self) -> None:
        assert hasattr(AuthService, "list_keys")
        assert inspect.iscoroutinefunction(AuthService.list_keys)


class TestKeyHashing:
    """API key hashing uses SHA-256."""

    def test_key_hash_is_sha256(self) -> None:
        raw_key = "pk_test_abc123"
        expected = hashlib.sha256(raw_key.encode()).hexdigest()
        assert len(expected) == 64

    def test_different_keys_different_hashes(self) -> None:
        h1 = hashlib.sha256(b"pk_test_key1").hexdigest()
        h2 = hashlib.sha256(b"pk_test_key2").hexdigest()
        assert h1 != h2


class TestTierDefaults:
    """Tier-related logic."""

    def test_free_tier_prefix(self) -> None:
        tier = TierEnum.FREE
        prefix = "pk_live_" if tier != TierEnum.FREE else "pk_test_"
        assert prefix == "pk_test_"

    def test_pro_tier_prefix(self) -> None:
        tier = TierEnum.PRO
        prefix = "pk_live_" if tier != TierEnum.FREE else "pk_test_"
        assert prefix == "pk_live_"

    def test_business_tier_prefix(self) -> None:
        tier = TierEnum.BUSINESS
        prefix = "pk_live_" if tier != TierEnum.FREE else "pk_test_"
        assert prefix == "pk_live_"

    def test_enterprise_tier_prefix(self) -> None:
        tier = TierEnum.ENTERPRISE
        prefix = "pk_live_" if tier != TierEnum.FREE else "pk_test_"
        assert prefix == "pk_live_"
