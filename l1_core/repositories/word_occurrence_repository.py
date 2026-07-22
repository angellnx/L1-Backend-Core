"""Word occurrence repository.

Counts how many times a word appears (as a card's front text) across
every card in the database, for a given language — an aggregate over
every user of the app, not just one deck or one user's own cards.

Unlike FrequencyRepository (which reads static pre-ranked frequency
lists shipped with the app), this repository derives frequency
directly from live app data: the words users are actually adding and
studying. There is no per-user scoping here on purpose — the whole
point is a count across the app's whole user base.

Matching is case-insensitive. A card's front is compared as a whole
string, not searched as a substring — this matches the granularity
cards are actually created at (one word or short expression per
card), so a card with front "the dog" is not counted as an
occurrence of "dog".
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from l1_core.database.models.orm_models import CardORM


class WordOccurrenceRepository:
    """Counts word occurrences across all cards, all users, all decks."""

    def __init__(self, session: Session):
        self._session = session

    def count_occurrences(self, language_code: str, word: str) -> int:
        """Count how many cards use `word` as their front text, in a language.

        Args:
            language_code: ISO 639-1 code of the language to count within.
            word: The word (or short expression) to count occurrences of.
                Matching is case-insensitive and whitespace-trimmed.

        Returns:
            int: Number of cards, across every user of the app, whose
                front matches `word` in that language. 0 if no one has
                added that word yet.
        """
        normalized = word.strip().lower()
        stmt = (
            select(func.count())
            .select_from(CardORM)
            .where(
                CardORM.language_code == language_code.lower(),
                func.lower(CardORM.front) == normalized,
            )
        )
        return self._session.scalar(stmt) or 0

    def get_word_counts(
        self, language_code: str, limit: int | None = None
    ) -> list[tuple[str, int]]:
        """Rank every distinct word by how many cards use it, for a language.

        Useful as a live, community-driven alternative to a static
        frequency list: words many users are studying rise to the top
        naturally, without shipping a pre-built dataset.

        Args:
            language_code: ISO 639-1 code of the language to rank within.
            limit: Optional cap on the number of words returned.

        Returns:
            list[tuple[str, int]]: (word, occurrence_count) pairs, most
                frequent first. Words differing only by case are merged
                into a single lowercase entry.
        """
        stmt = (
            select(func.lower(CardORM.front), func.count())
            .where(CardORM.language_code == language_code.lower())
            .group_by(func.lower(CardORM.front))
            .order_by(func.count().desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return [(word, count) for word, count in self._session.execute(stmt)]
