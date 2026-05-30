#include "backtest_engine.h"
#include <algorithm>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <chrono>
#include <unordered_set>

// ═══════════════════════════════════════════════════════════════════════════════
//  Helpers
// ═══════════════════════════════════════════════════════════════════════════════

SimpleTime to_time(const std::string& hhmm) {
    int h = std::stoi(hhmm.substr(0, 2));
    int m = std::stoi(hhmm.substr(3, 2));
    return SimpleTime(h, m);
}

int round_to_atm(double spot) {
    return (int)(round(spot / 50.0) * 50.0);
}

void calculate_straddle_quantities(double call_price, double put_price,
                                     double leg_capital, int lot_size,
                                     int& qc, int& qp) {
    if (call_price <= 0 || put_price <= 0) {
        qc = 0; qp = 0;
        return;
    }

    double call_contracts_raw = leg_capital / call_price / lot_size;
    double put_contracts_raw  = leg_capital / put_price  / lot_size;

    int call_floor = (int)std::floor(call_contracts_raw);
    int put_floor  = (int)std::floor(put_contracts_raw);

    int min_qty = std::min(call_floor, put_floor);
    qc = min_qty * lot_size;
    qp = min_qty * lot_size;
}

bool in_no_trade_window(const SimpleTime& t, const Config& cfg) {
    for (auto& [s, e] : cfg.no_trade_windows) {
        if (t >= s && t < e) return true;
    }
    return false;
}

static std::unordered_set<std::string> build_slot_set(const std::string& entry,
                                                        int interval,
                                                        const std::string& close_str) {
    std::unordered_set<std::string> slots;
    SimpleTime base = to_time(entry);
    SimpleTime ceiling = to_time(close_str);
    int total_min_base    = base.hour * 60 + base.minute;
    int total_min_ceiling = ceiling.hour * 60 + ceiling.minute;
    for (int m = total_min_base; m < total_min_ceiling; m += interval) {
        int h = m / 60;
        int mi = m % 60;
        char buf[6];
        snprintf(buf, sizeof(buf), "%02d:%02d", h, mi);
        slots.emplace(buf);
    }
    return slots;
}


// ═══════════════════════════════════════════════════════════════════════════════
//  run_backtest_cpp — Main simulation engine
// ═══════════════════════════════════════════════════════════════════════════════

