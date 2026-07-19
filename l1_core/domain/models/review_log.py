"""ReviewLog domain model.

Stores the immutable history of every review. This is deliberately
kept separate from the Card's live SM-2 state: the Card holds "where
we are right now", the ReviewLog holds "everything that happened".

Keeping a full history (with `reviewed_at`, `updated_at`-style
timestamps) now — even though the current algorithm (SM-2) only
needs the card's current state — means a future migration to FSRS
(which needs the full review history to fit its model) does not
require a data migration, just a new SrsService implementation
reading from the same ReviewLog table.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ReviewLog:
    """A single, immutable review event.

    Attributes:
        id: Primary key (None until persisted).
        card_id: The card that was reviewed.
        quality: SM-2 grade for this review, 0-5
            (0 = complete blackout, 5 = perfect recall).
        interval_before: Card's interval_days before this review.
        interval_after: Card's interval_days after this review.
        ease_factor_after: Card's ease_factor after this review.
        reviewed_at: When the review happened (UTC).
        reaction_time_ms: Optional time taken to answer, in
            milliseconds. Not used by SM-2, but retained for a future
            FSRS migration and for study-habit stats.
    """

    card_id: int
    quality: int
    interval_before: int
    interval_after: int
    ease_factor_after: float
    id: int | None = None
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reaction_time_ms: int | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.quality <= 5:
            raise ValueError("quality must be between 0 and 5 (SM-2 grading scale)")
