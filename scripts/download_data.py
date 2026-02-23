#!/usr/bin/env python3
"""הורדת נתונים מראש ושמירה ב-cache"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.fetcher import fetch_ohlcv
from src.data.storage import save_to_cache
from src.config.symbols import DEFAULT_SYMBOLS


def main():
    print("הורדת נתונים...")
    start = "2020-01-01"
    end = "2024-12-31"
    cache_dir = Path(__file__).parent.parent / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    data = fetch_ohlcv(DEFAULT_SYMBOLS, start, end, progress=True)
    for sym, df in data.items():
        path = save_to_cache(sym, df, str(cache_dir))
        print(f"  {sym}: {len(df)} bars -> {path}")
    print("סיום.")


if __name__ == "__main__":
    main()
