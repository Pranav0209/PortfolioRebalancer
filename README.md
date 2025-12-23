# 📊 Portfolio Rebalancer

A Streamlit-based tool for quantity-based portfolio replication and drift analysis. Intelligently detects column formats across different brokers using LLM-based auto-detection.

## 🎯 What It Does

Compares a source portfolio (your target allocation) against a target portfolio (current holdings) to:

- ✅ Identify stocks that are **aligned**
- 🔺 Flag **overweight** positions
- 🔻 Flag **underweight** positions  
- ❌ Find **missing** stocks
- ⚠️ Identify **extra** stocks
- 🔄 Generate **buy/sell recommendations** with exact quantities
- 📊 Visualize drift and allocation mismatches
- 🤖 **Auto-detect columns** across different broker CSV formats
- 💰 **Fresh Investment Planning**: Create new portfolios maintaining exact weight percentages

## 💡 Two Modes of Operation

### 1. Rebalance Existing Account
Compare your current holdings against a target allocation to identify buy/sell actions.

### 2. Fresh Investment
Start a new portfolio from scratch while maintaining the exact weight percentages and allocation design from a model portfolio.

## 🔑 Key Principle

**Prices are not required for rebalancing.** Since market prices are identical across accounts at any point in time, they cancel out. Quantity proportions alone determine allocation alignment.

**For fresh investment:** Uses Invested Price (historical buy price) to preserve original portfolio allocation design based on how the model was constructed.

Formula:
```
Weight% = Quantity / Total_Quantity × 100
Drift% = Target_Weight% - Source_Weight%
Fresh_Qty = (Weight% / 100) × Investment_Amount / Invested_Price
```

## 🔄 Multi-Column Quantity Handling

The app automatically detects and sums all relevant quantity columns:
- ✅ Quantity Available
- ✅ Quantity Pledged (Margin)
- ✅ Quantity Pledged (Loan)
- ❌ Excludes: Quantity Discrepant, Quantity Long Term (to avoid double-counting)
- ❌ Filters out debt instruments (SGB prefix - Sovereign Gold Bonds)

## 📁 Project Structure

