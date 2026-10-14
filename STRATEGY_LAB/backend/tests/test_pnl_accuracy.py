"""
Unit test suite for P&L calculation accuracy, transaction costs,
margin models, and data quality tracking.
Covers Tigers: T1 (P&L accuracy), T2 (Data quality), T3 (Realistic margin),
T4 (No-trade window default), E1 (Transaction cost model), E2 (Edge cases).
"""

import pytest
import math
from STRATEGY_LAB.backend.strategies.base import Leg, TradeEntry, BaseStrategy
from STRATEGY_LAB.backend.strategies.registry import get_all_strategies, get_strategy
from STRATEGY_LAB.backend.strategies.short_straddle import ShortStraddleStrategy
from STRATEGY_LAB.backend.strategies.short_strangle import ShortStrangleStrategy
from STRATEGY_LAB.backend.strategies.long_straddle import LongStraddleStrategy
from STRATEGY_LAB.backend.strategies.bull_call_spread import BullCallSpreadStrategy
from STRATEGY_LAB.backend.strategies.iron_condor import IronCondorStrategy
from STRATEGY_LAB.backend.config import DEFAULT_PARAMS


# ── T1: P&L Calculation Accuracy ─────────────────────────────────────────────

class TestPnLAccuracy:
    def test_buy_leg_profit_and_loss(self):
        """BUY leg: profit when price rises, loss when price drops."""
        # 1 lot of 65
        leg = Leg(strike=24500, option_type="CE", direction="BUY",
                  entry_price=100.0, current_price=120.0, quantity=65)
        # Profit = (120 - 100) * 65 = +1300
        assert leg.pnl == pytest.approx(1300.0)

        # Loss when price drops to 80
        leg.current_price = 80.0
        assert leg.pnl == pytest.approx(-1300.0)

    def test_sell_leg_profit_and_loss(self):
        """SELL leg: profit when price drops (decay), loss when price rises."""
        leg = Leg(strike=24500, option_type="CE", direction="SELL",
                  entry_price=100.0, current_price=70.0, quantity=65)
        # Profit = -1 * (70 - 100) * 65 = +1950 (decay collected)
        assert leg.pnl == pytest.approx(1950.0)

        # Loss when price surges to 150
        leg.current_price = 150.0
        assert leg.pnl == pytest.approx(-3250.0)

    def test_short_straddle_combined_pnl(self):
        """Short straddle: sell ATM CE and PE. Both decay -> profit on both."""
        ce = Leg(strike=24500, option_type="CE", direction="SELL",
                 entry_price=150.0, current_price=120.0, quantity=65)
        pe = Leg(strike=24500, option_type="PE", direction="SELL",
                 entry_price=130.0, current_price=100.0, quantity=65)
        trade = TradeEntry(trade_no=1, entry_time="09:20", legs=[ce, pe],
                           atm_at_entry=24500, hold_deadline_min=660)

        # CE profit: (150 - 120) * 65 = 1950
        # PE profit: (130 - 100) * 65 = 1950
        # Total gross = 3900
        assert trade.gross_pnl == pytest.approx(3900.0)
        assert trade.net_pnl == pytest.approx(3900.0)  # without txn costs

    def test_iron_condor_4_leg_pnl(self):
        """Iron Condor: 2 short inner legs + 2 long outer protection wings."""
        legs = [
            Leg(strike=24600, option_type="CE", direction="SELL", entry_price=80.0, current_price=50.0, quantity=65),
            Leg(strike=24400, option_type="PE", direction="SELL", entry_price=75.0, current_price=45.0, quantity=65),
            Leg(strike=24700, option_type="CE", direction="BUY", entry_price=40.0, current_price=20.0, quantity=65),
            Leg(strike=24300, option_type="PE", direction="BUY", entry_price=35.0, current_price=15.0, quantity=65),
        ]
        trade = TradeEntry(trade_no=1, entry_time="09:20", legs=legs,
                           atm_at_entry=24500, hold_deadline_min=660)
        # Leg 1 (SELL CE): (80 - 50) * 65 = +1950
        # Leg 2 (SELL PE): (75 - 45) * 65 = +1950
        # Leg 3 (BUY CE):  (20 - 40) * 65 = -1300
        # Leg 4 (BUY PE):  (15 - 35) * 65 = -1300
        # Total = 1950 + 1950 - 1300 - 1300 = +1300
        assert trade.gross_pnl == pytest.approx(1300.0)


# ── E1: Transaction Cost Model ───────────────────────────────────────────────

