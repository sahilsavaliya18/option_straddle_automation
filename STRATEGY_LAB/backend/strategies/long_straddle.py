"""Long Straddle — Buy ATM CE + Buy ATM PE.
This replicates the existing NEUTRAL_STRADDLE logic for validation."""

from .base import BaseStrategy, Leg, StrategyMeta
import math


class LongStraddleStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="long_straddle",
            name="Long Straddle",
            category="other",
            num_legs=2,
            description=(
                "Buy an ATM Call and an ATM Put at the same strike. "
                "Profits from large moves in either direction. "
                "Identical to the existing NEUTRAL_STRADDLE strategy."
            ),
            risk_type="defined",
            max_profit="Unlimited",
            max_loss="Total premium paid (both legs)",
            ideal_iv="low",
            ideal_trend="volatile / big move expected",
            default_params={"take_profit_pct": 3.0, "stop_loss_pct": 1.0},
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        offset = config.get("offset_from_spot", 0)
        strike = atm - offset
        return [
            Leg(strike=strike, option_type="CE", direction="BUY"),
            Leg(strike=strike, option_type="PE", direction="BUY"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        """Neutral sizing: min of both legs (matches existing C++ engine)."""
        if len(legs) != 2:
            return []

        leg_capital = capital / 2
        ce_leg = legs[0]
        pe_leg = legs[1]

        if ce_leg.entry_price <= 0 or pe_leg.entry_price <= 0:
            return []

        ce_lots = math.floor(leg_capital / ce_leg.entry_price / lot_size)
        pe_lots = math.floor(leg_capital / pe_leg.entry_price / lot_size)
        min_lots = min(ce_lots, pe_lots)

        if min_lots <= 0:
            return []

        ce_leg.quantity = min_lots * lot_size
        pe_leg.quantity = min_lots * lot_size
        return legs
