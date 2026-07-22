from l1_core.domain.models.card import Card
from l1_core.domain.models.deck import Deck
from l1_core.repositories.card_repository import CardRepository
from l1_core.repositories.deck_repository import DeckRepository
from l1_core.repositories.word_occurrence_repository import WordOccurrenceRepository


def _create_deck(session, name="en-basics", language_code="en"):
    deck_repo = DeckRepository(session)
    deck = deck_repo.add(Deck(name=name, language_code=language_code))
    session.commit()
    return deck


def test_count_occurrences_counts_across_multiple_decks(session):
    deck_a = _create_deck(session, name="deck-a")
    deck_b = _create_deck(session, name="deck-b")
    card_repo = CardRepository(session)
    card_repo.add(Card(deck_id=deck_a.id, language_code="en", front="dog", back="cachorro"))
    card_repo.add(Card(deck_id=deck_b.id, language_code="en", front="dog", back="cachorro"))
    card_repo.add(Card(deck_id=deck_b.id, language_code="en", front="cat", back="gato"))
    session.commit()

    repo = WordOccurrenceRepository(session)
    assert repo.count_occurrences("en", "dog") == 2
    assert repo.count_occurrences("en", "cat") == 1


def test_count_occurrences_is_case_insensitive(session):
    deck = _create_deck(session)
    card_repo = CardRepository(session)
    card_repo.add(Card(deck_id=deck.id, language_code="en", front="Dog", back="cachorro"))
    card_repo.add(Card(deck_id=deck.id, language_code="en", front="DOG", back="cachorro"))
    session.commit()

    repo = WordOccurrenceRepository(session)
    assert repo.count_occurrences("en", "dog") == 2


def test_count_occurrences_does_not_match_substrings(session):
    deck = _create_deck(session)
    card_repo = CardRepository(session)
    card_repo.add(Card(deck_id=deck.id, language_code="en", front="the dog", back="o cachorro"))
    session.commit()

    repo = WordOccurrenceRepository(session)
    assert repo.count_occurrences("en", "dog") == 0


def test_count_occurrences_is_scoped_by_language(session):
    deck_en = _create_deck(session, name="en-deck", language_code="en")
    deck_pt = _create_deck(session, name="pt-deck", language_code="pt")
    card_repo = CardRepository(session)
    card_repo.add(Card(deck_id=deck_en.id, language_code="en", front="pão", back="bread"))
    card_repo.add(Card(deck_id=deck_pt.id, language_code="pt", front="pão", back="bread"))
    card_repo.add(Card(deck_id=deck_pt.id, language_code="pt", front="pão", back="bread"))
    session.commit()

    repo = WordOccurrenceRepository(session)
    assert repo.count_occurrences("en", "pão") == 1
    assert repo.count_occurrences("pt", "pão") == 2


def test_count_occurrences_returns_zero_for_unknown_word(session):
    _create_deck(session)
    repo = WordOccurrenceRepository(session)
    assert repo.count_occurrences("en", "nonexistent") == 0


def test_get_word_counts_orders_by_frequency_descending(session):
    deck = _create_deck(session)
    card_repo = CardRepository(session)
    for front in ["dog", "dog", "dog", "cat", "cat", "bird"]:
        card_repo.add(Card(deck_id=deck.id, language_code="en", front=front, back="x"))
    session.commit()

    repo = WordOccurrenceRepository(session)
    counts = repo.get_word_counts("en")
    assert counts == [("dog", 3), ("cat", 2), ("bird", 1)]


def test_get_word_counts_merges_case_variants(session):
    deck = _create_deck(session)
    card_repo = CardRepository(session)
    card_repo.add(Card(deck_id=deck.id, language_code="en", front="Dog", back="x"))
    card_repo.add(Card(deck_id=deck.id, language_code="en", front="dog", back="x"))
    session.commit()

    repo = WordOccurrenceRepository(session)
    counts = repo.get_word_counts("en")
    assert counts == [("dog", 2)]


def test_get_word_counts_respects_limit(session):
    deck = _create_deck(session)
    card_repo = CardRepository(session)
    for front in ["dog", "dog", "cat"]:
        card_repo.add(Card(deck_id=deck.id, language_code="en", front=front, back="x"))
    session.commit()

    repo = WordOccurrenceRepository(session)
    counts = repo.get_word_counts("en", limit=1)
    assert counts == [("dog", 2)]


def test_get_word_counts_empty_when_no_cards(session):
    _create_deck(session)
    repo = WordOccurrenceRepository(session)
    assert repo.get_word_counts("en") == []
