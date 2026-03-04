"""כללי כניסה ויציאה – APOTE"""

from enum import Enum
from typing import Optional
import pandas as pd

from .regime import MarketRegime, detect_market_regime
from .ranking import rank_assets
from .risk import RiskManager


class ExitReason(Enum):
    TREND_REVERSAL = "trend_reversal"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    REBALANCE = "rebalance"


def should_enter(
    symbol: str,
    top_ranked: list[str],
    regime: MarketRegime,
    risk_manager: RiskManager,
    portfolio_value: float,
    current_drawdown: float,
) -> tuple[bool, str]:
    """
    כניסה רק אם:
    - הנכס ברשימת הדירוג העליונה
    - מצב השוק מאפשר חשיפה
    - מסנני נזילות מסופקים (מדלגים ב-backtest)
    - מגמה חיובית
    """
    if symbol not in top_ranked:
        return False, "not_in_top_ranked"
    if regime == MarketRegime.RISK_OFF:
        return False, "risk_off"
    if not risk_manager.can_trade(portfolio_value, current_drawdown):
        return False, "drawdown_limit"
    return True, "ok"


def should_exit_trend_reversal(prices: pd.Series, ma_period: int = 20) -> bool:
    """זיהוי היפוך מגמה – מחיר מתחת ל-MA"""
    if prices is None or len(prices) < ma_period:
        return False
    current = float(prices.iloc[-1])
    ma = prices.rolling(ma_period).mean().iloc[-1]
    return pd.notna(ma) and current < ma


def atr_value(high, low, close, period: int = 14) -> float:
    """חישוב ATR – תומך ב-Backtrader lines או pandas Series"""
    try:
        if hasattr(high, "__getitem__"):
            n = min(len(close), period + 5)
            high_s = pd.Series([float(high[-i]) for i in range(n, 0, -1)])
            low_s = pd.Series([float(low[-i]) for i in range(n, 0, -1)])
            close_s = pd.Series([float(close[-i]) for i in range(n, 0, -1)])
        else:
            high_s, low_s, close_s = high, low, close
        if len(close_s) < period:
            return 0.0
        tr1 = high_s - low_s
        tr2 = (high_s - close_s.shift(1)).abs()
        tr3 = (low_s - close_s.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return float(tr.rolling(period).mean().iloc[-1])
    except Exception:
        return 0.0
