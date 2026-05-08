import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CoinRecord:
    symbol: str
    name: str | None = None
    price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    percent_change_24h: float | None = None
    vol_mcap_ratio: float | None = None
    coinglass_url: str | None = None
    source: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "market_cap": self.market_cap,
            "volume_24h": self.volume_24h,
            "percent_change_24h": self.percent_change_24h,
            "vol_mcap_ratio": self.vol_mcap_ratio,
            "coinglass_url": self.coinglass_url,
            "source": self.source,
            **self.extra,
        }


class Source(ABC):
    name: str

    @abstractmethod
    def fetch(self, limit: int = 20) -> list[CoinRecord]: ...


def bybit_tv_url(symbol: str) -> str:
    return f"https://www.coinglass.com/tv/Bybit_{symbol}USDT"
