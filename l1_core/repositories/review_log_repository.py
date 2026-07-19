"""ReviewLog repository."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from l1_core.database.models.orm_models import ReviewLogORM
from l1_core.domain.models.review_log import ReviewLog


class ReviewLogRepository:
    """Coordinates ReviewLog domain model persistence."""

    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, orm: ReviewLogORM) -> ReviewLog:
        return ReviewLog(
            id=orm.id,
            card_id=orm.card_id,
            quality=orm.quality,
            interval_before=orm.interval_before,
            interval_after=orm.interval_after,
            ease_factor_after=orm.ease_factor_after,
            reviewed_at=orm.reviewed_at,
            reaction_time_ms=orm.reaction_time_ms
        )

    def _to_orm(self, log: ReviewLog) -> ReviewLogORM:
        return ReviewLogORM(
            id=log.id,
            card_id=log.card_id,
            quality=log.quality,
            interval_before=log.interval_before,
            interval_after=log.interval_after,
            ease_factor_after=log.ease_factor_after,
            reviewed_at=log.reviewed_at,
            reaction_time_ms=log.reaction_time_ms
        )

    def add(self, log: ReviewLog) -> ReviewLog:
        orm = self._to_orm(log)
        self._session.add(orm)
        self._session.flush()
        return self._to_domain(orm)

    def list_by_card(self, card_id: int) -> list[ReviewLog]:
        """Retrieve the full review history for a card, oldest first.

        Args:
            card_id: The card to fetch review history for.

        Returns:
            list[ReviewLog]: Review history, ordered chronologically.
        """
        stmt = (
            select(ReviewLogORM)
            .where(ReviewLogORM.card_id == card_id)
            .order_by(ReviewLogORM.reviewed_at.asc())
        )
        return [self._to_domain(o) for o in self._session.scalars(stmt)]

    def count_total(self) -> int:
        """Count the total number of review log entries.

        Returns:
            int: Total number of reviews recorded across all cards.
        """
        stmt = select(ReviewLogORM)
        return len(list(self._session.scalars(stmt)))
