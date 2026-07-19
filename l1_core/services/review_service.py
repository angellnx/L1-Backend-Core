"""Review service: orchestrates a study session by pulling due cards,
delegating the SM-2 calculation to SrsService, and persisting both
the updated card state and the resulting ReviewLog."""
from l1_core.domain.models.card import Card
from l1_core.domain.models.review_log import ReviewLog
from l1_core.repositories.card_repository import CardRepository
from l1_core.repositories.review_log_repository import ReviewLogRepository
from l1_core.services.srs_service import SrsService


class ReviewService:
    """Orchestrates a study session.

    Responsibilities:
    - Fetch cards due for review
    - Delegate SM-2 grading to SrsService
    - Persist the updated card state and the resulting ReviewLog
    """

    def __init__(
        self,
        card_repository: CardRepository,
        review_log_repository: ReviewLogRepository,
        srs_service: SrsService | None = None
    ):
        self.cards = card_repository
        self.logs = review_log_repository
        self.srs = srs_service or SrsService()

    def get_due_cards(self, language_code: str, limit: int = 20) -> list[Card]:
        """Retrieve cards due for review in a given language.

        Args:
            language_code: ISO 639-1 code of the language to study.
            limit: Maximum number of cards to return.

        Returns:
            list[Card]: Due cards, soonest-due first.
        """
        return self.cards.list_due(language_code, limit=limit)

    def submit_review(
        self, card: Card, quality: int, reaction_time_ms: int | None = None
    ) -> ReviewLog:
        """Grade a single card and persist the result.

        Applies the SM-2 grading, persists the card's updated
        scheduling state, and records the review in history.

        Args:
            card: The card being reviewed.
            quality: SM-2 grade for this review, 0-5.
            reaction_time_ms: Optional time taken to answer, in
                milliseconds.

        Returns:
            ReviewLog: The created review log entry.
        """
        log = self.srs.review(card, quality, reaction_time_ms=reaction_time_ms)
        self.cards.update(card)
        return self.logs.add(log)
