"""Language repository."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from l1_core.database.models.orm_models import LanguageORM
from l1_core.domain.models.language import Language


class LanguageRepository:
    """Coordinates Language domain model persistence."""

    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, orm: LanguageORM) -> Language:
        return Language(
            code=orm.code, name=orm.name, has_frequency_data=orm.has_frequency_data
        )

    def _to_orm(self, language: Language) -> LanguageORM:
        return LanguageORM(
            code=language.code,
            name=language.name,
            has_frequency_data=language.has_frequency_data
        )

    def add(self, language: Language) -> Language:
        orm = self._to_orm(language)
        self._session.merge(orm)
        self._session.flush()
        return language

    def get(self, code: str) -> Language | None:
        orm = self._session.get(LanguageORM, code.lower())
        return self._to_domain(orm) if orm else None

    def list_all(self) -> list[Language]:
        stmt = select(LanguageORM)
        return [self._to_domain(o) for o in self._session.scalars(stmt)]
