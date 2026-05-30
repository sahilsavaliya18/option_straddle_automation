#include "backtest_engine.h"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// ═══════════════════════════════════════════════════════════════════════════════
//  Convert Python dict → Config struct
// ═══════════════════════════════════════════════════════════════════════════════

static Config dict_to_config(const py::dict& d) {
    Config cfg;

    cfg.data_folder       = py::cast<std::string>(d["data_folder"]);
    cfg.expiry_date       = py::cast<std::string>(d["expiry_date"]);
    cfg.market_open       = py::cast<std::string>(d["market_open"]);
    cfg.market_close      = py::cast<std::string>(d["market_close"]);
    cfg.entry_time        = py::cast<std::string>(d["entry_time"]);
    cfg.trade_interval    = py::cast<int>(d["trade_interval"]);
    cfg.hold_minutes      = py::cast<int>(d["hold_minutes"]);
    cfg.lot_size          = py::cast<int>(d["lot_size"]);
    cfg.capital_per_trade = py::cast<double>(d["capital_per_trade"]);
    cfg.leg_capital       = py::cast<double>(d["leg_capital"]);
    cfg.offset_from_spot  = py::cast<int>(d["offset_from_spot"]);
    cfg.take_profit_pct   = py::cast<double>(d["take_profit_pct"]);
    cfg.stop_loss_pct     = py::cast<double>(d["stop_loss_pct"]);
    cfg.tp_rupees         = py::cast<double>(d["tp_rupees"]);
    cfg.sl_rupees         = py::cast<double>(d["sl_rupees"]);

    // No-trade windows: list of [start, end] strings
    py::list nw = d["no_trade_windows"];
    for (auto item : nw) {
        py::tuple tp = py::cast<py::tuple>(item);
        std::string s = py::cast<std::string>(tp[0]);
        std::string e = py::cast<std::string>(tp[1]);
        cfg.no_trade_windows.push_back({to_time(s), to_time(e)});
    }

    return cfg;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Convert TradeResult → Python dict
// ═══════════════════════════════════════════════════════════════════════════════

static py::dict trade_result_to_dict(const TradeResult& tr) {
    py::dict d;
    d["Trade_No"]       = tr.trade_no;
    d["Entry_Time"]     = tr.entry_time;
    d["Exit_Time"]      = tr.exit_time;
    d["Exit_Reason"]    = tr.exit_reason;
    d["ATM_at_Entry"]   = tr.atm_at_entry;
    d["Strike"]         = tr.strike;
    d["CE_Entry"]       = tr.ce_entry;
    d["CE_Exit"]        = tr.ce_exit;
    d["CE_Qty"]         = tr.ce_qty;
    d["CE_PnL"]         = tr.ce_pnl;
    d["PE_Entry"]       = tr.pe_entry;
    d["PE_Exit"]        = tr.pe_exit;
    d["PE_Qty"]         = tr.pe_qty;
    d["PE_PnL"]         = tr.pe_pnl;
    d["Net_PnL"]        = tr.net_pnl;
    d["Cumulative_PnL"] = tr.cumulative_pnl;
    return d;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Module definition
// ═══════════════════════════════════════════════════════════════════════════════

PYBIND11_MODULE(backtest_engine, m) {
    m.doc() = "NIFTY Long Straddle Backtester - C++ accelerated engine";

    m.def("run_backtest", [](const py::dict& config_dict) {
        Config cfg = dict_to_config(config_dict);
        BacktestResult res = run_backtest_cpp(cfg);

        // Convert trades to list of dicts
        py::list trades_list;
        for (const auto& tr : res.trades) {
            trades_list.append(trade_result_to_dict(tr));
        }

        // Convert logs to list of dicts
        py::list logs_list;
        for (const auto& lg : res.logs) {
            py::dict ld;
            ld["message"]  = lg.message;
            ld["is_entry"] = lg.is_entry;
            logs_list.append(ld);
        }

        // Return result dict
        py::dict result_dict;
        result_dict["trades"]         = trades_list;
        result_dict["logs"]           = logs_list;
        result_dict["backtest_date"]  = res.backtest_date;
        result_dict["total_trades"]   = res.total_trades;
        result_dict["wins"]           = res.wins;
        result_dict["losses"]         = res.losses;
        result_dict["avg_pnl"]        = res.avg_pnl;
        result_dict["final_pnl"]      = res.final_pnl;
        return result_dict;
    },
    "Run straddle backtest with C++ engine",
    py::arg("config"));
}
