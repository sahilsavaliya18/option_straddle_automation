"""
Abstract base class for all option strategies.

Every strategy must implement:
  - get_legs()     : define which strikes/types to trade
  - calc_quantities() : how many lots per leg
  - check_exit()   : custom exit logic (TP/SL can be overridden)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Leg:
    """A single option leg in a strategy."""
    strike: int                          # e.g. 24500
    option_type: str                     # "CE" or "PE"
    direction: str                       # "BUY" or "SELL"
    entry_price: float = 0.0
    current_price: float = 0.0
    quantity: int = 0                    # signed: positive for BUY, negative for SELL

    @property
    def pnl(self) -> float:
        """P&L for this leg (positive means profit)."""
        multiplier = 1 if self.direction == "BUY" else -1
        return multiplier * (self.current_price - self.entry_price) * abs(self.quantity)


@dataclass
class TradeEntry:
    """Represents a complete trade (all legs together)."""
    trade_no: int
    entry_time: str                      # "HH:MM"
    legs: list[Leg]
    atm_at_entry: int
    hold_deadline_min: int               # total minutes from midnight

    # Filled on exit
    exit_time: str = ""
    exit_reason: str = ""
    txn_costs: float = 0.0               # Total transaction costs for this trade

    @property
    def gross_pnl(self) -> float:
        """Raw P&L before transaction costs."""
        return sum(leg.pnl for leg in self.legs)

    @property
    def net_pnl(self) -> float:
        """P&L after transaction costs."""
        return self.gross_pnl - self.txn_costs

    @property
    def total_cost(self) -> float:
        """Total capital deployed (absolute)."""
        return sum(abs(leg.entry_price * leg.quantity) for leg in self.legs)


@dataclass
class StrategyMeta:
    """Metadata about a strategy for the registry/UI."""
    id: str                              # "bull_call_spread"
    name: str                            # "Bull Call Spread"
    category: str                        # "bullish" | "bearish" | "neutral" | "other"
    num_legs: int                        # 1, 2, or 4
    description: str = ""
    risk_type: str = "defined"           # "defined" or "undefined"
    max_profit: str = ""                 # e.g. "Unlimited" or "Limited to spread width"
    max_loss: str = ""                   # e.g. "Premium paid" or "Unlimited"
    ideal_iv: str = ""                   # "high" | "low" | "any"
    ideal_trend: str = ""               # "strong_up" | "mild_up" | "sideways" | etc.

    # Default parameters specific to this strategy (override global defaults)
    default_params: dict = field(default_factory=dict)


class BaseStrategy(ABC):
    """
    Abstract base strategy. All 12 strategies inherit from this.

    The engine calls:
      1. get_legs(atm, spot, config) → list of Leg objects defining the trade
      2. calc_quantities(legs, capital, lot_size) → updates leg.quantity
      3. check_exit(trade, current_prices, config) → exit reason or None
    """

    @abstractmethod
    def meta(self) -> StrategyMeta:
        """Return strategy metadata."""
        ...

    @abstractmethod
    def get_legs(self, atm: int, spot: float, config: dict) -> list[Leg]:
        """
        Define the legs for entry.

        Args:
            atm: ATM strike rounded to nearest 50
            spot: exact spot price
            config: strategy configuration dict

        Returns:
            List of Leg objects (entry_price not yet filled — engine fills them)
        """
        ...

    def calc_quantities(self, legs: list[Leg], capital: float,
                        lot_size: int, config: dict | None = None) -> list[Leg]:
        """
        Calculate quantities for each leg based on available capital.
        Default: equal capital split across legs, buy as many lots as affordable.

        For BUY legs: qty = floor(leg_capital / price) rounded to lot_size
        For SELL legs: uses margin model from config
        """
        if not legs:
            return legs

        leg_capital = capital / max(len(legs), 1)
        min_lots: int | None = None

        for leg in legs:
            if leg.entry_price <= 0:
                return []  # can't trade with zero/negative price

            if leg.direction == "SELL" and config and config.get("margin_mode") == "realistic":
                # T3 fix: realistic margin = ~15% of notional per lot
                margin_per_lot = self.calc_margin_per_lot(leg, lot_size, config)
                raw_lots = leg_capital / margin_per_lot if margin_per_lot > 0 else 0
            else:
                raw_lots = leg_capital / (leg.entry_price * lot_size)

            lots = int(raw_lots)
            min_lots = lots if min_lots is None else min(min_lots, lots)

        if min_lots is None or min_lots <= 0:
            return []

        # Assign equal quantity to all legs (ensures balanced position)
        for leg in legs:
            leg.quantity = int(min_lots * lot_size)

        return legs

    @staticmethod
    def calc_margin_per_lot(leg: Leg, lot_size: int, config: dict) -> float:
        """
        Estimate margin required per lot for a SELL position.

        Realistic model: ~15% of notional value (approximating SPAN margin).
        Simple model: 2 × premium × lot_size (original, too low).
        """
        mode = config.get("margin_mode", "realistic")
        if mode == "simple":
            return leg.entry_price * 2 * lot_size

        # Realistic: margin ≈ max(15% of strike × lot_size, 3 × premium × lot_size)
        notional_margin = leg.strike * lot_size * 0.15
        premium_margin = leg.entry_price * 3 * lot_size
        return max(notional_margin, premium_margin)

    @staticmethod
    def calc_txn_costs(trade: 'TradeEntry', config: dict) -> float:
        """
        Calculate total transaction costs for a closed trade.
        Includes: brokerage, STT, exchange charges, GST, stamp duty, SEBI fees, slippage.

        Returns total cost in ₹ (always positive).
        """
        if not config.get("txn_enabled", False):
            return 0.0

        num_legs = len(trade.legs)
        lot_size = config.get("lot_size", 65)
        num_lots = max(abs(trade.legs[0].quantity) // lot_size, 1) if trade.legs else 1

        # Brokerage: flat per order, 2 orders per leg (entry + exit)
        brokerage = config.get("txn_cost_per_order", 20) * num_legs * 2

        # STT: only on sell-side premium at exit
        stt = 0.0
        stt_pct = config.get("txn_stt_sell_pct", 0.05) / 100
        for leg in trade.legs:
            # For options, STT applies on sell side at exercise/exit
            if leg.direction == "SELL":
                stt += leg.entry_price * abs(leg.quantity) * stt_pct  # on premium at entry
            else:
                stt += leg.current_price * abs(leg.quantity) * stt_pct  # on sell at exit

        # Exchange charges on turnover (both entry and exit)
        exchange_pct = config.get("txn_exchange_pct", 0.053) / 100
        turnover = sum(
            (leg.entry_price + leg.current_price) * abs(leg.quantity)
            for leg in trade.legs
        )
        exchange_charges = turnover * exchange_pct

        # GST on (brokerage + exchange charges)
        gst_pct = config.get("txn_gst_pct", 18.0) / 100
        gst = (brokerage + exchange_charges) * gst_pct

        # Stamp duty on buy-side
        stamp_pct = config.get("txn_stamp_buy_pct", 0.003) / 100
        stamp = sum(
            leg.entry_price * abs(leg.quantity) * stamp_pct
            for leg in trade.legs
            if leg.direction == "BUY"
        )

        # SEBI charges
        sebi_pct = config.get("txn_sebi_pct", 0.0001) / 100
        sebi = turnover * sebi_pct

        # Slippage
        slippage = config.get("txn_slippage_per_lot", 1.0) * num_lots * num_legs

        return round(brokerage + stt + exchange_charges + gst + stamp + sebi + slippage, 2)

    def check_exit(self, trade: TradeEntry, current_prices: dict,
                   config: dict) -> Optional[str]:
        """
        Check if trade should exit.

        Args:
            trade: the active TradeEntry
            current_prices: dict mapping (strike, option_type) → current_price
            config: strategy config with tp_rupees, sl_rupees, etc.

        Returns:
            Exit reason string, or None to keep holding.
        """
        # Update current prices on all legs
        for leg in trade.legs:
            key = (leg.strike, leg.option_type)
            if key in current_prices:
                leg.current_price = current_prices[key]

        net_pnl = trade.net_pnl
        tp_rupees = config.get("tp_rupees", 3000)
        sl_rupees = config.get("sl_rupees", 1000)

        if net_pnl >= tp_rupees:
            return "TAKE_PROFIT"
        if net_pnl <= -sl_rupees:
            return "STOP_LOSS"

        return None

    def get_payoff_data(self, atm: int, config: dict) -> list[dict]:
        """
        Generate theoretical payoff diagram data points.
        Returns list of {price, payoff} dicts for charting.
        """
        legs = self.get_legs(atm, float(atm), config)
        # Simulate with 1 lot each for payoff shape
        for leg in legs:
            leg.entry_price = 100.0  # placeholder
            leg.quantity = config.get("lot_size", 65)

        points = []
        for offset in range(-2000, 2001, 50):
            underlying = atm + offset
            total_payoff = 0.0

            for leg in legs:
                if leg.option_type == "CE":
                    intrinsic = max(0, underlying - leg.strike)
                else:
                    intrinsic = max(0, leg.strike - underlying)

                if leg.direction == "BUY":
                    payoff = (intrinsic - leg.entry_price) * leg.quantity
                else:
                    payoff = (leg.entry_price - intrinsic) * leg.quantity

                total_payoff += payoff

            points.append({"price": underlying, "payoff": round(total_payoff, 2)})

        return points
