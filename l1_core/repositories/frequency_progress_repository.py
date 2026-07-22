"""FrequencyProgress repository.

Tiny repository around a single-row-per-language table tracking how
far into each language's frequency list the user has already gone.
"""
from sqlalchemy.orm import Session
from l1_core.database.models.orm_models import FrequencyProgressORM
from l1_core.domain.models.frequency_progress import FrequencyProgress


class FrequencyProgressRepository:
    """Coordinates FrequencyProgress domain model persistence."""

    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, orm: FrequencyProgressORM) -> FrequencyProgress:
        return FrequencyProgress(
            language_code=orm.language_code, last_rank_used=orm.last_rank_used
        )

    def get(self, language_code: str) -> FrequencyProgress:
        orm = self._session.get(FrequencyProgressORM, language_code.lower())
        if orm is None:
            return FrequencyProgress(language_code=language_code.lower(), last_rank_used=0)
        return self._to_domain(orm)

    def upsert(self, progress: FrequencyProgress) -> FrequencyProgress:
        orm = self._session.get(FrequencyProgressORM, progress.language_code)
        if orm is None:
            orm = FrequencyProgressORM(
                language_code=progress.language_code,
                last_rank_used=progress.last_rank_used
            )
            self._session.add(orm)
        else:
            orm.last_rank_used = progress.last_rank_used
        self._session.flush()
        return self._to_domain(orm)