```
setup.sh              # One-command setup & launch script (recommended)
streamlit_app.py      # Main Streamlit application
loaders.py            # CSV/Excel file parsing + LLM column detection
normalize.py          # Portfolio normalization & weight calculations
allocation.py         # Drift analysis & classification
rebalance.py          # Rebalancing logic & quantity guidance
visuals.py            # Charts and visualizations
config.py             # API key management
requirements.txt      # Python dependencies
.gitignore            # Excludes config file with API key
README.md             # This file
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended) ⭐

```bash
cd /Users/pranavmotamarri/Documents/PortfolioRebalancer
chmod +x setup.sh
./setup.sh
```

This will:
- ✅ Check Python installation
- ✅ Create virtual environment (if needed)
- ✅ Install all dependencies from requirements.txt
- ✅ Start the Streamlit app automatically

### Option 2: Manual Setup

**Step 1:** Get your Groq API Key

The app uses Groq LLM for intelligent column detection. Get a free API key:
- Visit [console.groq.com/keys](https://console.groq.com/keys)
- Sign up (free account)
- Generate your API key

**Step 2:** Install Dependencies

```bash
cd /Users/pranavmotamarri/Documents/PortfolioRebalancer
pip install -r requirements.txt
```

**Step 3:** Run the App

```bash
streamlit run streamlit_app.py
```

### Step 4: Save Your API Key (Both Options)

In the sidebar, paste your Groq API key and click "💾 Save API Key". It will be stored locally and reused for future sessions.

## 📤 Input Format

Both source and target portfolios should be CSV or Excel files. The app will **automatically detect column names** across different broker formats:

**Bio Growth Format:**
```csv
Scrip Name,Net Qty
FILATEX,1738
ROSSARI,239
```

**Zerodha Format:**
```csv
Symbol,ISIN,Sector,Quantity Available,Quantity Pledged (Margin),Quantity Pledged (Loan),...
ADANIENSOL,INE931S01010,ENERGY,0,414,0,...
IRB,INE821I01022,ENGINEERING,0,12844,0,...
```

The app intelligently detects which columns contain symbols and quantities, and automatically sums all quantity columns.

## 🤖 Intelligent Column Detection

The app uses **Groq's Llama 3.3 LLM** to automatically identify the correct columns even with different broker formats:

- **Primary Detection**: Uses LLM to analyze column names and sample data
- **Fallback Detection**: Pattern-based detection if LLM fails
- **Smart Summing**: Automatically combines multiple quantity columns (Available + Pledged Margin + Pledged Loan)
- **Price Detection**: Intelligently identifies price columns with preference for:
  - **Invested Price** (preferred for fresh investment - preserves original allocation design)
  - **Market Price** (current value, useful for market-based comparisons)
  - Manual input option (if no price column found)
- **Cleanup**: Removes debt instruments (SG prefix), duplicates, and invalid entries

### Supported Broker Formats
- ✅ Bio Growth (Scrip Name, Net Qty, Invested Price, Market Price)
- ✅ Zerodha (Symbol, multiple Quantity columns, Average Price)
- ✅ Generic CSV (flexible column names)
- ✅ Excel files

### 1. Drift Analysis Tab
- Complete symbol-by-symbol breakdown
- Source %, Target %, Drift %
- Classification (Aligned / Overweight / Underweight / Missing / Extra)
- Tracking Error metric
- Download drift analysis as CSV

### 2. Rebalance Actions Tab (Rebalance Mode Only)
- Current quantity vs target quantity
- Buy/Sell/Hold recommendations
- Exact number of shares to trade
- Scale factor showing relative portfolio sizes
- Download rebalance actions as CSV

### 3. Fresh Investment Tab (Fresh Investment Mode Only)
- Calculate quantities to buy based on investment amount
- Maintains exact weight percentages from model
- Uses Invested Price to preserve original allocation design
- Shows calculated vs adjusted quantities
- Transparent rounding disclosure
- Download investment plan as CSV

### 4. Visualizations Tab
- **Allocation Comparison**: Source vs Target side-by-side (Rebalance mode)
- **Drift Distribution**: Overweight/underweight by stock
- **Portfolio Health**: Pie chart of status distribution

## 📥 Downloads

After analysis, download results as CSV:
- `drift_analysis.csv` - Complete drift breakdown (all modes)
- `rebalance_actions.csv` - Rebalance recommendations (Rebalance mode only)
- `investment_plan.csv` - Fresh investment quantities (Fresh Investment mode only)

## 🔬 How Analysis Works

### Step 1: Load & Parse with Auto-Detection
- Read CSV/Excel files (handles multiple header rows like Zerodha)
- **Use LLM to detect symbol, quantity, and price columns**
- Automatically sum multiple quantity columns
- Clean symbol names (uppercase, strip whitespace)
- Filter out debt instruments (SG prefix)
- Validate quantities (must be > 0)
- Remove duplicates (keep first)
- Preserve Invested Price for fresh investment (maintains original design)

### Step 2: Normalize
- Calculate total quantity for each portfolio
- Compute weight % for each stock
- Sort by weight descending

### Step 3: Calculate Drift (Rebalance Mode)
For each stock:
```
Drift% = Target_Weight% - Source_Weight%
```

### Step 4: Classify (Rebalance Mode)
- **Aligned**: Drift < 0.01%
- **Overweight**: Drift > 0.01%
- **Underweight**: Drift < -0.01%
- **Missing**: In source but not target
- **Extra**: In target but not source

### Step 5: Rebalancing (Rebalance Mode)
Calculate scale factor:
```
Scale = Total_Target_Qty / Total_Source_Qty
```

For each stock:
```
Target_Qty_Ideal = Source_Qty × Scale
Action_Qty = Target_Qty_Ideal - Current_Target_Qty
```

### Step 5: Fresh Investment (Fresh Investment Mode)
Calculate investment quantities:
```
For each stock:
  Amount = (Weight% / 100) × Investment_Amount
  Calculated_Qty = Amount / Invested_Price
  Target_Qty = round(Calculated_Qty) [minimum 1 if weight > 0]
  Adjusted_Qty = Scale quantities to exactly match investment amount
