"""markovgen: an order-N Markov chain text generator.

Public API
----------
>>> from markovgen import MarkovChain
>>> chain = MarkovChain(order=2).fit("the cat sat the cat ran")
>>> chain.generate(5)
"""

from .chain import MarkovChain
from .text import tokenize

__all__ = ["MarkovChain", "tokenize"]
__version__ = "0.1.0"
