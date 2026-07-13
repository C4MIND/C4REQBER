"""ORM metadata smoke tests (no live database required)."""

from __future__ import annotations

from data.orm import ApiLog, Base, Discovery, Hypothesis, User


def test_orm_tables_registered() -> None:
    names = set(Base.metadata.tables.keys())
    assert names == {"users", "discoveries", "hypotheses", "api_logs"}


def test_orm_models_importable() -> None:
    assert User.__tablename__ == "users"
    assert Discovery.__tablename__ == "discoveries"
    assert Hypothesis.__tablename__ == "hypotheses"
    assert ApiLog.__tablename__ == "api_logs"


def test_user_email_column() -> None:
    email_col = User.__table__.c.email
    assert email_col.unique is True
    assert email_col.nullable is False
