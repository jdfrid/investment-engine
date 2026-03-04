"""זיהוי מצב שוק – Risk-On / Risk-Off"""

from enum import Enum
from typing import Optional
import pandas as pd


class MarketRegime(Enum):
    RISK_ON = "risk_on"   # שוק חיובי, תנודתיות מקובלת
    RISK_OFF = "risk_off"  # שוק בירידות או תנודתיות גבוהה


def detect_market_regime(
    prices: pd.Series,
    volatility_pct: Optional[float] = None,
    ma_period: int = 50,
    vol_threshold: float = 0.25,
) -> MarketRegime:
    """
    מזהה מצב שוק לפי מגמה ותנודתיות.
    Risk-On: מגמה חיובית ותנודתיות נמוכה.
    Risk-Off: מגמה שלילית או תנודתיות גבוהה.
    """
    if prices is None or len(prices) < ma_period:
        return MarketRegime.RISK_OFF

    current = float(prices.iloc[-1])
    ma = prices.rolling(ma_period).mean().iloc[-1]
    if pd.isna(ma) or ma <= 0:
        return MarketRegime.RISK_OFF

    # מגמה: מחיר מעל MA = חיובי
    trend_positive = current >= ma

    # תנודתיות: אם לא סופקה, מחשבים מ-20 ימים אחרונים
    if volatility_pct is None:
        returns = prices.pct_change().dropna().tail(20)
        vol = returns.std() * (252 ** 0.5) if len(returns) > 5 else 0.5
        volatility_pct = vol
    vol_acceptable = volatility_pct < vol_threshold

    if trend_positive and vol_acceptable:
        return MarketRegime.RISK_ON
    return MarketRegime.RISK_OFF
