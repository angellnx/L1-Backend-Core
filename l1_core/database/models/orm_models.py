"""ORM (SQLAlchemy) models.

These mirror the domain models but are pure persistence concerns —
table names, foreign keys, indexes. They never contain business
logic; conversion to/from domain models happens in the repository
layer, keeping the domain package free of infrastructure imports.
"""
from datetime import datetime, timezone
from sqlalchemy import Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from l1_core.database.base import Base


class LanguageORM(Base):
    """ORM model for Language persistence."""

    __tablename__ = "languages"

    code: Mapped[str] = mapped_column(String(5), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    has_frequency_data: Mapped[bool] = mapped_column(default=False)


class DeckORM(Base):
    """ORM model for Deck persistence.

    A deck belongs to a language and owns many cards.
    """

    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    language_code: Mapped[str] = mapped_column(String(5), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    frequency_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    cards: Mapped[list["CardORM"]] = relationship(back_populates="deck")


class CardORM(Base):
    """ORM model for Card persistence.

    A card belongs to a deck and owns its own live SM-2 state.
    """

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(5), nullable=False)
    front: Mapped[str] = mapped_column(String(500), nullable=False)
    back: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    frequency_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    deck: Mapped["DeckORM"] = relationship(back_populates="cards")
    review_logs: Mapped[list["ReviewLogORM"]] = relationship(back_populates="card")


class ReviewLogORM(Base):
    """ORM model for ReviewLog persistence.

    Immutable history of every review, kept separate from the card's
    live SM-2 state.
    """

    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False)
    quality: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_before: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_after: Mapped[int] = mapped_column(Integer, nullable=False)
    ease_factor_after: Mapped[float] = mapped_column(Float, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    reaction_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    card: Mapped["CardORM"] = relationship(back_populates="review_logs")
