"""Command-line interface for MarkovText.

Examples
--------
    markovtext train corpus.txt -o model.json
    markovtext generate model.json --max-words 40 --count 3
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from .core import END, MarkovModel, train_on_file, train_on_text

# We store the transition table as a plain dict so it serialises to JSON.
_PLAIN = "_data"


def _to_dict(model: MarkovModel) -> dict:
    rows = {}
    for state, options in model._follows.items():
        # state is a tuple (needs joining); each continuation is a single
        # string word (kept as-is).
        rows[" ".join(state)] = {
            k if k != END else "__END__": v for k, v in options.items()
        }
    return {
        "order": model.order,
        "weighted": model.weighted,
        "documents": model.documents,
        _PLAIN: rows,
    }


def _from_dict(data: dict) -> MarkovModel:
    model = MarkovModel(order=data["order"], weighted=data["weighted"])
    for state_str, options in data[_PLAIN].items():
        state = tuple(state_str.split())  # boundary "\x00 \x00" -> (END, END)
        model._follows[state] = {
            (k if k != "__END__" else END): v for k, v in options.items()
        }
    model._distinct = data.get("documents", 0)
    return model


def _load_model(path: Path) -> MarkovModel:
    return _from_dict(json.loads(path.read_text(encoding="utf-8")))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="markovtext",
        description="Train and generate text with a Markov chain.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    train = sub.add_parser("train", help="train a model from a corpus file")
    train.add_argument("corpus", type=Path, help="input text file")
    train.add_argument("-o", "--output", type=Path, default=Path("model.json"))
    train.add_argument(
        "-n", "--order", type=int, default=2, help="chain order (default: 2)"
    )
    train.add_argument(
        "--uniform",
        action="store_true",
        help="ignore word frequencies; pick continuations uniformly",
    )
    train.set_defaults(func=_cmd_train)

    gen = sub.add_parser("generate", help="generate text from a saved model")
    gen.add_argument("model", type=Path, help="saved model JSON file")
    gen.add_argument("--max-words", type=int, default=50)
    gen.add_argument("--count", type=int, default=1, help="how many samples")
    gen.add_argument("--seed", default=None, help="random seed for reproducible output")
    gen.set_defaults(func=_cmd_generate)

    return parser


def _cmd_train(args: argparse.Namespace) -> int:
    model = MarkovModel(order=args.order, weighted=not args.uniform)
    train_on_file(model, args.corpus)
    if not model:
        sys.stderr.write("error: no text found in corpus\n")
        return 1
    args.output.write_text(
        json.dumps(_to_dict(model), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"trained: {model.documents} document(s), "
        f"{model.vocabulary} unique words -> {args.output}"
    )
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    model = _load_model(args.model)
    rng = random.Random(args.seed)
    for _ in range(args.count):
        print(model.generate(max_words=args.max_words, rng=rng))
        print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
