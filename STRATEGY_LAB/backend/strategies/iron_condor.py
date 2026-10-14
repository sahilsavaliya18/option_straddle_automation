"""Iron Condor — 4-leg neutral defined-risk strategy.
Sell inner OTM CE + PE, Buy outer OTM CE + PE."""

from .base import BaseStrategy, Leg, StrategyMeta, TradeEntry
from typing import Optional


class IronCondorStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="iron_condor",
            name="Iron Condor",
            category="other",
            num_legs=4,
            description=(
                "Sell an OTM Call and OTM Put (inner wings), "
                "buy a further OTM Call and Put (outer wings). "
                "Profits in a defined range — defined risk version of short strangle."
            ),
            risk_type="defined",
            max_profit="Net credit received",
            max_loss="Wing width - net credit",
            ideal_iv="high",
            ideal_trend="sideways / range-bound",
            default_params={
                "spread_width": 100,
                "take_profit_pct": 2.0,
                "stop_loss_pct": 1.5,
            },
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        width = config.get("spread_width", 100)
        # Inner strikes (OTM by 'width')
        inner_ce = atm + width
        inner_pe = atm - width
        # Outer strikes (further OTM by another 'width')
        outer_ce = inner_ce + width
        outer_pe = inner_pe - width

        return [
            # Inner (SELL)
            Leg(strike=inner_ce, option_type="CE", direction="SELL"),
            Leg(strike=inner_pe, option_type="PE", direction="SELL"),
            # Outer (BUY)
            Leg(strike=outer_ce, option_type="CE", direction="BUY"),
            Leg(strike=outer_pe, option_type="PE", direction="BUY"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        if len(legs) != 4:
            return []

        for leg in legs:
            if leg.entry_price <= 0:
                return []

        sold_prem = legs[0].entry_price + legs[1].entry_price
        bought_prem = legs[2].entry_price + legs[3].entry_price
        net_credit = sold_prem - bought_prem

        wing_width = legs[2].strike - legs[0].strike
        max_risk = max(wing_width - net_credit, 0.01)

        lots = int(capital / (max_risk * lot_size))
        if lots <= 0:
            return []

        for leg in legs:
            leg.quantity = lots * lot_size
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
