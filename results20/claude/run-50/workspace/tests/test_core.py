"""Tests for the Markov chain core."""

import random

import pytest

from markov import MarkovModel, train_on_text
from markov.cli import _from_dict, _to_dict


def test_order_must_be_positive():
    with pytest.raises(ValueError):
        MarkovModel(order=0)
    with pytest.raises(ValueError):
        MarkovModel(order=-3)


def test_generate_before_training_raises():
    with pytest.raises(ValueError):
        MarkovModel().generate()


def test_single_document_reproduces_itself():
    # With only one document, an order-1 uniform model must reproduce it.
    model = MarkovModel(order=2, weighted=False).train("the cat sat")
    out = model.generate(max_words=10, rng=random.Random(0))
    assert out == "the cat sat"


def test_order_two_uses_pair_context():
    # "dog" should follow "the brown", not appear elsewhere.
    corpus = "the brown dog ran\n" "the white cat slept"
    model = MarkovModel(order=2, weighted=False)
    train_on_text(model, corpus)

    # Force the state (END, the) -> "brown"; then (the, brown) -> "dog".
    rng = random.Random(0)
    state = ("\x00", "the")
    assert model._pick(state, rng) == "brown"
    state = ("the", "brown")
    assert model._pick(state, rng) == "dog"


def test_max_words_caps_output():
    model = MarkovModel(order=2, weighted=False).train(
        "one two three four five six seven eight nine ten"
    )
    out = model.generate(max_words=4, rng=random.Random(0))
    assert len(out.split()) <= 4


def test_vocabulary_and_document_counts():
    model = MarkovModel()
    train_on_text(model, "a b c\n\na d")
    assert model.vocabulary == 4  # {a, b, c, d}
    assert model.documents == 2


def test_serialisation_round_trip():
    model = MarkovModel(order=2, weighted=True)
    train_on_text(model, "the quick fox jumps\n\nthe lazy dog sleeps")

    data = _to_dict(model)
    assert data["order"] == 2
    assert "the lazy" in data["_data"]

    clone = _from_dict(data)
    assert clone.order == model.order
    assert clone.weighted == model.weighted
    assert clone.documents == model.documents
    # Same seeded output both sides.
    a = model.generate(max_words=30, rng=random.Random(7))
    b = clone.generate(max_words=30, rng=random.Random(7))
    assert a == b


def test_generation_is_reproducible_with_seed():
    m1 = MarkovModel(order=2)
    m2 = MarkovModel(order=2)
    train_on_text(m1, "alpha beta gamma\n\nalpha delta")
    train_on_text(m2, "alpha beta gamma\n\nalpha delta")

    out1 = m1.generate(max_words=20, rng=random.Random(42))
    out2 = m2.generate(max_words=20, rng=random.Random(42))
    assert out1 == out2


def test_weighted_output_favours_frequent_continuation():
    # "a" is followed by "red" 9 times and "blue" once.
    docs = ["a red"] * 9 + ["a blue"]
    model = MarkovModel(order=1, weighted=True)
    model.train_iter(docs)

    seen_blue = 0
    for i in range(200):
        state = ("\x00", "a")
        if model._pick(state, random.Random(i)) == "blue":
            seen_blue += 1
    # With 10% frequency we expect ~20 blue picks; allow a wide band.
    assert seen_blue < 60
