"""שמירה וטעינה מקומית (cache)"""

from pathlib import Path
import pandas as pd
from typing import Optional


def _ensure_cache_dir(cache_dir: str) -> Path:
    p = Path(cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_to_cache(
    symbol: str,
    df: pd.DataFrame,
    cache_dir: str = "data/cache",
) -> str:
    """שומר DataFrame לקובץ parquet"""
    base = _ensure_cache_dir(cache_dir)
    path = base / f"{symbol}.parquet"
    df.to_parquet(path, index=True)
    return str(path)


def load_from_cache(
    symbol: str,
    cache_dir: str = "data/cache",
) -> Optional[pd.DataFrame]:
    """טוען DataFrame מ-cache אם קיים"""
    path = Path(cache_dir) / f"{symbol}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return None


def get_data_with_cache(
    symbol: str,
    start: str,
    end: str,
    cache_dir: str = "data/cache",
    force_refresh: bool = False,
):
    """
    טוען נתונים מ-cache או מ-yfinance.
    מחזיר DataFrame או None.
    """
    if not force_refresh:
        cached = load_from_cache(symbol, cache_dir)
        if cached is not None:
            # חיתוך לטווח המבוקש
            cached = cached.loc[start:end] if not cached.empty else cached
            if not cached.empty:
                return cached
    # אין cache – נדרש לקרוא מ-fetcher (הקריאה תיעשה ב-runner)
    return None
