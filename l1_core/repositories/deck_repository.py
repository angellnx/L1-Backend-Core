"""Deck repository."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from l1_core.database.models.orm_models import DeckORM
from l1_core.domain.models.deck import Deck, DeckSource


class DeckRepository:
    """Coordinates Deck domain model persistence."""

    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, orm: DeckORM) -> Deck:
        return Deck(
            id=orm.id,
            name=orm.name,
            language_code=orm.language_code,
            source=DeckSource(orm.source),
            frequency_start=orm.frequency_start,
            frequency_end=orm.frequency_end,
            created_at=orm.created_at
        )

    def _to_orm(self, deck: Deck) -> DeckORM:
        return DeckORM(
            id=deck.id,
            name=deck.name,
            language_code=deck.language_code,
            source=deck.source.value,
            frequency_start=deck.frequency_start,
            frequency_end=deck.frequency_end,
            created_at=deck.created_at
        )

    def add(self, deck: Deck) -> Deck:
        orm = self._to_orm(deck)
        self._session.add(orm)
        self._session.flush()
        return self._to_domain(orm)

    def get(self, deck_id: int) -> Deck | None:
        orm = self._session.get(DeckORM, deck_id)
        return self._to_domain(orm) if orm else None

    def get_by_name(self, name: str) -> Deck | None:
        stmt = select(DeckORM).where(DeckORM.name == name)
        orm = self._session.scalars(stmt).first()
        return self._to_domain(orm) if orm else None

    def list_by_language(self, language_code: str) -> list[Deck]:
        stmt = select(DeckORM).where(DeckORM.language_code == language_code)
        return [self._to_domain(o) for o in self._session.scalars(stmt)]

    def list_all(self) -> list[Deck]:
        stmt = select(DeckORM)
        return [self._to_domain(o) for o in self._session.scalars(stmt)]
