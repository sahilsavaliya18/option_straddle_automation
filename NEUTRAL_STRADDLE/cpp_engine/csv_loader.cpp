#include "backtest_engine.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <filesystem>
#include <codecvt>
#include <locale>

namespace fs = std::filesystem;

// ═══════════════════════════════════════════════════════════════════════════════
//  Helpers
// ═══════════════════════════════════════════════════════════════════════════════

// Strip BOM and whitespace from beginning of line
static std::string strip_bom(const std::string& s) {
    size_t i = 0;
    // Skip UTF-8 BOM
    if (s.size() >= 3 && s[0] == '\xEF' && s[1] == '\xBB' && s[2] == '\xBF')
        i = 3;
    // Skip whitespace
    while (i < s.size() && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r'))
        i++;
    return s.substr(i);
}

// Split a CSV line by comma — fast, no regex
static std::vector<std::string> split_csv_line(const std::string& line) {
    std::vector<std::string> fields;
    fields.reserve(8);
    size_t start = 0;
    for (size_t i = 0; i <= line.size(); ++i) {
        if (i == line.size() || line[i] == ',') {
            fields.emplace_back(line.substr(start, i - start));
            start = i + 1;
        }
    }
    return fields;
}

// Extract "HH:MM" from various datetime formats:
//   "2026-05-04 09:15:00" → "09:15"
//   "04-05-2026 09:15"    → "09:15"
//   "15-05-2026 09:15"    → "09:15"
static std::string extract_hhmm(const std::string& datetime_str) {
    // Find the space separator between date and time
    size_t space_pos = datetime_str.find(' ');
    if (space_pos == std::string::npos) return "";

    std::string time_part = datetime_str.substr(space_pos + 1);
    // Trim trailing seconds ":00" if present
    if (time_part.size() > 5 && time_part[5] == ':') {
        time_part = time_part.substr(0, 5);
    }
    // Trim whitespace / CR
    while (!time_part.empty() && (time_part.back() == '\r' || time_part.back() == ' '))
        time_part.pop_back();
    return time_part;
}

// Extract date string in "DDMMYYYY" format from datetime
//   "2026-05-04 09:15:00" → "04052026"
//   "04-05-2026 09:15"    → "04052026"
static std::string extract_date_ddmmyyyy(const std::string& datetime_str) {
    size_t space_pos = datetime_str.find(' ');
    std::string date_part = (space_pos != std::string::npos)
        ? datetime_str.substr(0, space_pos) : datetime_str;

    // Determine format: YYYY-MM-DD or DD-MM-YYYY
    std::vector<std::string> parts;
    size_t start = 0;
    for (size_t i = 0; i <= date_part.size(); ++i) {
        if (i == date_part.size() || date_part[i] == '-') {
            parts.emplace_back(date_part.substr(start, i - start));
            start = i + 1;
        }
    }
    if (parts.size() != 3) return "";

    // If first part is 4 digits → YYYY-MM-DD format
    if (parts[0].size() == 4) {
        return parts[2] + parts[1] + parts[0]; // DD + MM + YYYY
    }
    // Otherwise DD-MM-YYYY format
    return parts[0] + parts[1] + parts[2]; // DD + MM + YYYY
}


// ═══════════════════════════════════════════════════════════════════════════════
//  Strike cache
// ═══════════════════════════════════════════════════════════════════════════════

static std::unordered_map<std::string,
    std::unordered_map<std::string, std::pair<double,double>>> strike_cache;


// ═══════════════════════════════════════════════════════════════════════════════
//  load_spot_data
// ═══════════════════════════════════════════════════════════════════════════════

std::unordered_map<std::string, double>
load_spot_data(const std::string& folder, std::string& date_str) {

    // Find NIFTY50_spot_*.csv
    std::vector<fs::path> candidates;
    for (auto& entry : fs::directory_iterator(folder)) {
        if (entry.is_regular_file()) {
            std::string fname = entry.path().filename().string();
            if (fname.find("NIFTY50_spot_") == 0 &&
                fname.size() >= 4 && fname.substr(fname.size()-4) == ".csv") {
                candidates.push_back(entry.path());
            }
        }
    }

    if (candidates.empty()) {
        throw std::runtime_error("No NIFTY50_spot_*.csv found in: " + folder);
    }
    std::sort(candidates.begin(), candidates.end());

    fs::path spot_path = candidates[0];
    std::cout << "  Spot file  ->  " << spot_path.filename().string() << std::endl;

    std::ifstream ifs(spot_path);
    if (!ifs.is_open()) {
        throw std::runtime_error("Cannot open: " + spot_path.string());
    }

    std::unordered_map<std::string, double> prices;
    std::string line;
    bool header_done = false;

    while (std::getline(ifs, line)) {
        line = strip_bom(line);
        if (line.empty()) continue;

        if (!header_done) {
            header_done = true;
            continue;  // skip header row
        }

        auto fields = split_csv_line(line);
        if (fields.size() < 2) continue;

        std::string hhmm = extract_hhmm(fields[0]);
        if (hhmm.empty()) continue;

        double spot_price = std::stod(fields[1]);

        // First row → extract date
        if (date_str.empty()) {
            date_str = extract_date_ddmmyyyy(fields[0]);
        }

        prices[hhmm] = spot_price;
    }

    std::cout << "  Loaded spot data (" << prices.size() << " candles)" << std::endl;
    return prices;
}


// ═══════════════════════════════════════════════════════════════════════════════
//  load_strike_data
// ═══════════════════════════════════════════════════════════════════════════════

std::unordered_map<std::string, std::pair<double,double>>
load_strike_data(const std::string& folder, int strike, const std::string& expiry) {

    std::string cache_key = std::to_string(strike) + "_" + expiry;
    if (strike_cache.find(cache_key) != strike_cache.end()) {
        return strike_cache[cache_key];
    }

    std::string filename = std::to_string(strike) + "_" + expiry + ".csv";
    fs::path filepath = fs::path(folder) / filename;

    if (!fs::exists(filepath)) {
        std::cout << "  Warning: Not found: " << filename << std::endl;
        strike_cache[cache_key] = {};
        return {};
    }

    std::ifstream ifs(filepath);
    if (!ifs.is_open()) {
        std::cout << "  Warning: Cannot open: " << filename << std::endl;
        strike_cache[cache_key] = {};
        return {};
    }

    // Read header to find column indices
    std::string header_line;
    if (!std::getline(ifs, header_line)) {
        strike_cache[cache_key] = {};
        return {};
    }
    header_line = strip_bom(header_line);

    auto header_fields = split_csv_line(header_line);
    int call_idx = -1, put_idx = -1;
    std::string call_col_name = std::to_string(strike) + "CALL";
    std::string put_col_name  = std::to_string(strike) + "PUT";

    for (int i = 0; i < (int)header_fields.size(); ++i) {
        if (header_fields[i] == call_col_name) call_idx = i;
        if (header_fields[i] == put_col_name)  put_idx = i;
    }

    if (call_idx < 0 || put_idx < 0) {
        std::cout << "  Warning: Missing columns in " << filename << std::endl;
        strike_cache[cache_key] = {};
        return {};
    }

    std::unordered_map<std::string, std::pair<double,double>> prices;
    std::string line;

    while (std::getline(ifs, line)) {
        line = strip_bom(line);
        if (line.empty()) continue;

        auto fields = split_csv_line(line);
        if (fields.size() <= (size_t)std::max(call_idx, put_idx)) continue;

        std::string hhmm = extract_hhmm(fields[0]);
        if (hhmm.empty()) continue;

        double call_price = std::stod(fields[call_idx]);
        double put_price  = std::stod(fields[put_idx]);

        prices[hhmm] = {call_price, put_price};
    }

    strike_cache[cache_key] = prices;
    std::cout << "  Loaded  " << filename << "  (" << prices.size() << " candles)" << std::endl;
    return prices;
}
