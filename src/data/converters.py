"""המרת DataFrame לפורמט Backtrader"""

import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import backtrader as bt


def prepare_dataframe_for_backtrader(df: pd.DataFrame) -> pd.DataFrame:
    """
    מוודא ש-DataFrame בפורמט הנדרש:
    - Index: DatetimeIndex
    - Columns: open, high, low, close, volume (lowercase)
    """
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    # נרמול שמות
    col_map = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }
    if "adj close" in df.columns:
        df["close"] = df["adj close"]
    # בחירת עמודות
    needed = ["open", "high", "low", "close", "volume"]
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")
    return df[needed].dropna()


def df_to_backtrader_feed(df: pd.DataFrame):
    """המרת DataFrame ל-PandasData של Backtrader"""
    import backtrader as bt

    df = prepare_dataframe_for_backtrader(df)
    return bt.feeds.PandasData(dataname=df)
