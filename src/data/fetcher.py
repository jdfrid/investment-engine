"""שליפת נתוני OHLCV מ-yfinance"""

import yfinance as yf
import pandas as pd
from typing import Optional


def fetch_ohlcv(
    symbols: list[str],
    start: str,
    end: str,
    progress: bool = False,
) -> dict[str, pd.DataFrame]:
    """
    מחזיר dict: symbol -> DataFrame עם open, high, low, close, volume.
    """
    data: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        df = yf.download(
            sym,
            start=start,
            end=end,
            progress=progress,
            auto_adjust=True,
            threads=False,
            group_by="ticker",
        )
        if df.empty:
            # נסיון חלופי עם period
            df = yf.download(sym, period="5y", progress=False, auto_adjust=True, threads=False)
        if df.empty:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df = df[sym].copy()
            except (KeyError, TypeError):
                df = df.copy()
        # נרמול שמות עמודות
        df = _normalize_columns(df)
        if not df.empty and "close" in df.columns:
            data[sym] = df
    return data


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """המרת עמודות ל-lowercase והסרת רווחים"""
    df = df.copy()
    df.columns = [str(c).lower().strip() for c in df.columns]
    # להעדיף adj close (מותאם ל-splits/dividends) אם קיים
    if "adj close" in df.columns:
        df["close"] = df["adj close"].copy()
    return df
