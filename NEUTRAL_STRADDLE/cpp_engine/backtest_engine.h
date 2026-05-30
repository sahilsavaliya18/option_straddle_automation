#ifndef BACKTEST_ENGINE_H
#define BACKTEST_ENGINE_H

#include <string>
#include <vector>
#include <unordered_map>
#include <cstdint>
#include <cmath>

// ═══════════════════════════════════════════════════════════════════════════
//  Data structures
// ═══════════════════════════════════════════════════════════════════════════

struct SimpleTime {
    int hour;
    int minute;
    SimpleTime() : hour(0), minute(0) {}
    SimpleTime(int h, int m) : hour(h), minute(m) {}
    bool operator>=(const SimpleTime& other) const {
        return (hour * 60 + minute) >= (other.hour * 60 + other.minute);
    }
    bool operator<(const SimpleTime& other) const {
        return (hour * 60 + minute) < (other.hour * 60 + other.minute);
    }
    std::string to_string() const {
        char buf[6];
        snprintf(buf, sizeof(buf), "%02d:%02d", hour, minute);
        return std::string(buf);
    }
};

struct Trade {
    int         trade_num;
    std::string entry_time;       // "HH:MM"
    SimpleTime  hold_deadline;    // time when INTERVAL exit kicks in
    int         atm;
    int         strike;
    double      ec;               // CE entry price
    double      ep;               // PE entry price
    int         qc;               // CE quantity (qty of shares)
    int         qp;               // PE quantity
};

struct TradeResult {
    int         trade_no;
    std::string entry_time;
    std::string exit_time;
    std::string exit_reason;
    int         atm_at_entry;
    int         strike;
    double      ce_entry;
    double      ce_exit;
    int         ce_qty;
    double      ce_pnl;
    double      pe_entry;
    double      pe_exit;
    int         pe_qty;
    double      pe_pnl;
    double      net_pnl;
    double      cumulative_pnl;   // filled after sorting
};

struct Config {
    std::string data_folder;
    std::string expiry_date;
    std::string market_open;      // "09:15"
    std::string market_close;     // "15:30"
    std::string entry_time;       // "09:20"
    int         trade_interval;   // 5
    int         hold_minutes;     // 60
    int         lot_size;         // 65
    double      capital_per_trade; // 100000
    double      leg_capital;       // 50000
    int         offset_from_spot;  // 0
    double      take_profit_pct;   // 3.0
    double      stop_loss_pct;     // 1.0
    double      tp_rupees;         // derived
    double      sl_rupees;         // derived
    std::vector<std::pair<SimpleTime, SimpleTime>> no_trade_windows;
};

struct LogEntry {
    std::string message;
    bool        is_entry;     // true = ENTRY log, false = EXIT/SKIP log
};

// ═══════════════════════════════════════════════════════════════════════════
//  Functions
// ═══════════════════════════════════════════════════════════════════════════

SimpleTime  to_time(const std::string& hhmm);
int         round_to_atm(double spot);
void        calculate_straddle_quantities(double call_price, double put_price,
                                          double leg_capital, int lot_size,
                                          int& qc, int& qp);
bool        in_no_trade_window(const SimpleTime& t, const Config& cfg);

// CSV loaders
std::unordered_map<std::string, double>
            load_spot_data(const std::string& folder, std::string& date_str);

std::unordered_map<std::string, std::pair<double,double>>
            load_strike_data(const std::string& folder, int strike,
                             const std::string& expiry);

// Main engine
struct BacktestResult {
    std::vector<TradeResult>  trades;
    std::vector<LogEntry>     logs;
    std::string               backtest_date;
    int                       total_trades;
    int                       wins;
    int                       losses;
    double                    avg_pnl;
    double                    final_pnl;
};

BacktestResult run_backtest_cpp(const Config& cfg);

#endif // BACKTEST_ENGINE_H
