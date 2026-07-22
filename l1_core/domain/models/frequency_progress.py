"""FrequencyProgress domain model.

Tracks, per language, the last frequency rank already turned into a
deck — so `l1 deck generate` always knows where to continue from
without the user having to remember or specify it.

In the current single-user CLI this is scoped only by language_code.
A `user_id` field is intentionally omitted for now; when L1 grows a
backend API with multiple users, this becomes composite-keyed on
(user_id, language_code) — a small, additive change.
"""
from dataclasses import dataclass


@dataclass
class FrequencyProgress:
    """Tracks how far into a language's frequency list the user has
    already generated decks.

    Attributes:
        language_code: ISO 639-1 code of the language.
        last_rank_used: The highest frequency rank already included
            in a generated deck. 0 means nothing generated yet.
    """

    language_code: str
    last_rank_used: int = 0

    def __post_init__(self) -> None:
        if self.last_rank_used < 0:
            raise ValueError("last_rank_used cannot be negative")
