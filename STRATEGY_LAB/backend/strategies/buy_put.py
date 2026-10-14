"""Buy Put — Bearish single-leg strategy. Buy a PE at/near ATM."""

from .base import BaseStrategy, Leg, StrategyMeta


class BuyPutStrategy(BaseStrategy):

    def meta(self) -> StrategyMeta:
        return StrategyMeta(
            id="buy_put",
            name="Buy Put",
            category="bearish",
            num_legs=1,
            description="Buy an ATM Put option. Profit when NIFTY falls below the strike - premium paid.",
            risk_type="defined",
            max_profit="Substantial (limited by strike going to 0)",
            max_loss="Premium paid",
            ideal_iv="low",
            ideal_trend="strong_down",
            default_params={"take_profit_pct": 5.0, "stop_loss_pct": 2.0},
        )

    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        offset = config.get("offset_from_spot", 0)
        strike = atm + offset
        return [Leg(strike=strike, option_type="PE", direction="BUY")]

    def calc_quantities(self, legs: list[Leg], capital: float, lot_size: int, config: dict | None = None) -> list[Leg]:
        if not legs or legs[0].entry_price <= 0:
            return []
        lots = int(capital / (legs[0].entry_price * lot_size))
        if lots <= 0:
            return []
        legs[0].quantity = lots * lot_size
        return legs
