"""SQLAlchemy ORM models for PostgreSQL (Alembic autogenerate source of truth)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for c4reqber PostgreSQL schema."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(50), server_default="free")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    discoveries: Mapped[list[Discovery]] = relationship(back_populates="user")
    api_logs: Mapped[list[ApiLog]] = relationship(back_populates="user")


class Discovery(Base):
    __tablename__ = "discoveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    top_hypothesis: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), server_default="pending")
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float)
    validation_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    user: Mapped[Optional[User]] = relationship(back_populates="discoveries")
    hypotheses: Mapped[list[Hypothesis]] = relationship(back_populates="discovery")


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    discovery_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discoveries.id", ondelete="CASCADE")
    )
    hypothesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    method: Mapped[Optional[str]] = mapped_column(String(100))
    c4_path: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text))
    triz_principles: Mapped[Optional[list[int]]] = mapped_column(ARRAY(Integer))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    discovery: Mapped[Optional[Discovery]] = relationship(back_populates="hypotheses")


class ApiLog(Base):
    __tablename__ = "api_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    method: Mapped[Optional[str]] = mapped_column(String(10))
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    user: Mapped[Optional[User]] = relationship(back_populates="api_logs")