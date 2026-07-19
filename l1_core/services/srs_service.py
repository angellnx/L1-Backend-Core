"""Spaced repetition scheduling service.

Implements SM-2 (the algorithm behind the original SuperMemo/early
Anki). Deliberately pure: it only touches the Card object passed in
and returns the ReviewLog entry describing what happened — no
database session, no I/O. This makes it trivial to unit test and,
later, to swap for an FSRS-based implementation without touching any
other layer (repositories/CLI would be unaffected — only this file
and its tests change).

Quality scale (0-5), the standard SM-2 grading:
    0 - complete blackout
    1 - wrong, but the correct answer felt familiar
    2 - wrong, but the correct answer was easy to recall once shown
    3 - correct, but required significant effort
    4 - correct, with some hesitation
    5 - correct, perfect recall
Quality < 3 counts as a lapse and resets the repetition streak.
"""
from datetime import datetime, timedelta, timezone
from l1_core.domain.models.card import Card
from l1_core.domain.models.review_log import ReviewLog

MIN_EASE_FACTOR = 1.3
LAPSE_QUALITY_THRESHOLD = 3


class SrsService:
    """Pure SM-2 spaced-repetition scheduling, with no I/O of its own."""

    def review(self, card: Card, quality: int, reaction_time_ms: int | None = None) -> ReviewLog:
        """Apply a single SM-2 review to a card, mutating it in place.

        Args:
            card: The card being reviewed. Its SM-2 state (ease
                factor, interval, repetitions, next_review_at) is
                mutated directly.
            quality: SM-2 grade for this review, 0-5.
            reaction_time_ms: Optional time taken to answer, in
                milliseconds. Not used by SM-2, but carried onto the
                resulting ReviewLog for future FSRS use and stats.

        Returns:
            ReviewLog: A record of this review, matching the card's
                updated state.

        Raises:
            ValueError: If quality is not in [0, 5].
        """
        if not 0 <= quality <= 5:
            raise ValueError("quality must be between 0 and 5")

        interval_before = card.interval_days

        if quality < LAPSE_QUALITY_THRESHOLD:
            card.repetitions = 0
            card.interval_days = 1
        else:
            if card.repetitions == 0:
                card.interval_days = 1
            elif card.repetitions == 1:
                card.interval_days = 6
            else:
                card.interval_days = round(card.interval_days * card.ease_factor)
            card.repetitions += 1

        new_ease_factor = card.ease_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        card.ease_factor = max(MIN_EASE_FACTOR, round(new_ease_factor, 2))

        now = datetime.now(timezone.utc)
        card.next_review_at = now + timedelta(days=card.interval_days)

        return ReviewLog(
            card_id=card.id,
            quality=quality,
            interval_before=interval_before,
            interval_after=card.interval_days,
            ease_factor_after=card.ease_factor,
            reviewed_at=now,
            reaction_time_ms=reaction_time_ms
        )
