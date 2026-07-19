from datetime import datetime, timedelta, timezone

from l1_core.domain.models.card import Card
from l1_core.domain.models.deck import Deck
from l1_core.repositories.card_repository import CardRepository
from l1_core.repositories.deck_repository import DeckRepository


def _create_deck(session, name="en-basics", language_code="en"):
    deck_repo = DeckRepository(session)
    deck = deck_repo.add(Deck(name=name, language_code=language_code))
    session.commit()
    return deck


def test_add_and_get_card(session):
    deck = _create_deck(session)
    repo = CardRepository(session)

    added = repo.add(
        Card(deck_id=deck.id, language_code="en", front="dog", back="cachorro")
    )
    session.commit()

    fetched = repo.get(added.id)
    assert fetched is not None
    assert fetched.front == "dog"
    assert fetched.back == "cachorro"
    assert fetched.ease_factor == 2.5


def test_list_by_deck_returns_only_that_decks_cards(session):
    deck_a = _create_deck(session, name="deck-a")
    deck_b = _create_deck(session, name="deck-b")
    repo = CardRepository(session)

    repo.add(Card(deck_id=deck_a.id, language_code="en", front="a1", back="b1"))
    repo.add(Card(deck_id=deck_b.id, language_code="en", front="a2", back="b2"))
    session.commit()

    cards = repo.list_by_deck(deck_a.id)
    assert len(cards) == 1
    assert cards[0].front == "a1"


def test_list_due_includes_new_cards_never_reviewed(session):
    deck = _create_deck(session)
    repo = CardRepository(session)
    repo.add(Card(deck_id=deck.id, language_code="en", front="new", back="novo"))
    session.commit()

    due = repo.list_due("en")
    assert len(due) == 1
    assert due[0].front == "new"


def test_list_due_excludes_cards_scheduled_in_the_future(session):
    deck = _create_deck(session)
    repo = CardRepository(session)
    future = datetime.now(timezone.utc) + timedelta(days=5)
    repo.add(
        Card(
            deck_id=deck.id,
            language_code="en",
            front="future",
            back="futuro",
            next_review_at=future,
            repetitions=1,
            interval_days=5,
        )
    )
    session.commit()

    due = repo.list_due("en")
    assert due == []


def test_list_due_includes_cards_scheduled_in_the_past(session):
    deck = _create_deck(session)
    repo = CardRepository(session)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    repo.add(
        Card(
            deck_id=deck.id,
            language_code="en",
            front="overdue",
            back="atrasado",
            next_review_at=past,
            repetitions=1,
            interval_days=1,
        )
    )
    session.commit()

    due = repo.list_due("en")
    assert len(due) == 1
    assert due[0].front == "overdue"


def test_update_persists_new_srs_state(session):
    deck = _create_deck(session)
    repo = CardRepository(session)
    card = repo.add(Card(deck_id=deck.id, language_code="en", front="cat", back="gato"))
    session.commit()

    card.ease_factor = 2.7
    card.interval_days = 6
    card.repetitions = 2
    repo.update(card)
    session.commit()

    fetched = repo.get(card.id)
    assert fetched.ease_factor == 2.7
    assert fetched.interval_days == 6
    assert fetched.repetitions == 2
