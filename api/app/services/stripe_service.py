"""Stripe billing integration service."""

from __future__ import annotations

from typing import Any

import stripe

from app.config import settings

# Configure Stripe API key
stripe.api_key = settings.stripe_secret_key

PRICE_IDS: dict[str, str] = {
    "pro": settings.stripe_pro_price_id,
    "business": settings.stripe_business_price_id,
}


class StripeService:
    """Service for Stripe billing operations."""

    @staticmethod
    async def create_customer(
        email: str, name: str | None = None
    ) -> str:
        """Create a Stripe customer.

        Args:
            email: Customer email address.
            name: Optional customer name.

        Returns:
            Stripe customer ID.
        """
        customer = stripe.Customer.create(
            email=email,
            name=name or "",
        )
        return str(customer.id)

    @staticmethod
    async def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe checkout session for subscription.

        Args:
            customer_id: Stripe customer ID.
            price_id: Stripe price ID.
            success_url: URL to redirect on success.
            cancel_url: URL to redirect on cancel.

        Returns:
            Checkout session URL.
        """
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return str(session.url)

    @staticmethod
    async def create_portal_session(
        customer_id: str, return_url: str
    ) -> str:
        """Create a Stripe customer portal session.

        Args:
            customer_id: Stripe customer ID.
            return_url: URL to return to after portal.

        Returns:
            Portal session URL.
        """
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return str(session.url)

    @staticmethod
    async def get_subscription(
        customer_id: str,
    ) -> Any:
        """Get active subscription for a customer.

        Args:
            customer_id: Stripe customer ID.

        Returns:
            Subscription object or None.
        """
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1,
        )
        if subscriptions.data:
            return subscriptions.data[0]
        return None

    @staticmethod
    async def record_usage(
        subscription_item_id: str, quantity: int
    ) -> None:
        """Record metered usage for overage billing.

        Args:
            subscription_item_id: Stripe subscription item ID.
            quantity: Usage quantity to record.
        """
        stripe.SubscriptionItem.create_usage_record(  # type: ignore[attr-defined]
            subscription_item_id,
            quantity=quantity,
            action="increment",
        )
