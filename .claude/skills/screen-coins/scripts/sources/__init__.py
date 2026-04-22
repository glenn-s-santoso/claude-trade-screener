
from .base import Source
from .cmc import CMCSource
from .coinglass import CoinglassSource
from .santiment import SantimentSource

SOURCES: dict[str, type[Source]] = {
    "cmc": CMCSource,
    "santiment": SantimentSource,
    "coinglass": CoinglassSource,
}
