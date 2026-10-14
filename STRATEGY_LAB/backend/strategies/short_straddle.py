"""Short Straddle — Sell ATM CE + Sell ATM PE.
Profits from low volatility / time decay."""

from .base import BaseStrategy, Leg, StrategyMeta, TradeEntry
from typing import Optional
import math


class ShortStraddleStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="short_straddle",
            name="Short Straddle",
            category="neutral",
            num_legs=2,
            description=(
                "Sell an ATM Call and an ATM Put at the same strike. "
                "Profits from low volatility as both options decay. "
                "Unlimited risk if NIFTY moves sharply."
            ),
            risk_type="undefined",
            max_profit="Total credit received (both premiums)",
            max_loss="Unlimited",
            ideal_iv="high",
            ideal_trend="sideways / range-bound",
            default_params={"take_profit_pct": 2.0, "stop_loss_pct": 1.5, "capital_per_trade": 500000},
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        offset = config.get("offset_from_spot", 0)
        strike = atm - offset
        return [
            Leg(strike=strike, option_type="CE", direction="SELL"),
            Leg(strike=strike, option_type="PE", direction="SELL"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float,
                        lot_size: int, config: dict | None = None) -> list[Leg]:
        """
        For short strategies, use margin-based sizing.
        T3 fix: Uses realistic margin model (~15% of notional) instead of 2x premium.
        """
        if len(legs) != 2:
            return []

        ce_leg, pe_leg = legs[0], legs[1]
        if ce_leg.entry_price <= 0 or pe_leg.entry_price <= 0:
            return []

        config = config or {}
        # Margin per lot = max of the two legs' margin requirements
        ce_margin = self.calc_margin_per_lot(ce_leg, lot_size, config)
        pe_margin = self.calc_margin_per_lot(pe_leg, lot_size, config)
        # For straddle, both legs need margin (but not fully additive — ~1.5x the larger)
        total_margin_per_lot = max(ce_margin, pe_margin) * 1.5
        lots = int(capital / total_margin_per_lot)

        if lots <= 0:
            return []

        ce_leg.quantity = lots * lot_size
        pe_leg.quantity = lots * lot_size
        return legs

    def check_exit(self, trade: TradeEntry, current_prices: dict,
                   config: dict) -> Optional[str]:
        """
        For short strategies, P&L is inverted:
        - Positive P&L = options lost value = good (SELL profits from decay)
        - The base class Leg.pnl already handles direction correctly
        """
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
