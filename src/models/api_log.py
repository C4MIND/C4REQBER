"""API log model for rate limiting."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import GUID, Base


if TYPE_CHECKING:
    from src.models.user import User


class ApiLog(Base):
    """API request log for rate limiting and monitoring."""

    __tablename__ = "api_logs"

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
    endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    user: Mapped[User | None] = relationship()
