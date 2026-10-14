"""
Strategy registry — central catalog of all implemented strategies.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseStrategy


def get_all_strategies() -> dict[str, "BaseStrategy"]:
    """Return a dict of strategy_id → strategy instance."""
    from .buy_call import BuyCallStrategy
    from .buy_put import BuyPutStrategy
    from .bull_call_spread import BullCallSpreadStrategy
    from .bull_put_spread import BullPutSpreadStrategy
    from .bear_call_spread import BearCallSpreadStrategy
    from .bear_put_spread import BearPutSpreadStrategy
    from .short_straddle import ShortStraddleStrategy
    from .short_strangle import ShortStrangleStrategy
    from .long_straddle import LongStraddleStrategy
    from .long_strangle import LongStrangleStrategy
    from .iron_butterfly import IronButterflyStrategy
    from .iron_condor import IronCondorStrategy

    strategies = [
        BuyCallStrategy(),
        BuyPutStrategy(),
        BullCallSpreadStrategy(),
        BullPutSpreadStrategy(),
        BearCallSpreadStrategy(),
        BearPutSpreadStrategy(),
        ShortStraddleStrategy(),
        ShortStrangleStrategy(),
        LongStraddleStrategy(),
        LongStrangleStrategy(),
        IronButterflyStrategy(),
        IronCondorStrategy(),
    ]

    return {s.meta().id: s for s in strategies}


def get_strategy(strategy_id: str) -> "BaseStrategy":
    """Get a single strategy by ID."""
    all_strats = get_all_strategies()
    if strategy_id not in all_strats:
        raise ValueError(
            f"Unknown strategy '{strategy_id}'. "
            f"Available: {list(all_strats.keys())}"
        )
    return all_strats[strategy_id]


def get_strategies_by_category(category: str) -> dict[str, "BaseStrategy"]:
    """Filter strategies by category."""
    return {
        sid: s for sid, s in get_all_strategies().items()
        if s.meta().category == category
    }