BacktestResult run_backtest_cpp(const Config& cfg) {

    auto start_time = std::chrono::high_resolution_clock::now();

    BacktestResult result;

    // ── Load spot data ──────────────────────────────────────────────────────
    std::string backtest_date;
    auto spot_prices = load_spot_data(cfg.data_folder, backtest_date);
    result.backtest_date = backtest_date;

    // ── Build timeline ──────────────────────────────────────────────────────
    SimpleTime open_t  = to_time(cfg.market_open);
    SimpleTime close_t = to_time(cfg.market_close);

    std::vector<std::string> timeline;
    int total_open  = open_t.hour * 60 + open_t.minute;
    int total_close = close_t.hour * 60 + close_t.minute;
    for (int m = total_open; m <= total_close; ++m) {
        int h = m / 60;
        int mi = m % 60;
        char buf[6];
        snprintf(buf, sizeof(buf), "%02d:%02d", h, mi);
        timeline.emplace_back(buf);
    }

    // ── Build slot set ──────────────────────────────────────────────────────
    auto slot_set   = build_slot_set(cfg.entry_time, cfg.trade_interval, cfg.market_close);
    SimpleTime entry_from = to_time(cfg.entry_time);

    // ── Simulation ──────────────────────────────────────────────────────────
    std::vector<Trade> open_trades;
    int trade_num = 0;

    for (const auto& minute_str : timeline) {
        SimpleTime cur_t    = to_time(minute_str);
        bool       is_slot  = slot_set.find(minute_str) != slot_set.end();
        bool       is_close = cur_t >= close_t;

        // ── Check exits ────────────────────────────────────────────────────
        std::vector<Trade> still_open;
        for (const auto& trade : open_trades) {
            auto strike_data = load_strike_data(cfg.data_folder, trade.strike, cfg.expiry_date);
            auto it = strike_data.find(minute_str);
            double c = (it != strike_data.end()) ? it->second.first : trade.ec;
            double p = (it != strike_data.end()) ? it->second.second : trade.ep;

            double pnl = (c - trade.ec) * trade.qc + (p - trade.ep) * trade.qp;
            bool held_long_enough = cur_t >= trade.hold_deadline;

            std::string reason = "";
            if (is_close) {
                reason = "MARKET_CLOSE";
            } else if (pnl >= cfg.tp_rupees) {
                reason = "TAKE_PROFIT";
            } else if (pnl <= -cfg.sl_rupees) {
                reason = "STOP_LOSS";
            } else if (held_long_enough) {
                reason = "INTERVAL";
            }

            if (!reason.empty()) {
                TradeResult tr;
                tr.trade_no      = trade.trade_num;
                tr.entry_time    = trade.entry_time;
                tr.exit_time     = minute_str;
                tr.exit_reason   = reason;
                tr.atm_at_entry  = trade.atm;
                tr.strike        = trade.strike;
                tr.ce_entry      = trade.ec;
                tr.ce_exit       = c;
                tr.ce_qty        = trade.qc;
                tr.ce_pnl        = std::round((c - trade.ec) * trade.qc * 100.0) / 100.0;
                tr.pe_entry      = trade.ep;
                tr.pe_exit       = p;
                tr.pe_qty        = trade.qp;
                tr.pe_pnl        = std::round((p - trade.ep) * trade.qp * 100.0) / 100.0;
                tr.net_pnl       = std::round(pnl * 100.0) / 100.0;
                tr.cumulative_pnl = 0; // recalculated later
                result.trades.push_back(tr);

                // Log
                std::ostringstream oss;
                oss << "[" << std::setw(3) << trade.trade_num << "]  "
                    << trade.entry_time << " -> " << minute_str << "  "
                    << std::left << std::setw(14) << reason << "  P&L: "
                    << (pnl >= 0 ? "+" : "") << "Rs" << std::fixed << std::setprecision(0)
                    << pnl;
                result.logs.push_back(LogEntry{oss.str(), false});
            } else {
                still_open.push_back(trade);
            }
        }
        open_trades = still_open;

        // ── New Trade Entry ─────────────────────────────────────────────────
        if (!is_slot || cur_t < entry_from || is_close) continue;
        if (in_no_trade_window(cur_t, cfg)) {
            result.logs.push_back(LogEntry{minute_str + "  SLOT SKIPPED -- inside no-trade window", false});
            continue;
        }

        auto spot_it = spot_prices.find(minute_str);
        if (spot_it == spot_prices.end()) {
            result.logs.push_back(LogEntry{minute_str + "  SLOT SKIPPED -- no spot data", false});
            continue;
        }
        double spot = spot_it->second;

        int atm    = round_to_atm(spot);
        int strike = atm - cfg.offset_from_spot;

        auto strike_data = load_strike_data(cfg.data_folder, strike, cfg.expiry_date);
        auto pr_it = strike_data.find(minute_str);
        if (pr_it == strike_data.end()) {
            result.logs.push_back(LogEntry{minute_str + "  SLOT SKIPPED -- no option data for " + std::to_string(strike), false});
            continue;
        }

        double ec = pr_it->second.first;
        double ep = pr_it->second.second;

        int qc, qp;
        calculate_straddle_quantities(ec, ep, cfg.leg_capital, cfg.lot_size, qc, qp);

        if (qc == 0 && qp == 0) {
            result.logs.push_back(LogEntry{minute_str + "  SLOT SKIPPED -- all quantities 0", false});;
            continue;
        }

        // Calculate hold deadline
        int entry_total_min = cur_t.hour * 60 + cur_t.minute + cfg.hold_minutes;
        SimpleTime hold_deadline(entry_total_min / 60, entry_total_min % 60);

        trade_num++;
        Trade new_trade;
        new_trade.trade_num     = trade_num;
        new_trade.entry_time    = minute_str;
        new_trade.hold_deadline = hold_deadline;
        new_trade.atm           = atm;
        new_trade.strike        = strike;
        new_trade.ec            = ec;
        new_trade.ep            = ep;
        new_trade.qc            = qc;
        new_trade.qp            = qp;
        open_trades.push_back(new_trade);

        // Log entry
        std::ostringstream oss;
        oss << "[" << std::setw(3) << trade_num << "]  ENTRY  " << minute_str
            << "  Spot=" << std::fixed << std::setprecision(1) << spot
            << "  ATM=" << atm << "  Strike=" << strike
            << "\n         CE=" << std::fixed << std::setprecision(2) << ec
            << " x " << qc << "   |   PE=" << ep << " x " << qp;
        result.logs.push_back(LogEntry{oss.str(), true});
    }

    // ── Force close remaining open trades ──────────────────────────────────
    std::string last_min = timeline.back();
    for (const auto& trade : open_trades) {
        auto strike_data = load_strike_data(cfg.data_folder, trade.strike, cfg.expiry_date);
        auto it = strike_data.find(last_min);
        double c = (it != strike_data.end()) ? it->second.first : trade.ec;
        double p = (it != strike_data.end()) ? it->second.second : trade.ep;
        double pnl = (c - trade.ec) * trade.qc + (p - trade.ep) * trade.qp;

        TradeResult tr;
        tr.trade_no      = trade.trade_num;
        tr.entry_time    = trade.entry_time;
        tr.exit_time     = last_min;
        tr.exit_reason   = "MARKET_CLOSE";
        tr.atm_at_entry  = trade.atm;
        tr.strike        = trade.strike;
        tr.ce_entry      = trade.ec;
        tr.ce_exit       = c;
        tr.ce_qty        = trade.qc;
        tr.ce_pnl        = std::round((c - trade.ec) * trade.qc * 100.0) / 100.0;
        tr.pe_entry      = trade.ep;
        tr.pe_exit       = p;
        tr.pe_qty        = trade.qp;
        tr.pe_pnl        = std::round((p - trade.ep) * trade.qp * 100.0) / 100.0;
        tr.net_pnl       = std::round(pnl * 100.0) / 100.0;
        tr.cumulative_pnl = 0;
        result.trades.push_back(tr);

        std::ostringstream oss;
        oss << "[" << std::setw(3) << trade.trade_num << "]  "
            << trade.entry_time << " -> " << last_min << "  MARKET_CLOSE    P&L: "
            << (pnl >= 0 ? "+" : "") << "Rs" << std::fixed << std::setprecision(0)
            << pnl;
        result.logs.push_back({oss.str(), false});
    }

    // ── Final Processing: Sort + Recalculate Cumulative PnL ────────────────
    if (!result.trades.empty()) {
        // Sort by Entry_Time
        std::sort(result.trades.begin(), result.trades.end(),
            [](const TradeResult& a, const TradeResult& b) {
                return a.entry_time < b.entry_time;
            });

        // Renumber Trade_No
        double cum_pnl = 0.0;
        for (int i = 0; i < (int)result.trades.size(); ++i) {
            result.trades[i].trade_no = i + 1;
            cum_pnl += result.trades[i].net_pnl;
            result.trades[i].cumulative_pnl = std::round(cum_pnl * 100.0) / 100.0;
        }

        result.total_trades = (int)result.trades.size();
        result.wins   = 0;
        result.losses = 0;
        double sum_pnl = 0.0;
        for (const auto& t : result.trades) {
            sum_pnl += t.net_pnl;
            if (t.net_pnl > 0) result.wins++;
            else if (t.net_pnl < 0) result.losses++;
        }
        result.avg_pnl   = sum_pnl / result.total_trades;
        result.final_pnl = cum_pnl;
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    double elapsed_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
    std::cout << "  C++ engine elapsed: " << std::fixed << std::setprecision(1)
              << elapsed_ms << " ms" << std::endl;

    return result;
}
