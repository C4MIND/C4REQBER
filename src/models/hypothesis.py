"""Hypothesis model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import GUID, Base


if TYPE_CHECKING:
    from src.models.discovery import Discovery


class Hypothesis(Base):
    """A generated hypothesis."""

    __tablename__ = "hypotheses"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4
    )
    discovery_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("discoveries.id", ondelete="CASCADE"),
        nullable=False
    )
    hypothesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Stored as JSON strings for cross-database compatibility
    c4_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    triz_principles: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    discovery: Mapped[Discovery] = relationship(back_populates="hypotheses")
