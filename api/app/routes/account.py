"""Account and usage information routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.usage_service import UsageService

router = APIRouter(prefix="/v1/account", tags=["Account"])

# Monthly quota limits by tier
MONTHLY_LIMITS: dict[str, int] = {
    "free": 3000,
    "pro": 50000,
    "business": 500000,
    "enterprise": 10000000,
}


# ── Response schemas ──────────────────────────────────────────


class UsageResponse(BaseModel):
    """API usage summary response."""

    period: dict[str, str]
    queries: dict[str, int]
    breakdown: dict[str, int]
    limits: dict[str, object]
    remaining: int


class BillingResponse(BaseModel):
    """Billing information response."""

    tier: str
    status: str
    current_period: dict[str, str]
    payment_method: dict[str, str] | None
    invoices: list[dict[str, object]]


# ── Routes ────────────────────────────────────────────────────


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    request: Request,
    start_date: date | None = Query(None, description="Period start date"),
    end_date: date | None = Query(None, description="Period end date"),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    """Get your API usage for the current billing period."""
    key_info = getattr(request.state, "key_info", None)
    if not key_info:
        raise HTTPException(status_code=401, detail="Authentication required")

    account_id = key_info.get("account_id")
    if not account_id:
        raise HTTPException(
            status_code=401, detail="Account ID not found in key info"
        )

    tier = key_info.get("tier", "free")

    service = UsageService(db)
    usage = await service.get_usage_summary(account_id, start_date, end_date)

    monthly_limit = MONTHLY_LIMITS.get(tier, 3000)
    total_queries: int = usage["queries"]["total"]

    return UsageResponse(
        period=usage["period"],
        queries=usage["queries"],
        breakdown=usage["breakdown"],
        limits={
            "monthly": monthly_limit,
            "tier": tier,
        },
        remaining=max(0, monthly_limit - total_queries),
    )


@router.get("/billing", response_model=BillingResponse)
async def get_billing(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BillingResponse:
    """Get your billing information and invoices."""
    key_info = getattr(request.state, "key_info", None)
    if not key_info:
        raise HTTPException(status_code=401, detail="Authentication required")

    tier = key_info.get("tier", "free")

    return BillingResponse(
        tier=tier,
        status="active",
        current_period={
            "start": date.today().replace(day=1).isoformat(),
            "end": date.today().isoformat(),
        },
        payment_method=None,
        invoices=[],
    )


@router.post("/upgrade")
async def upgrade_tier(
    request: Request,
    target_tier: str = Query(..., description="Target tier: pro, business"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Upgrade your account to a higher tier.

    Redirects to Stripe checkout for payment.
    """
    key_info = getattr(request.state, "key_info", None)
    if not key_info:
        raise HTTPException(status_code=401, detail="Authentication required")

    if target_tier not in ("pro", "business", "enterprise"):
        raise HTTPException(
            status_code=400, detail="Invalid target tier"
        )

    raise HTTPException(
        status_code=501,
        detail="Not implemented — use Stripe checkout at parceldata.ai/pricing",
    )
