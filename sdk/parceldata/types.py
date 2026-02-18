"""Type definitions for the ParcelData SDK."""

from __future__ import annotations

from typing import Literal

DetailTier = Literal["micro", "standard", "extended", "full"]
SortOrder = Literal["asc", "desc"]
Confidence = Literal["low", "medium", "high"]
