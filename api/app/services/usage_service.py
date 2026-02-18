"""Usage tracking and quota management service."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import func

from app.database.redis import get_redis
from app.models.api_key import APIKey
from app.models.usage import UsageEvent, UsageRecord

# Query cost weights by endpoint type
QUERY_COSTS: dict[str, int] = {
    "property_lookup": 1,
    "property_lookup_full": 2,
    "property_search": 1,
    "comparables": 3,
    "market_trends": 5,
    "batch": 1,
}

# Daily quota limits by tier
DAILY_LIMITS: dict[str, int] = {
    "free": 100,
    "pro": 10000,
    "business": 500000,
    "enterprise": 10000000,
}


class UsageService:
    """Service for tracking API usage and checking quotas."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        query_count: int = 1,
    ) -> None:
        """Record an API usage event.

        Args:
            api_key_id: The API key used.
            endpoint: Request path.
            method: HTTP method.
            status_code: Response status code.
            response_time_ms: Response time in milliseconds.
            query_count: Number of queries (for batch endpoints).
        """
        # Create event record
        event = UsageEvent(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            query_count=query_count,
            status_code=status_code,
            response_time_ms=response_time_ms,
        )
        self.db.add(event)

        # Update daily aggregate
        await self._update_daily_aggregate(api_key_id, endpoint, query_count)

        await self.db.commit()

        # Increment Redis counter for fast quota checks
        try:
            redis = await get_redis()
            today = date.today().isoformat()
            usage_key = f"usage:{api_key_id}:{today}"
            await redis.incrby(usage_key, query_count)
            await redis.expire(usage_key, 172800)  # 48h TTL
        except Exception:
            pass  # Redis unavailable; DB is source of truth

    async def _update_daily_aggregate(
        self,
        api_key_id: int,
        endpoint: str,
        query_count: int,
    ) -> None:
        """Update daily usage aggregate.

        Args:
            api_key_id: The API key used.
            endpoint: Request path.
            query_count: Number of queries.
        """
        today = date.today()

        # Get or create daily record
        stmt = select(UsageRecord).where(
            UsageRecord.api_key_id == api_key_id,
            UsageRecord.usage_date == today,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            # Get account_id from key
            key_stmt = select(APIKey.account_id).where(APIKey.id == api_key_id)
            key_result = await self.db.execute(key_stmt)
            account_id = key_result.scalar_one()

            record = UsageRecord(
                api_key_id=api_key_id,
                account_id=account_id,
                usage_date=today,
            )
            self.db.add(record)

        # Update counts
        record.queries_count += query_count
        cost = QUERY_COSTS.get(endpoint, 1)
        record.queries_billable += query_count * cost

        # Update endpoint-specific counts
        if "property" in endpoint and "search" not in endpoint:
            record.property_lookups += query_count
        elif "search" in endpoint:
            record.property_searches += query_count
        elif "comparable" in endpoint:
            record.comparables_requests += query_count
        elif "batch" in endpoint:
            record.batch_requests += query_count

    async def get_usage_summary(
        self,
        account_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get usage summary for an account.

        Args:
            account_id: The account ID.
            start_date: Start of period (default: first of month).
            end_date: End of period (default: today).

        Returns:
            Dict with period, queries, and breakdown.
        """
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        stmt = select(
            func.coalesce(func.sum(UsageRecord.queries_count), 0).label(
                "total_queries"
            ),
            func.coalesce(func.sum(UsageRecord.queries_billable), 0).label(
                "billable_queries"
            ),
            func.coalesce(func.sum(UsageRecord.property_lookups), 0).label(
                "property_lookups"
            ),
            func.coalesce(func.sum(UsageRecord.property_searches), 0).label(
                "property_searches"
            ),
            func.coalesce(
                func.sum(UsageRecord.comparables_requests), 0
            ).label("comparables"),
        ).where(
            UsageRecord.account_id == account_id,
            UsageRecord.usage_date >= start_date,
            UsageRecord.usage_date <= end_date,
        )

        result = await self.db.execute(stmt)
        row = result.one()

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "queries": {
                "total": row.total_queries,
                "billable": row.billable_queries,
            },
            "breakdown": {
                "property_lookups": row.property_lookups,
                "property_searches": row.property_searches,
                "comparables": row.comparables,
            },
        }

    async def check_quota(
        self, api_key_id: int, tier: str
    ) -> tuple[bool, int, int]:
        """Check if key has remaining quota.

        Args:
            api_key_id: The API key ID.
            tier: The tier level string.

        Returns:
            Tuple of (has_quota, used, limit).
        """
        limit = DAILY_LIMITS.get(tier, 100)

        today = date.today()

        # Try Redis first for speed
        try:
            redis = await get_redis()
            today_str = today.isoformat()
            usage_key = f"usage:{api_key_id}:{today_str}"
            used = int(await redis.get(usage_key) or 0)
            return (used < limit, used, limit)
        except Exception:
            pass

        # Fall back to DB
        stmt = select(UsageRecord.queries_count).where(
            UsageRecord.api_key_id == api_key_id,
            UsageRecord.usage_date == today,
        )
        result = await self.db.execute(stmt)
        used = result.scalar_one_or_none() or 0
        return (used < limit, used, limit)
