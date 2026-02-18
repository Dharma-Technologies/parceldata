"""Tests for StripeService (P10-04 S7) and Stripe config (S11)."""

from __future__ import annotations

import inspect

from app.config import settings
from app.services.stripe_service import PRICE_IDS, StripeService


class TestStripeService:
    """StripeService class and methods."""

    def test_class_exists(self) -> None:
        assert StripeService is not None

    def test_create_customer_method(self) -> None:
        assert hasattr(StripeService, "create_customer")
        assert inspect.iscoroutinefunction(StripeService.create_customer)

    def test_create_checkout_session_method(self) -> None:
        assert hasattr(StripeService, "create_checkout_session")
        assert inspect.iscoroutinefunction(
            StripeService.create_checkout_session
        )

    def test_create_portal_session_method(self) -> None:
        assert hasattr(StripeService, "create_portal_session")
        assert inspect.iscoroutinefunction(
            StripeService.create_portal_session
        )

    def test_get_subscription_method(self) -> None:
        assert hasattr(StripeService, "get_subscription")
        assert inspect.iscoroutinefunction(StripeService.get_subscription)

    def test_record_usage_method(self) -> None:
        assert hasattr(StripeService, "record_usage")
        assert inspect.iscoroutinefunction(StripeService.record_usage)


class TestPriceIds:
    """PRICE_IDS configuration."""

    def test_pro_price_id(self) -> None:
        assert "pro" in PRICE_IDS

    def test_business_price_id(self) -> None:
        assert "business" in PRICE_IDS


class TestStripeConfig:
    """Stripe settings in config (S11)."""

    def test_stripe_secret_key_exists(self) -> None:
        assert hasattr(settings, "stripe_secret_key")

    def test_stripe_publishable_key_exists(self) -> None:
        assert hasattr(settings, "stripe_publishable_key")

    def test_stripe_webhook_secret_exists(self) -> None:
        assert hasattr(settings, "stripe_webhook_secret")

    def test_stripe_pro_price_id_exists(self) -> None:
        assert hasattr(settings, "stripe_pro_price_id")

    def test_stripe_business_price_id_exists(self) -> None:
        assert hasattr(settings, "stripe_business_price_id")

    def test_defaults_are_empty(self) -> None:
        # Default values are empty strings (not set yet)
        assert settings.stripe_secret_key == ""
        assert settings.stripe_webhook_secret == ""
