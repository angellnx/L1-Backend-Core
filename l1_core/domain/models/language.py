"""Language domain model.

Represents a language supported by L1. Kept intentionally minimal —
the frequency word list availability is a property of the language,
not a separate lookup, since it directly affects whether automatic
deck generation is possible for it.
"""
from dataclasses import dataclass


@dataclass
class Language:
    """A language supported by the system.

    Attributes:
        code: ISO 639-1 two-letter code (e.g. "en", "pt", "es").
        name: Human-readable name (e.g. "English", "Português").
        has_frequency_data: Whether a frequency word list exists for
            this language under l1_core/data/frequency/<code>.txt,
            enabling automatic deck generation.
    """

    code: str
    name: str
    has_frequency_data: bool = False

    def __post_init__(self) -> None:
        if not self.code or len(self.code) > 5:
            raise ValueError("Language code must be a short, non-empty string")
        self.code = self.code.lower()
