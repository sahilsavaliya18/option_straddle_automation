"""Bear Call Spread — Bearish 2-leg credit spread.
Sell lower-strike CE + Buy higher-strike CE."""

from .base import BaseStrategy, Leg, StrategyMeta


class BearCallSpreadStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="bear_call_spread",
            name="Bear Call Spread",
            category="bearish",
            num_legs=2,
            description=(
                "Sell an ATM Call and buy a higher-strike Call. "
                "A credit spread that profits when NIFTY stays below the sold strike."
            ),
            risk_type="defined",
            max_profit="Net credit received",
            max_loss="(Spread width - net credit) x quantity",
            ideal_iv="high",
            ideal_trend="mild_down",
            default_params={"spread_width": 100, "take_profit_pct": 3.0, "stop_loss_pct": 2.0},
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        width = config.get("spread_width", 100)
        offset = config.get("offset_from_spot", 0)
        lower_strike = atm + offset
        upper_strike = lower_strike + width
        return [
            Leg(strike=lower_strike, option_type="CE", direction="SELL"),
            Leg(strike=upper_strike, option_type="CE", direction="BUY"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        if len(legs) != 2:
            return []
        sell_leg, buy_leg = legs[0], legs[1]
        if sell_leg.entry_price <= 0 or buy_leg.entry_price <= 0:
            return []

        width = buy_leg.strike - sell_leg.strike
        net_credit = sell_leg.entry_price - buy_leg.entry_price
        max_risk_per_unit = max(width - net_credit, 0.01)
        lots = int(capital / (max_risk_per_unit * lot_size))
        if lots <= 0:
            return []

        for leg in legs:
            leg.quantity = lots * lot_size
        return legs
