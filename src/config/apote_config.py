"""
APOTE – Automated Portfolio Optimization Trading Engine
תצורה לפי המפרט המלא
"""

# מבנה תיק – 3 מקטעי סיכון
PORTFOLIO_SEGMENTS = {
    "high_risk": 0.33,
    "medium_risk": 0.33,
    "low_risk": 0.33,
}

# ניהול סיכונים
RISK_MANAGEMENT = {
    "max_trade_risk": 0.01,      # 1% מקסימום סיכון לעסקה
    "max_drawdown": 0.15,        # 15% מקסימום drawdown
    "max_asset_exposure": 0.25,  # מקסימום 25% לנכס בודד
    "atr_stop_multiplier": 2.0,  # מכפיל ATR ל-Stop-Loss דינמי
}

# ביצוע
EXECUTION = {
    "cycles_per_day": 4,
    "order_type_default": "LIMIT",
    "order_type_emergency": "MARKET",
}

# משקלי מומנטום (Return20, Return60, Return120)
MOMENTUM_WEIGHTS = {
    "return_20": 0.5,
    "return_60": 0.3,
    "return_120": 0.2,
}

# מצבי מערכת
class SystemMode:
    AUTO = "AUTO"
    PAUSE = "PAUSE"
    MANUAL = "MANUAL"
    KILL_SWITCH = "KILL_SWITCH"

# נכסים לפי מקטע סיכון (דוגמה – ניתן להרחיב)
HIGH_RISK_SYMBOLS = ["QQQ", "VGT", "XLK"]
MEDIUM_RISK_SYMBOLS = ["SPY", "VOO", "IVV"]
LOW_RISK_SYMBOLS = ["VTI", "BND", "AGG"]

ALL_APOTE_SYMBOLS = list(set(HIGH_RISK_SYMBOLS + MEDIUM_RISK_SYMBOLS + LOW_RISK_SYMBOLS))
