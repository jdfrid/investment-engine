# מנוע השקעות אוטומטי – Investment Engine

מערכת backtesting למסחר אוטומטי במדדים מובילים (SPY, QQQ, VOO, VTI) עם כללים:

## 🌐 פריסה לאינטרנט

ראה **[DEPLOY.md](DEPLOY.md)** להוראות פריסה ל־Streamlit Cloud (חינמי).
- **Stop-Loss 20%** – מכירת כל הפוזיציה
- **Take-Profit 20%** – מכירת הרווח בלבד, השארת ההשקעה

## התקנה

```bash
cd investment-engine
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## הרצה

### ממשק Web (מומלץ)

```bash
streamlit run app.py
```

יפתח דפדפן עם דשבורד – הגדרות, הרצת backtest, ותצוגת תוצאות.

### Backtest משורת פקודה

```bash
python scripts/run_backtest.py
```

### הורדת נתונים מראש

```bash
python scripts/download_data.py
```

### בדיקות

```bash
python tests/test_rules_engine.py
```

## מבנה

```
investment-engine/
├── src/
│   ├── data/       # yfinance, cache, converters
│   ├── analysis/   # מדדי ביצועים
│   ├── strategy/   # Rules Engine + Backtrader Strategy
│   ├── backtest/   # Runner
│   └── config/     # symbols, rules
├── scripts/
├── tests/
└── output/
```
