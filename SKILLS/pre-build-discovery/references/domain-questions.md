# Domain-Specific Question Banks

> Use the question bank for your project's domain. Answer every question in
> writing — even if the answer is "not applicable" or "I don't know yet."
> The questions you can't answer are the specification gaps you need to fill.

---

## 🏦 Trading / Finance / Quantitative Projects

### Market Structure
- [ ] What instrument(s) are you trading? (equities, options, futures, forex?)
- [ ] What exchange? What are its trading hours?
- [ ] What is the lot size / contract size?
- [ ] What is the tick size / minimum price movement?
- [ ] What is the expiry cycle? (weekly, monthly, quarterly?)
- [ ] Are there circuit breaker / limit up-down rules?
- [ ] What happens during market holidays — does data exist? Should the system skip them?

### Costs That Eat Into P&L
- [ ] Brokerage per trade (flat or percentage?)
- [ ] Securities Transaction Tax (STT) — different for buy vs sell? Different for options vs futures?
- [ ] GST on brokerage
- [ ] Stamp duty
- [ ] Exchange transaction charges
- [ ] SEBI turnover fees
- [ ] Slippage estimate — what's realistic? (₹0.50? ₹2? ₹5 per lot?)
- [ ] Do you want gross P&L, net P&L, or both displayed?

### Position Sizing & Margin
- [ ] How much capital per trade?
- [ ] How are quantities calculated? (fixed lots, capital-based, risk-based?)
- [ ] For SELL positions: what margin model? (simplified, SPAN-like, broker-specific?)
- [ ] Maximum position size limit?
- [ ] Can the system go to 0 capital mid-day, or does it need a reserve?

### P&L Calculation (CRITICAL)
- [ ] Write the exact formula for BUY leg P&L with a worked example
- [ ] Write the exact formula for SELL leg P&L with a worked example
- [ ] For multi-leg strategies: how is net P&L calculated? Sum of legs?
- [ ] What precision? Round to nearest rupee? Paisa?
- [ ] Is P&L per unit, per lot, or total?

### Entry & Exit Rules
- [ ] What time does trading start? Can you enter at market open or need a delay?
- [ ] What triggers an entry? (fixed time interval, signal, manual?)
- [ ] What triggers an exit? List ALL conditions:
  - Take profit: fixed amount? percentage? trailing?
  - Stop loss: fixed amount? percentage? time-based?
  - Interval/hold time: hard cutoff or soft?
  - Market close: forced exit at what time exactly?
- [ ] Priority order when multiple exit conditions trigger simultaneously?
- [ ] Can the same strike be re-entered after exit?

### Data Quality
- [ ] What is the data frequency? (tick, 1-sec, 1-min, 5-min, daily?)
- [ ] What % of data points are typically missing?
- [ ] What should happen when a price is missing at the exact entry/exit time?
- [ ] Are prices bid, ask, mid, or last traded? Does it matter for your strategy?
- [ ] Is the data adjusted for splits/dividends? Does it need to be?

### Strategy-Specific
- [ ] For each strategy: describe it in plain English (not just the name)
- [ ] How many legs? What type (CE/PE)? What direction (BUY/SELL)?
- [ ] How are strike prices selected? (ATM, OTM by X points, nearest round number?)
- [ ] Are all legs entered simultaneously or sequentially?
- [ ] What happens if one leg of a spread can't be filled (data missing)?

---

## 🌐 Web Application Projects

### Users & Access
- [ ] Who uses this? (just you, your team, public?)
- [ ] Authentication needed? (none, password, OAuth, API key?)
- [ ] Multiple user roles with different permissions?
- [ ] How many concurrent users?

### Data & State
- [ ] What data is stored? Where? (browser, SQLite, Postgres, cloud?)
- [ ] What happens if the database is deleted — is data recoverable?
- [ ] Real-time updates needed, or page refresh is fine?
- [ ] What is the data volume growth rate?

### UI Requirements
- [ ] Desktop-only, mobile-only, or responsive?
- [ ] Dark mode, light mode, or both?
- [ ] What existing dashboards/tools are you trying to match the feel of?
- [ ] What are the 3 most important things a user should see on first load?

### Deployment
- [ ] Local-only, or cloud-deployed?
- [ ] If cloud: what provider? What budget?
- [ ] Custom domain needed?
- [ ] HTTPS required?
- [ ] CI/CD, or manual deploy?

---

## 📊 Data Pipeline Projects

### Sources
- [ ] What are all the data sources? (APIs, files, databases, scraping?)
- [ ] How often does each source update?
- [ ] What authentication is needed for each source?
- [ ] Are there rate limits? What happens if you exceed them?

### Processing
- [ ] What transformations are applied to raw data?
- [ ] What validation checks should run on incoming data?
- [ ] What should happen on validation failure? (skip, default, halt?)
- [ ] Is processing idempotent? (running it twice gives the same result?)

### Storage
- [ ] What is the storage format? (CSV, Parquet, database, JSON?)
- [ ] How long is data retained?
- [ ] What is the expected storage size per day/month/year?
- [ ] Is there a backup strategy?

### Monitoring
- [ ] How do you know the pipeline is working?
- [ ] What alerts should fire? (data missing, job failed, anomaly detected?)
- [ ] Who gets alerted?

---

## 🤖 ML / AI Model Projects

### Problem Definition
- [ ] What is the prediction target? (classification, regression, ranking?)
- [ ] What is the baseline performance? (random guess, current heuristic?)
- [ ] What metric defines success? (accuracy, F1, RMSE, business metric?)
- [ ] What is the minimum acceptable performance?

### Data
- [ ] Training data size? (rows, features, time range)
- [ ] Is the data labeled? How was labeling done?
- [ ] Train/test split strategy? (random, time-based, stratified?)
- [ ] Known data leakage risks?

### Deployment
- [ ] Batch predictions or real-time inference?
- [ ] What latency is acceptable?
- [ ] How often does the model retrain?
- [ ] What happens when the model is wrong?

---

## Universal Questions (Apply to ALL Projects)

### The "What Could Go Wrong" Block
- [ ] What is the WORST thing that could happen if the system gives wrong output?
- [ ] How would you KNOW the output is wrong? (Can you tell by looking, or is it silent?)
- [ ] Is there an existing system you can compare results against?
- [ ] What is the "simplest possible test" to verify the core logic works?

### The "Scope" Block
- [ ] What are 3 things this project MUST do?
- [ ] What are 3 things this project must NOT do?
- [ ] What is the "Version 1" — the smallest useful version?
- [ ] What is "nice to have" vs "must have"?

### The "I'll Know It's Done When" Block
- [ ] Write 3 concrete acceptance criteria:
  - "I can ______ and see ______"
  - "When I input ______, the output is ______"
  - "The system handles ______ by ______"