class TestTransactionCostModel:
    def test_txn_costs_disabled_returns_zero(self):
        trade = TradeEntry(
            trade_no=1, entry_time="09:20",
            legs=[Leg(strike=24500, option_type="CE", direction="BUY", entry_price=100.0, current_price=120.0, quantity=65)],
            atm_at_entry=24500, hold_deadline_min=660,
        )
        cost = BaseStrategy.calc_txn_costs(trade, {"txn_enabled": False})
        assert cost == 0.0

    def test_txn_costs_enabled_computes_all_components(self):
        trade = TradeEntry(
            trade_no=1, entry_time="09:20",
            legs=[
                Leg(strike=24500, option_type="CE", direction="BUY", entry_price=100.0, current_price=110.0, quantity=65),
                Leg(strike=24500, option_type="PE", direction="BUY", entry_price=90.0, current_price=80.0, quantity=65),
            ],
            atm_at_entry=24500, hold_deadline_min=660,
        )
        config = {
            "txn_enabled": True,
            "txn_cost_per_order": 20.0,     # ₹20/order
            "txn_stt_sell_pct": 0.05,       # 0.05% on sell
            "txn_exchange_pct": 0.053,      # 0.053% turnover
            "txn_gst_pct": 18.0,            # 18% on brokerage+exchange
            "txn_stamp_buy_pct": 0.003,     # 0.003% on buy
            "txn_sebi_pct": 0.0001,
            "txn_slippage_per_lot": 1.0,
            "lot_size": 65,
        }
        cost = BaseStrategy.calc_txn_costs(trade, config)
        assert cost > 0.0
        # Brokerage alone is 2 legs * 2 (entry+exit) * 20 = 80
        # Plus GST, STT, exchange, slippage, stamp duty
        assert cost >= 80.0

        # When txn_costs set on trade, net_pnl is properly reduced
        trade.txn_costs = cost
        assert trade.net_pnl == pytest.approx(trade.gross_pnl - cost)


# ── T3: Margin Model for Short Positions ─────────────────────────────────────

class TestMarginModel:
    def test_realistic_margin_vs_simple_margin(self):
        leg = Leg(strike=24500, option_type="CE", direction="SELL", entry_price=100.0)
        lot_size = 65

        simple_margin = BaseStrategy.calc_margin_per_lot(leg, lot_size, {"margin_mode": "simple"})
        # Simple = 100 * 2 * 65 = 13,000
        assert simple_margin == pytest.approx(13000.0)

        realistic_margin = BaseStrategy.calc_margin_per_lot(leg, lot_size, {"margin_mode": "realistic"})
        # Notional = 24500 * 65 * 0.15 = 238,875 (closer to actual SPAN margin of ~1.5 - 2.5 lakhs)
        # Premium margin = 100 * 3 * 65 = 19,500
        # max(238875, 19500) = 238,875
        assert realistic_margin == pytest.approx(238875.0)
        assert realistic_margin > simple_margin

    def test_short_straddle_sizing_with_realistic_margin(self):
        strategy = ShortStraddleStrategy()
        legs = strategy.get_legs(atm=24500, spot=24500.0, config={})
        legs[0].entry_price = 150.0
        legs[1].entry_price = 140.0

        # With 1 lakh capital, realistic margin (~2.4 lakhs * 1.5 = 3.6 lakhs per lot) should allow 0 lots
        sized_legs = strategy.calc_quantities(legs, capital=100000.0, lot_size=65, config={"margin_mode": "realistic"})
        assert sized_legs == []

        # With 5 lakhs capital, should afford 1 lot
        sized_legs = strategy.calc_quantities(legs, capital=500000.0, lot_size=65, config={"margin_mode": "realistic"})
        assert len(sized_legs) == 2
        assert sized_legs[0].quantity == 65
        assert sized_legs[1].quantity == 65


# ── T4: Configuration Defaults ───────────────────────────────────────────────

class TestConfigDefaults:
    def test_default_no_trade_windows_is_empty(self):
        """T4 fix: default no_trade_windows must be empty to avoid blocking 87% of trades."""
        assert DEFAULT_PARAMS.get("no_trade_windows") == []

    def test_transaction_costs_enabled_by_default(self):
        assert DEFAULT_PARAMS.get("txn_enabled") is True
        assert DEFAULT_PARAMS.get("txn_cost_per_order") == 20.0


# ── Registry & Strategy Interface Uniformity ─────────────────────────────────

class TestStrategyRegistry:
    def test_all_12_strategies_registered(self):
        strategies = get_all_strategies()
        assert len(strategies) == 12

    def test_all_strategies_have_valid_metadata_and_signatures(self):
        strategies = get_all_strategies()
        for sid, strat in strategies.items():
            meta = strat.meta()
            assert meta.id == sid
            assert meta.name
            assert meta.category in ("bullish", "bearish", "neutral", "other")
            assert meta.num_legs in (1, 2, 4)

            # Test get_legs returns valid legs
            legs = strat.get_legs(atm=24500, spot=24500.0, config={})
            assert len(legs) == meta.num_legs
            for leg in legs:
                assert leg.strike > 0
                assert leg.option_type in ("CE", "PE")
                assert leg.direction in ("BUY", "SELL")
                leg.entry_price = 100.0

            # Test calc_quantities accepts 4 arguments without error
            sized = strat.calc_quantities(legs, capital=500000.0, lot_size=65, config={})
            assert isinstance(sized, list)
