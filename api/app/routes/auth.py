"""Authentication and API key management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.api_key import Account, TierEnum
from app.services.auth_service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


# ── Request / Response schemas ────────────────────────────────


class SignupRequest(BaseModel):
    """Request body for account signup."""

    email: EmailStr
    name: str | None = None
    company: str | None = None


class SignupResponse(BaseModel):
    """Response for successful signup."""

    account_id: int
    api_key: str
    tier: str
    message: str


class CreateKeyRequest(BaseModel):
    """Request body for creating an additional API key."""

    name: str | None = None
    scopes: list[str] = ["read"]


class CreateKeyResponse(BaseModel):
    """Response for key creation."""

    api_key: str
    key_id: int
    tier: str
    scopes: list[str]


class KeyInfo(BaseModel):
    """Public info about an API key (no secret)."""

    id: int
    name: str | None
    key_prefix: str
    tier: str
    scopes: list[object]
    is_active: bool
    last_used: str | None


# ── Routes ────────────────────────────────────────────────────


@router.post("/signup", response_model=SignupResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
) -> SignupResponse:
    """Create a new account and get an API key.

    The API key is only shown once — save it securely.
    """
    service = AuthService(db)

    # Check if email already exists
    stmt = select(Account).where(Account.email == request.email.lower())
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists",
        )

    # Create account
    account = await service.create_account(
        email=request.email,
        name=request.name,
        company=request.company,
    )

    # Create API key
    raw_key, _api_key = await service.create_api_key(
        account_id=account.id,
        name="Default Key",
        tier=TierEnum.FREE,
    )

    return SignupResponse(
        account_id=account.id,
        api_key=raw_key,
        tier="free",
        message="Save your API key — it will not be shown again.",
    )


@router.post("/keys", response_model=CreateKeyResponse)
async def create_key(
    body: CreateKeyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CreateKeyResponse:
    """Create an additional API key for your account.

    Requires authentication with an existing key that has 'admin' scope.
    """
    key_info = getattr(request.state, "key_info", None)
    if not key_info:
        raise HTTPException(status_code=401, detail="Authentication required")

    scopes = key_info.get("scopes", [])
    if "admin" not in scopes:
        raise HTTPException(
            status_code=403,
            detail="Admin scope required to create keys",
        )

    account_id = key_info.get("account_id")
    tier_str = key_info.get("tier", "free")
    tier = TierEnum(tier_str)

    service = AuthService(db)
    raw_key, api_key = await service.create_api_key(
        account_id=account_id,
        name=body.name,
        tier=tier,
        scopes=body.scopes,
    )

    return CreateKeyResponse(
        api_key=raw_key,
        key_id=api_key.id,
        tier=tier.value,
        scopes=body.scopes,
    )


@router.get("/keys")
async def list_keys(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[KeyInfo]:
    """List all API keys for your account.

    Does not show the actual key values.
    """
    key_info = getattr(request.state, "key_info", None)
    if not key_info:
        raise HTTPException(status_code=401, detail="Authentication required")

    account_id = key_info.get("account_id")
    service = AuthService(db)
    keys = await service.list_keys(account_id)

    return [
        KeyInfo(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            tier=k.tier.value,
            scopes=k.scopes,
            is_active=k.is_active,
            last_used=k.last_used.isoformat() if k.last_used else None,
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_key(
    key_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoke an API key.

    The key will immediately stop working.
    """
    key_info = getattr(request.state, "key_info", None)
    if not key_info:
        raise HTTPException(status_code=401, detail="Authentication required")

    service = AuthService(db)
    success = await service.revoke_key(key_id)

    if not success:
        raise HTTPException(status_code=404, detail="Key not found")

    return {"message": "Key revoked successfully"}
