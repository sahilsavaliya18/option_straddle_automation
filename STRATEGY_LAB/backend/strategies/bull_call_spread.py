"""Bull Call Spread — Bullish 2-leg defined-risk strategy.
Buy lower-strike CE + Sell higher-strike CE."""

from .base import BaseStrategy, Leg, StrategyMeta


class BullCallSpreadStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="bull_call_spread",
            name="Bull Call Spread",
            category="bullish",
            num_legs=2,
            description=(
                "Buy an ATM Call and sell a higher-strike Call. "
                "Limited profit and limited loss — a debit spread that profits from a moderate rise."
            ),
            risk_type="defined",
            max_profit="Limited to (spread width - net debit) x quantity",
            max_loss="Net debit paid",
            ideal_iv="moderate",
            ideal_trend="mild_up",
            default_params={"spread_width": 100, "take_profit_pct": 4.0, "stop_loss_pct": 2.0},
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        width = config.get("spread_width", 100)
        offset = config.get("offset_from_spot", 0)
        lower_strike = atm + offset
        upper_strike = lower_strike + width
        return [
            Leg(strike=lower_strike, option_type="CE", direction="BUY"),
            Leg(strike=upper_strike, option_type="CE", direction="SELL"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        if len(legs) != 2:
            return []
        buy_leg = legs[0]
        sell_leg = legs[1]
        if buy_leg.entry_price <= 0 or sell_leg.entry_price <= 0:
            return []

        # Net debit per unit = buy premium - sell premium
        net_debit = max(buy_leg.entry_price - sell_leg.entry_price, 0.01)
        lots = int(capital / (net_debit * lot_size))
        if lots <= 0:
            return []

        for leg in legs:
            leg.quantity = lots * lot_size
        return legs
