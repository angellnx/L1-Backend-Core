"""Card repository.

Converts between the Card domain model and CardORM, and scopes
queries the way the CLI needs them: by deck, by language, and by
due status (for study sessions).
"""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from l1_core.database.models.orm_models import CardORM
from l1_core.domain.models.card import Card, CardSource


class CardRepository:
    """Coordinates Card domain model persistence."""

    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, orm: CardORM) -> Card:
        return Card(
            id=orm.id,
            deck_id=orm.deck_id,
            language_code=orm.language_code,
            front=orm.front,
            back=orm.back,
            source=CardSource(orm.source),
            frequency_rank=orm.frequency_rank,
            ease_factor=orm.ease_factor,
            interval_days=orm.interval_days,
            repetitions=orm.repetitions,
            next_review_at=orm.next_review_at,
            created_at=orm.created_at
        )

    def _to_orm(self, card: Card) -> CardORM:
        return CardORM(
            id=card.id,
            deck_id=card.deck_id,
            language_code=card.language_code,
            front=card.front,
            back=card.back,
            source=card.source.value,
            frequency_rank=card.frequency_rank,
            ease_factor=card.ease_factor,
            interval_days=card.interval_days,
            repetitions=card.repetitions,
            next_review_at=card.next_review_at,
            created_at=card.created_at
        )

    def add(self, card: Card) -> Card:
        orm = self._to_orm(card)
        self._session.add(orm)
        self._session.flush()
        return self._to_domain(orm)

    def add_many(self, cards: list[Card]) -> list[Card]:
        orms = [self._to_orm(c) for c in cards]
        self._session.add_all(orms)
        self._session.flush()
        return [self._to_domain(o) for o in orms]

    def get(self, card_id: int) -> Card | None:
        orm = self._session.get(CardORM, card_id)
        return self._to_domain(orm) if orm else None

    def list_by_deck(self, deck_id: int) -> list[Card]:
        stmt = select(CardORM).where(CardORM.deck_id == deck_id)
        return [self._to_domain(o) for o in self._session.scalars(stmt)]

    def list_due(self, language_code: str, limit: int = 20) -> list[Card]:
        """Retrieve cards due for review in a given language.

        A card is due if it has never been reviewed, or its
        next_review_at has already passed.

        Args:
            language_code: ISO 639-1 code of the language to study.
            limit: Maximum number of cards to return.

        Returns:
            list[Card]: Due cards, soonest-due first.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(CardORM)
            .where(CardORM.language_code == language_code)
            .where(
                (CardORM.next_review_at.is_(None)) | (CardORM.next_review_at <= now)
            )
            .order_by(CardORM.next_review_at.asc().nulls_first())
            .limit(limit)
        )
        return [self._to_domain(o) for o in self._session.scalars(stmt)]

    def update(self, card: Card) -> Card:
        if card.id is None:
            raise ValueError("Cannot update a card without an id")
        orm = self._session.get(CardORM, card.id)
        if orm is None:
            raise ValueError(f"Card {card.id} not found")
        orm.ease_factor = card.ease_factor
        orm.interval_days = card.interval_days
        orm.repetitions = card.repetitions
        orm.next_review_at = card.next_review_at
        self._session.flush()
        return self._to_domain(orm)

    def max_frequency_rank(self, language_code: str) -> int:
        """Retrieve the highest frequency rank already turned into a card.

        Used as a safety cross-check alongside FrequencyProgress.

        Args:
            language_code: ISO 639-1 code of the language to check.

        Returns:
            int: Highest frequency_rank already used, or 0 if none.
        """
        stmt = select(CardORM).where(
            CardORM.language_code == language_code,
            CardORM.source == CardSource.FREQUENCY.value
        )
        ranks = [o.frequency_rank for o in self._session.scalars(stmt) if o.frequency_rank]
        return max(ranks) if ranks else 0
