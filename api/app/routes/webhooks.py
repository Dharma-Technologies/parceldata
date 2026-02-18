"""Stripe webhook handler routes."""

from __future__ import annotations

from typing import Any

import stripe
import structlog
from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None),
) -> dict[str, bool]:
    """Handle Stripe webhook events.

    Processes subscription changes, payment events, etc.
    """
    payload = await request.body()

    if not settings.stripe_webhook_secret:
        logger.warning("stripe_webhook_secret not configured")
        raise HTTPException(
            status_code=503,
            detail="Webhook endpoint not configured",
        )

    try:
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            payload,
            stripe_signature or "",
            settings.stripe_webhook_secret,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Invalid payload"
        ) from exc
    except stripe.SignatureVerificationError as exc:
        raise HTTPException(
            status_code=400, detail="Invalid signature"
        ) from exc

    # Handle event types
    event_type: str = event.type
    event_data: Any = event.data.object

    if event_type == "checkout.session.completed":
        await _handle_checkout_complete(event_data)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_update(event_data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_cancel(event_data)
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(event_data)
    else:
        logger.info("unhandled_stripe_event", event_type=event_type)

    return {"received": True}


async def _handle_checkout_complete(session: Any) -> None:
    """Handle successful checkout — upgrade account tier."""
    customer_id = session.get("customer") if hasattr(session, "get") else None
    logger.info(
        "checkout_complete",
        customer_id=customer_id,
    )
    # TODO: Find account by stripe_customer_id and update tier


async def _handle_subscription_update(subscription: Any) -> None:
    """Handle subscription changes."""
    logger.info(
        "subscription_updated",
        subscription_id=getattr(subscription, "id", None),
    )
    # TODO: Update account tier based on subscription


async def _handle_subscription_cancel(subscription: Any) -> None:
    """Handle subscription cancellation — downgrade to free."""
    logger.info(
        "subscription_cancelled",
        subscription_id=getattr(subscription, "id", None),
    )
    # TODO: Downgrade account to free tier


async def _handle_payment_failed(invoice: Any) -> None:
    """Handle failed payment — may need to restrict access."""
    logger.info(
        "payment_failed",
        invoice_id=getattr(invoice, "id", None),
    )
    # TODO: Mark account as payment_failed, send notification
