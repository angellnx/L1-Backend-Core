"""Frequency-based deck generation.

This is the core "no more picking what to study" feature: given a
language and a count, it looks at where the user last left off
(FrequencyProgress), pulls the next N words from the ranked
frequency list, creates a deck named after the rank range, and
creates one card per word — advancing the progress marker so the
next call continues from there automatically.

KNOWN LIMITATION (flagged deliberately, not glossed over): this
service does not translate words. Card.back is left as a
placeholder that the user (or a future integration) must fill in.
Auto-translation needs either a bundled bilingual dictionary or a
translation API, which is intentionally out of scope for this
sprint — see README roadmap. Without it, "front" is the target-
language word and "back" is a placeholder the CLI should prompt the
user to edit before the card is first studied.
"""
from l1_core.domain.models.card import Card, CardSource
from l1_core.domain.models.deck import Deck, DeckSource
from l1_core.domain.models.frequency_progress import FrequencyProgress
from l1_core.repositories.card_repository import CardRepository
from l1_core.repositories.deck_repository import DeckRepository
from l1_core.repositories.frequency_progress_repository import (
    FrequencyProgressRepository
)
from l1_core.repositories.frequency_repository import FrequencyRepository

TRANSLATION_PLACEHOLDER = "(translation pending)"


class FrequencyService:
    """Orchestrates frequency-based deck generation.

    Responsibilities:
    - Look up where the user last left off for a language
    - Pull the next N words from the ranked frequency list
    - Create a deck named after the rank range, and one card per word
    - Advance the progress marker so the next call continues automatically
    """

    def __init__(
        self,
        frequency_repository: FrequencyRepository,
        frequency_progress_repository: FrequencyProgressRepository,
        deck_repository: DeckRepository,
        card_repository: CardRepository
    ):
        self.frequency = frequency_repository
        self.progress = frequency_progress_repository
        self.decks = deck_repository
        self.cards = card_repository

    def generate_next_deck(self, language_code: str, count: int) -> Deck:
        """Generate the next frequency-based deck for a language.

        Continues from wherever the last call for this language left
        off, tracked via FrequencyProgress.

        Args:
            language_code: ISO 639-1 code of the language to generate
                a deck for (must have frequency data available).
            count: Number of cards to include in the deck.

        Returns:
            Deck: The created deck, with its cards persisted.

        Raises:
            FileNotFoundError: If no frequency list exists for the
                language (check Language.has_frequency_data first).
            ValueError: If count <= 0, or the language's frequency
                list is exhausted.
        """
        if count <= 0:
            raise ValueError("count must be a positive number of cards")

        language_code = language_code.lower()
        progress = self.progress.get(language_code)
        start_rank = progress.last_rank_used + 1
        end_rank = progress.last_rank_used + count

        total_available = self.frequency.total_words(language_code)
        if start_rank > total_available:
            raise ValueError(
                f"Frequency list for '{language_code}' exhausted "
                f"({total_available} words already used)"
            )
        end_rank = min(end_rank, total_available)

        words = self.frequency.get_words(language_code, start_rank, end_rank)
        if not words:
            raise ValueError(
                f"No words found for '{language_code}' in range {start_rank}-{end_rank}"
            )

        deck_name = Deck.frequency_deck_name(language_code, start_rank, end_rank)
        deck = Deck(
            name=deck_name,
            language_code=language_code,
            source=DeckSource.FREQUENCY,
            frequency_start=start_rank,
            frequency_end=end_rank
        )
        deck = self.decks.add(deck)

        cards = [
            Card(
                deck_id=deck.id,
                language_code=language_code,
                front=word,
                back=TRANSLATION_PLACEHOLDER,
                source=CardSource.FREQUENCY,
                frequency_rank=rank
            )
            for rank, word in words
        ]
        self.cards.add_many(cards)

        self.progress.upsert(
            FrequencyProgress(language_code=language_code, last_rank_used=end_rank)
        )

        return deck
