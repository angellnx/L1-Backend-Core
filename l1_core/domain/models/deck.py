"""Deck domain model."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class DeckSource(str, Enum):
    """How a deck's cards were populated."""

    MANUAL = "manual"
    FREQUENCY = "frequency"


@dataclass
class Deck:
    """A named collection of cards for a given language.

    Attributes:
        id: Primary key (None until persisted).
        name: Display name (auto-generated for frequency decks, e.g.
            "en-freq-0001-0020").
        language_code: ISO 639-1 code of the language this deck teaches.
        source: MANUAL (curated by hand) or FREQUENCY (auto-generated
            from a word-frequency list).
        frequency_start: First rank included, when source is FREQUENCY.
        frequency_end: Last rank included, when source is FREQUENCY.
        created_at: Creation timestamp (UTC).
    """

    name: str
    language_code: str
    id: int | None = None
    source: DeckSource = DeckSource.MANUAL
    frequency_start: int | None = None
    frequency_end: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Deck name cannot be empty")
        if self.source == DeckSource.FREQUENCY:
            if self.frequency_start is None or self.frequency_end is None:
                raise ValueError(
                    "Frequency decks must define frequency_start and frequency_end"
                )
            if self.frequency_start > self.frequency_end:
                raise ValueError("frequency_start cannot be greater than frequency_end")

    @classmethod
    def frequency_deck_name(cls, language_code: str, start: int, end: int) -> str:
        """Generates the conventional name for a frequency-based deck,
        e.g. 'en-freq-0021-0040'."""
        return f"{language_code}-freq-{start:04d}-{end:04d}"
