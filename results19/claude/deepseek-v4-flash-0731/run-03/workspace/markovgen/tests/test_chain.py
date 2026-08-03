from __future__ import annotations

from markovgen import MarkovChain, tokenize


def test_tokenize_basic():
    assert tokenize("the cat sat on the mat") == ["the", "cat", "sat", "on", "the", "mat"]


def test_tokenize_handles_punctuation_and_whitespace():
    assert tokenize("  hello,\nworld!  ") == ["hello,", "world!"]


def test_order_validation():
    try:
        MarkovChain(order=0)
    except ValueError:
        return
    raise AssertionError("order=0 should raise ValueError")


def test_token_counts():
    chain = MarkovChain(order=1).fit("a b c d")
    assert chain.token_count == 4
    # starts: (a),(b),(c),(d); transitions: a->b, b->c, c->d -> 3 pairs
    assert chain.transition_count == 3
    assert chain.start_count == 4


def test_fit_from_list_of_documents():
    chain = MarkovChain(order=1).fit(["a b", "c d"])
    assert chain.token_count == 4


def test_greedy_next_token():
    # (the,cat) is followed by "sat" more often than "ran", so greedy picks "sat".
    chain = MarkovChain(order=2, rng=__import__("random").Random(0)).fit(
        "the cat sat the cat ran the cat sat"
    )
    text = chain.generate(3)
    assert text == "the cat sat"


def test_generate_respects_length():
    chain = MarkovChain(order=1).fit("a b c d e")
    assert len(chain.generate(3).split()) == 3


def test_generate_with_seed():
    chain = MarkovChain(order=1).fit("red blue green red blue green")
    out = chain.generate(4, seed=["red"])
    assert out.split()[0] == "red"


def test_generate_stops_at_dead_end():
    chain = MarkovChain(order=1)
    chain.fit("a b")  # (b) has no outgoing transition
    text = chain.generate(10)
    # Every generated token comes from the vocabulary, never ``None``.
    assert set(text.split()) <= {"a", "b"}
    assert len(text.split()) <= 2


def test_generate_empty_on_empty_corpus():
    chain = MarkovChain(order=1).fit("   ")
    assert chain.generate(5) == ""


def test_output_tokens_all_from_vocabulary():
    chain = MarkovChain(order=2).fit("one two three one two four")
    out = chain.generate(20).split()
    vocab = {"one", "two", "three", "four"}
    assert set(out) <= vocab


def test_reproducible_with_fixed_seed():
    c1 = MarkovChain(order=2, rng=__import__("random").Random(42)).fit("x y z x y w")
    c2 = MarkovChain(order=2, rng=__import__("random").Random(42)).fit("x y z x y w")
    assert c1.generate(20) == c2.generate(20)
