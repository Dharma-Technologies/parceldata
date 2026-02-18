"""API key management and authentication service."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.redis import get_redis
from app.models.api_key import Account, APIKey, TierEnum


class AuthService:
    """Service for managing accounts and API keys."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_account(
        self,
        email: str,
        name: str | None = None,
        company: str | None = None,
    ) -> Account:
        """Create a new account.

        Args:
            email: Account email address.
            name: Optional display name.
            company: Optional company name.

        Returns:
            Created Account instance.
        """
        account = Account(
            email=email.lower(),
            name=name,
            company=company,
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def get_account_by_email(self, email: str) -> Account | None:
        """Look up an account by email.

        Args:
            email: Email address to search for.

        Returns:
            Account if found, else None.
        """
        stmt = select(Account).where(Account.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_api_key(
        self,
        account_id: int,
        name: str | None = None,
        tier: TierEnum = TierEnum.FREE,
        scopes: list[str] | None = None,
    ) -> tuple[str, APIKey]:
        """Create a new API key for an account.

        Args:
            account_id: Owning account ID.
            name: Optional key name.
            tier: Tier level for this key.
            scopes: Permission scopes (default: ["read"]).

        Returns:
            Tuple of (raw_key, APIKey). raw_key is only shown once.
        """
        key_id = secrets.token_urlsafe(24)
        prefix = "pk_live_" if tier != TierEnum.FREE else "pk_test_"
        raw_key = f"{prefix}{key_id}"

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = APIKey(
            key_hash=key_hash,
            key_prefix=prefix,
            account_id=account_id,
            name=name,
            tier=tier,
            scopes=scopes or ["read"],
        )

        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        # Cache key info in Redis for fast lookup
        try:
            redis = await get_redis()
            await redis.hset(
                f"apikey:{key_hash}",
                mapping={
                    "id": str(api_key.id),
                    "account_id": str(account_id),
                    "tier": tier.value,
                    "scopes": ",".join(api_key.scopes),  # type: ignore[arg-type]
                },
            )
            await redis.expire(f"apikey:{key_hash}", 86400)
        except Exception:
            pass  # Redis unavailable; DB is source of truth

        return raw_key, api_key

    async def validate_key(self, raw_key: str) -> dict[str, object] | None:
        """Validate an API key and return key info.

        Args:
            raw_key: The raw API key string.

        Returns:
            Dict with id, account_id, tier, scopes — or None if invalid.
        """
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Check Redis cache first
        try:
            redis = await get_redis()
            cached = await redis.hgetall(f"apikey:{key_hash}")

            if cached:
                return {
                    "id": int(cached["id"]),
                    "account_id": int(cached["account_id"]),
                    "tier": cached["tier"],
                    "scopes": cached["scopes"].split(","),
                }
        except Exception:
            pass  # Redis unavailable; fall through to DB

        # Check database
        stmt = select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # Update last used
        api_key.last_used = datetime.utcnow()
        await self.db.commit()

        # Cache in Redis
        key_info_mapping: dict[str | bytes, bytes | float | int | str] = {
            "id": str(api_key.id),
            "account_id": str(api_key.account_id),
            "tier": api_key.tier.value,
            "scopes": ",".join(api_key.scopes),  # type: ignore[arg-type]
        }
        try:
            redis = await get_redis()
            await redis.hset(f"apikey:{key_hash}", mapping=key_info_mapping)
            await redis.expire(f"apikey:{key_hash}", 86400)
        except Exception:
            pass

        return {
            "id": api_key.id,
            "account_id": api_key.account_id,
            "tier": api_key.tier.value,
            "scopes": api_key.scopes,
        }

    async def revoke_key(self, key_id: int) -> bool:
        """Revoke an API key.

        Args:
            key_id: The API key's database ID.

        Returns:
            True if revoked, False if not found.
        """
        stmt = select(APIKey).where(APIKey.id == key_id)
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        api_key.is_active = False
        await self.db.commit()

        # Invalidate Redis cache
        try:
            redis = await get_redis()
            await redis.delete(f"apikey:{api_key.key_hash}")
        except Exception:
            pass

        return True

    async def list_keys(self, account_id: int) -> list[APIKey]:
        """List all API keys for an account.

        Args:
            account_id: The account ID.

        Returns:
            List of APIKey instances (active ones).
        """
        stmt = (
            select(APIKey)
            .where(
                APIKey.account_id == account_id,
                APIKey.is_active.is_(True),
            )
            .order_by(APIKey.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