```

**Note**: Very small weight positions may round to 0 shares. For example:
- At lower investment amounts these positions drop out due to rounding
- Consider manually adding these positions at invested prices for completeness

### Portfolio Health
Tracking Error = √(Σ Drift%²)

Used to measure overall replication quality.

## 💡 Use Cases

1. **Bio Growth → Zerodha (Rebalance)**: Compare ideal Bio Growth allocation to actual Zerodha holdings
2. **Bio Growth → Fresh Investment**: Create new ₹40L+ portfolio exactly matching Bio Growth allocation design
3. **Model Portfolio → New Account**: Replicate model across multiple accounts (same or different amounts)
4. **One Account → Another**: Sync two accounts to same allocations
5. **Drift Monitoring**: Regular checks to keep portfolios aligned
6. **Margin/Pledged Analysis**: Account for both available and pledged quantities
7. **Allocation Preservation**: Use invested prices to maintain original portfolio design rationale

## ⚙️ Configuration

### API Key Management
Your Groq API key is stored locally in `.rebalancer_config.json` (git-ignored):
- **First time**: Paste API key in sidebar → Click "Save API Key"
- **Future sessions**: Key loads automatically
- **Change key**: Click "Clear" → Enter new key → Save

### No Other Configuration Needed
The app auto-detects:
- File format (CSV or Excel)
- Column names (any format)
- Number of stocks
- Quantity ranges
- Multiple quantity columns
- Header rows in CSVs

## 🔒 Safety Notes

- ✅ **No API key issues** → LLM used only for column detection, not data analysis
- ✅ **No live prices required** → Can work without price data for rebalancing
- ✅ **Invested Price preservation** → Fresh investments maintain original design using buy prices
- ✅ **No order placement** → Manual review before trading
- ✅ **No broker auth** → Safe to use with any broker
- ✅ **Quantity-based** → Works across different currency/markets
- ✅ **Local storage** → API key stored locally, not transmitted
- ✅ **Git-safe** → Config file is git-ignored
- ✅ **Price flexibility** → Works with or without price columns; manual input available


## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Column not found" | Check CSV has `symbol` and `quantity` columns |
| "Invalid quantity" | Ensure all quantities are numeric and positive |
| "Empty portfolio" | File may have no valid data rows |
| App won't load files | Try CSV first, then Excel if needed |

## 📝 Example Workflow

### Rebalance Mode
1. Export Bio Growth model as CSV → `source.csv`
2. Export Zerodha holdings as CSV → `target.csv`
3. Open app: `streamlit run streamlit_app.py`
4. Click "📊 Rebalance Existing Account"
5. Paste Groq API key in sidebar (first time only)
6. Upload both files → App auto-detects columns
7. Review Drift Analysis tab
8. Download `rebalance_actions.csv`
9. Execute trades manually in Zerodha
10. Re-upload holdings to confirm alignment ✅

### Fresh Investment Mode
1. Export Bio Growth as CSV → `model.csv`
2. Open app: `streamlit run streamlit_app.py`
3. Click "💰 Fresh Investment"
4. Upload Bio Growth CSV
5. Enter investment amount (e.g., ₹1,00,000)
6. App automatically detects Invested Price for allocation design preservation
7. Review investment plan with exact quantities
8. Download `investment_plan.csv`
9. Place buy orders manually in your broker
10. Successfully replicate allocation! ✅

## 📦 Dependencies

See [requirements.txt](requirements.txt):
- **streamlit** 1.28.1 - Web UI framework
- **pandas** 2.1.3 - Data processing
- **plotly** 5.18.0 - Interactive charts
- **httpx** 0.25.0 - Groq API calls
- **openpyxl** 3.1.5 - Excel support

## 📧 Notes

- This is a **personal portfolio management tool** designed for individual use
- Portfolio data is not stored or transmitted (LLM only sees columns, not data)
- Calculations are deterministic and repeatable
- Works offline except for LLM column detection
- API key is stored locally and not shared

---

**Built for intelligent portfolio management. Works with any broker format.**
