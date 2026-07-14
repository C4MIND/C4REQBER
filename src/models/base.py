"""SQLAlchemy base model and utilities for cross-database compatibility."""
import uuid
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):  # type: ignore[type-arg]
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect: Any) -> None:
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)  # type: ignore[return-value]
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))  # type: ignore[return-value]
            return str(value)  # type: ignore[return-value]

    def process_result_value(self, value: Any, dialect: Any) -> None:
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value  # type: ignore[no-any-return]


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass
