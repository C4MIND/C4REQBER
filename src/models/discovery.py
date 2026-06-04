"""Discovery model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import GUID, Base


if TYPE_CHECKING:
    from src.models.hypothesis import Hypothesis
    from src.models.user import User


class Discovery(Base):
    """A discovery/hypothesis generation session."""

    __tablename__ = "discoveries"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    top_hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped[User | None] = relationship(back_populates="discoveries")
    hypotheses: Mapped[list[Hypothesis]] = relationship(
        back_populates="discovery",
        cascade="all, delete-orphan"
    )
