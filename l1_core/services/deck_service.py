"""Deck service: creating and listing decks, and adding manual cards
to them."""
from l1_core.domain.models.card import Card, CardSource
from l1_core.domain.models.deck import Deck, DeckSource
from l1_core.repositories.card_repository import CardRepository
from l1_core.repositories.deck_repository import DeckRepository


class DeckService:
    """Orchestrates manual deck and card creation, and deck listing.

    Responsibilities:
    - Validate deck/card inputs (name uniqueness, deck existence)
    - Coordinate between the CLI (and, later, routers) and the
      repository layer
    """

    def __init__(self, deck_repository: DeckRepository, card_repository: CardRepository):
        self.decks = deck_repository
        self.cards = card_repository

    def create_manual_deck(self, name: str, language_code: str) -> Deck:
        """Create a new manually-curated deck.

        Args:
            name: Deck name (must be unique).
            language_code: ISO 639-1 code of the language this deck teaches.

        Returns:
            Deck: The created domain model.

        Raises:
            ValueError: If a deck with this name already exists.
        """
        existing = self.decks.get_by_name(name)
        if existing is not None:
            raise ValueError(f"A deck named '{name}' already exists")
        deck = Deck(name=name, language_code=language_code, source=DeckSource.MANUAL)
        return self.decks.add(deck)

    def add_card(self, deck_id: int, front: str, back: str) -> Card:
        """Add a manually-created card to an existing deck.

        Args:
            deck_id: The deck to add the card to (must exist).
            front: Prompt shown to the user.
            back: Answer/translation.

        Returns:
            Card: The created domain model.

        Raises:
            ValueError: If the deck doesn't exist.
        """
        deck = self.decks.get(deck_id)
        if deck is None:
            raise ValueError(f"Deck {deck_id} not found")
        card = Card(
            deck_id=deck_id,
            language_code=deck.language_code,
            front=front,
            back=back,
            source=CardSource.MANUAL
        )
        return self.cards.add(card)

    def list_decks(self, language_code: str | None = None) -> list[Deck]:
        """List decks, optionally filtered by language.

        Args:
            language_code: ISO 639-1 code to filter by. If omitted,
                all decks are returned.

        Returns:
            list[Deck]: Matching decks.
        """
        if language_code:
            return self.decks.list_by_language(language_code)
        return self.decks.list_all()
