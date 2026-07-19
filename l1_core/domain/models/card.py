"""Card domain model.

Key decision (same philosophy as A1 Backend Core): Rich Model over
Anemic Model. The Card owns its own spaced-repetition state (ease
factor, interval, repetitions, next review date) and exposes a
`is_due` business rule directly, instead of scattering that logic
across services. The SrsService is the only thing allowed to mutate
this state, and it does so through the card itself.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class CardSource(str, Enum):
    """Where a card originated from."""

    MANUAL = "manual"
    FREQUENCY = "frequency"


@dataclass
class Card:
    """A single flashcard belonging to a deck.

    Attributes:
        id: Primary key (None until persisted).
        deck_id: Owning deck.
        language_code: ISO 639-1 code of the language being studied.
        front: Prompt shown to the user.
        back: Answer/translation.
        source: Whether the card was added manually or generated from
            a frequency list.
        frequency_rank: Rank in the frequency list this card came
            from (None for manual cards).
        ease_factor: SM-2 ease factor, starts at 2.5.
        interval_days: Current interval between reviews, in days.
        repetitions: Consecutive correct reviews (quality >= 3).
        next_review_at: When this card is next due. None means it has
            never been reviewed and is due immediately.
        created_at: Creation timestamp (UTC).
    """

    deck_id: int
    language_code: str
    front: str
    back: str
    id: int | None = None
    source: CardSource = CardSource.MANUAL
    frequency_rank: int | None = None
    ease_factor: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    next_review_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.front.strip() or not self.back.strip():
            raise ValueError("Card front and back cannot be empty")
        if self.ease_factor < 1.3:
            raise ValueError("ease_factor cannot drop below 1.3 (SM-2 floor)")

    @property
    def is_due(self) -> bool:
        """A card is due if it has never been reviewed, or its next
        review date has already passed."""
        if self.next_review_at is None:
            return True
        now = datetime.now(timezone.utc)
        next_review = self.next_review_at
        if next_review.tzinfo is None:
            next_review = next_review.replace(tzinfo=timezone.utc)
        return next_review <= now

    @property
    def is_new(self) -> bool:
        """A card that has never been reviewed."""
        return self.repetitions == 0 and self.next_review_at is None
