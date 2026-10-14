"""Short Strangle — Sell OTM CE + Sell OTM PE.
Profits from time decay in a range-bound market."""

from .base import BaseStrategy, Leg, StrategyMeta, TradeEntry
from typing import Optional


class ShortStrangleStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="short_strangle",
            name="Short Strangle",
            category="neutral",
            num_legs=2,
            description=(
                "Sell an OTM Call and an OTM Put. "
                "Wider profit zone than short straddle but lower premium collected."
            ),
            risk_type="undefined",
            max_profit="Total credit received",
            max_loss="Unlimited",
            ideal_iv="high",
            ideal_trend="sideways / range-bound",
            default_params={
                "spread_width": 100,
                "take_profit_pct": 2.0,
                "stop_loss_pct": 1.5,
                "capital_per_trade": 500000,
            },
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        width = config.get("spread_width", 100)
        return [
            Leg(strike=atm + width, option_type="CE", direction="SELL"),
            Leg(strike=atm - width, option_type="PE", direction="SELL"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float,
                        lot_size: int, config: dict | None = None) -> list[Leg]:
        """
        For short strangle, use margin-based sizing.
        T3 fix: Uses realistic margin model (~15% of notional) instead of 2x premium.
        """
        if len(legs) != 2:
            return []

        ce_leg, pe_leg = legs[0], legs[1]
        if ce_leg.entry_price <= 0 or pe_leg.entry_price <= 0:
            return []

        config = config or {}
        ce_margin = self.calc_margin_per_lot(ce_leg, lot_size, config)
        pe_margin = self.calc_margin_per_lot(pe_leg, lot_size, config)
        total_margin_per_lot = max(ce_margin, pe_margin) * 1.5
        lots = int(capital / total_margin_per_lot)

        if lots <= 0:
            return []

        ce_leg.quantity = lots * lot_size
        pe_leg.quantity = lots * lot_size
        return legs

    def check_exit(self, trade: TradeEntry, current_prices: dict,
                   config: dict) -> Optional[str]:
        for leg in trade.legs:
            key = (leg.strike, leg.option_type)
            if key in current_prices:
                leg.current_price = current_prices[key]

        net_pnl = trade.net_pnl
        tp = config.get("tp_rupees", 2000)
        sl = config.get("sl_rupees", 1500)

        if net_pnl >= tp:
            return "TAKE_PROFIT"
        if net_pnl <= -sl:
            return "STOP_LOSS"

        return None
