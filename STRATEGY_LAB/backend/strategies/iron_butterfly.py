"""Iron Butterfly — 4-leg neutral defined-risk strategy.
Sell ATM CE + Sell ATM PE (body) + Buy OTM CE + Buy OTM PE (wings)."""

from .base import BaseStrategy, Leg, StrategyMeta, TradeEntry
from typing import Optional


class IronButterflyStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="iron_butterfly",
            name="Iron Butterfly",
            category="neutral",
            num_legs=4,
            description=(
                "Sell ATM Call and Put (short straddle body), "
                "buy OTM Call and Put (protective wings). "
                "Defined risk version of short straddle."
            ),
            risk_type="defined",
            max_profit="Net credit received",
            max_loss="Wing width - net credit",
            ideal_iv="high",
            ideal_trend="sideways / low volatility",
            default_params={
                "spread_width": 200,
                "take_profit_pct": 2.5,
                "stop_loss_pct": 1.5,
            },
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        width = config.get("spread_width", 200)
        return [
            # Body (SELL ATM)
            Leg(strike=atm, option_type="CE", direction="SELL"),
            Leg(strike=atm, option_type="PE", direction="SELL"),
            # Wings (BUY OTM)
            Leg(strike=atm + width, option_type="CE", direction="BUY"),
            Leg(strike=atm - width, option_type="PE", direction="BUY"),
        ]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        if len(legs) != 4:
            return []

        for leg in legs:
            if leg.entry_price <= 0:
                return []

        # Net credit = sold premiums - bought premiums
        sold_prem = legs[0].entry_price + legs[1].entry_price
        bought_prem = legs[2].entry_price + legs[3].entry_price
        net_credit = sold_prem - bought_prem

        # Max risk = wing width - net credit (per unit)
        wing_width = legs[2].strike - legs[0].strike  # OTM CE - ATM
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
        tp = config.get("tp_rupees", 2500)
        sl = config.get("sl_rupees", 1500)

        if net_pnl >= tp:
            return "TAKE_PROFIT"
        if net_pnl <= -sl:
            return "STOP_LOSS"

        return None
