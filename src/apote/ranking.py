"""דירוג נכסים – מומנטום + תנודתיות"""

from typing import Optional, Union
import pandas as pd

from src.config.apote_config import MOMENTUM_WEIGHTS


def _to_prices_df(data: Union[pd.DataFrame, dict]) -> pd.DataFrame:
    """ממיר dict של {symbol: df} ל-DataFrame עם עמודות = symbols"""
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, dict):
        series_list = []
        for sym, df in data.items():
            if df is not None and not df.empty and "close" in df.columns:
                s = df["close"].rename(sym)
                series_list.append(s)
        if not series_list:
            return pd.DataFrame()
        return pd.concat(series_list, axis=1)
    return pd.DataFrame()


def rank_assets(
    data: Union[pd.DataFrame, dict],
    w20: float = None,
    w60: float = None,
    w120: float = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    מדרג נכסים לפי: MomentumScore / Volatility
    Momentum = ממוצע משוקלל של Return20, Return60, Return120
    """
    prices_df = _to_prices_df(data)
    if prices_df.empty:
        return pd.DataFrame()
    w20 = w20 or MOMENTUM_WEIGHTS.get("return_20", 0.5)
    w60 = w60 or MOMENTUM_WEIGHTS.get("return_60", 0.3)
    w120 = w120 or MOMENTUM_WEIGHTS.get("return_120", 0.2)

    results = []
    for col in prices_df.columns:
        s = prices_df[col].dropna()
        if len(s) < 120:
            continue
        try:
            p = float(s.iloc[-1])
            p20 = float(s.iloc[-21]) if len(s) >= 21 else p
            p60 = float(s.iloc[-61]) if len(s) >= 61 else p
            p120 = float(s.iloc[-121]) if len(s) >= 121 else p

            ret20 = (p / p20 - 1) if p20 > 0 else 0
            ret60 = (p / p60 - 1) if p60 > 0 else 0
            ret120 = (p / p120 - 1) if p120 > 0 else 0

            momentum = w20 * ret20 + w60 * ret60 + w120 * ret120
            vol = s.pct_change().tail(60).std()
            vol = max(vol, 1e-8)
            score = momentum / vol
            results.append({"symbol": col, "score": score, "momentum": momentum, "volatility": vol})
        except Exception:
            continue

    df = pd.DataFrame(results)
    if df.empty:
        return df
    df = df.sort_values("score", ascending=False).head(top_n)
    return df.reset_index(drop=True)
