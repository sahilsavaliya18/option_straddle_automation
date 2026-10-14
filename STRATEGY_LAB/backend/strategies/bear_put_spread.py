"""Bear Put Spread — Bearish 2-leg debit spread.
Buy higher-strike PE + Sell lower-strike PE."""

from .base import BaseStrategy, Leg, StrategyMeta


class BearPutSpreadStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="bear_put_spread",
            name="Bear Put Spread",
            category="bearish",
            num_legs=2,
            description=(
                "Buy an ATM Put and sell a lower-strike Put. "
                "A debit spread that profits from a moderate decline in NIFTY."
            ),
            risk_type="defined",
            max_profit="Limited to (spread width - net debit) x quantity",
            max_loss="Net debit paid",
            ideal_iv="moderate",
            ideal_trend="mild_down",
            default_params={"spread_width": 100, "take_profit_pct": 4.0, "stop_loss_pct": 2.0},
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        width = config.get("spread_width", 100)
        offset = config.get("offset_from_spot", 0)
        upper_strike = atm + offset
        lower_strike = upper_strike - width
        return [
            Leg(strike=upper_strike, option_type="PE", direction="BUY"),
            Leg(strike=lower_strike, option_type="PE", direction="SELL"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        if len(legs) != 2:
            return []
        buy_leg, sell_leg = legs[0], legs[1]
        if buy_leg.entry_price <= 0 or sell_leg.entry_price <= 0:
            return []

        net_debit = max(buy_leg.entry_price - sell_leg.entry_price, 0.01)
        lots = int(capital / (net_debit * lot_size))
        if lots <= 0:
            return []

        for leg in legs:
            leg.quantity = lots * lot_size
        return legs
