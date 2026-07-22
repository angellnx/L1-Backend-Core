import pytest

from l1_core.repositories.card_repository import CardRepository
from l1_core.repositories.deck_repository import DeckRepository
from l1_core.repositories.frequency_progress_repository import (
    FrequencyProgressRepository,
)
from l1_core.repositories.frequency_repository import FrequencyRepository
from l1_core.services.frequency_service import (
    TRANSLATION_PLACEHOLDER,
    FrequencyService,
)


@pytest.fixture()
def frequency_service(session):
    return FrequencyService(
        frequency_repository=FrequencyRepository(),  # uses shipped sample data
        frequency_progress_repository=FrequencyProgressRepository(session),
        deck_repository=DeckRepository(session),
        card_repository=CardRepository(session),
    )


def test_generate_first_deck_starts_at_rank_one(frequency_service, session):
    deck = frequency_service.generate_next_deck("en", count=10)
    session.commit()

    assert deck.frequency_start == 1
    assert deck.frequency_end == 10
    assert deck.name == "en-freq-0001-0010"

    cards = CardRepository(session).list_by_deck(deck.id)
    assert len(cards) == 10
    assert cards[0].front == "the"
    assert cards[0].frequency_rank == 1
    assert cards[0].back == TRANSLATION_PLACEHOLDER


def test_generate_next_deck_continues_from_last_rank(frequency_service, session):
    frequency_service.generate_next_deck("en", count=10)
    session.commit()

    second_deck = frequency_service.generate_next_deck("en", count=10)
    session.commit()

    assert second_deck.frequency_start == 11
    assert second_deck.frequency_end == 20
    assert second_deck.name == "en-freq-0011-0020"


def test_generate_deck_for_unknown_language_raises(frequency_service):
    with pytest.raises(FileNotFoundError):
        frequency_service.generate_next_deck("xx", count=10)


def test_generate_deck_with_non_positive_count_raises(frequency_service):
    with pytest.raises(ValueError):
        frequency_service.generate_next_deck("en", count=0)
