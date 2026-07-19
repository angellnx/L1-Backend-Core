import pytest

from l1_core.domain.models.card import Card
from l1_core.services.srs_service import SrsService


def make_card(**overrides) -> Card:
    defaults = dict(
        id=1,
        deck_id=1,
        language_code="en",
        front="hello",
        back="olá",
    )
    defaults.update(overrides)
    return Card(**defaults)


def test_first_correct_review_sets_interval_to_one_day():
    card = make_card()
    srs = SrsService()

    log = srs.review(card, quality=4)

    assert card.interval_days == 1
    assert card.repetitions == 1
    assert log.interval_before == 0
    assert log.interval_after == 1


def test_second_correct_review_sets_interval_to_six_days():
    card = make_card(repetitions=1, interval_days=1)
    srs = SrsService()

    srs.review(card, quality=4)

    assert card.interval_days == 6
    assert card.repetitions == 2


def test_third_correct_review_multiplies_by_ease_factor():
    card = make_card(repetitions=2, interval_days=6, ease_factor=2.5)
    srs = SrsService()

    srs.review(card, quality=5)

    assert card.interval_days == round(6 * 2.5)
    assert card.repetitions == 3


def test_lapse_resets_repetitions_and_interval():
    card = make_card(repetitions=5, interval_days=30, ease_factor=2.3)
    srs = SrsService()

    srs.review(card, quality=1)

    assert card.repetitions == 0
    assert card.interval_days == 1


def test_ease_factor_never_drops_below_floor():
    card = make_card(ease_factor=1.3)
    srs = SrsService()

    for _ in range(10):
        srs.review(card, quality=0)

    assert card.ease_factor >= 1.3


def test_perfect_recall_increases_ease_factor():
    card = make_card(ease_factor=2.5)
    srs = SrsService()

    srs.review(card, quality=5)

    assert card.ease_factor > 2.5


def test_quality_out_of_range_raises():
    card = make_card()
    srs = SrsService()

    with pytest.raises(ValueError):
        srs.review(card, quality=6)

    with pytest.raises(ValueError):
        srs.review(card, quality=-1)


def test_review_sets_next_review_at():
    card = make_card()
    srs = SrsService()
    assert card.next_review_at is None

    srs.review(card, quality=4)

    assert card.next_review_at is not None


def test_returns_review_log_matching_card_state():
    card = make_card()
    srs = SrsService()

    log = srs.review(card, quality=5, reaction_time_ms=1200)

    assert log.card_id == card.id
    assert log.quality == 5
    assert log.ease_factor_after == card.ease_factor
    assert log.interval_after == card.interval_days
    assert log.reaction_time_ms == 1200
