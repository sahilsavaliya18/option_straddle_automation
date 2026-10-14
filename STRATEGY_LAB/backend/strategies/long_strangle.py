"""Long Strangle — Buy OTM CE + Buy OTM PE.
Cheaper than straddle but needs bigger move to profit."""

from .base import BaseStrategy, Leg, StrategyMeta
import math


class LongStrangleStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="long_strangle",
            name="Long Strangle",
            category="other",
            num_legs=2,
            description=(
                "Buy an OTM Call and an OTM Put. "
                "Cheaper than a straddle but requires a larger move to profit."
            ),
            risk_type="defined",
            max_profit="Unlimited",
            max_loss="Total premium paid",
            ideal_iv="low",
            ideal_trend="volatile / big move expected",
            default_params={
                "spread_width": 100,
                "take_profit_pct": 5.0,
                "stop_loss_pct": 2.0,
            },
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        width = config.get("spread_width", 100)
        return [
            Leg(strike=atm + width, option_type="CE", direction="BUY"),
            Leg(strike=atm - width, option_type="PE", direction="BUY"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        if len(legs) != 2:
            return []

        leg_capital = capital / 2
        ce_leg, pe_leg = legs[0], legs[1]

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
