"""הרצת Backtest"""

import backtrader as bt
import os
import tempfile
from pathlib import Path

from data.fetcher import fetch_ohlcv
from data.storage import save_to_cache, load_from_cache
from data.converters import df_to_backtrader_feed, prepare_dataframe_for_backtrader
from strategy.index_strategy import IndexRulesStrategy
from analysis.metrics import compute_metrics
from backtest.equity_recorder import EquityRecorder

# נתיב cache – בסביבת cloud (read-only) משתמשים ב-/tmp
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CACHE_DIR = _PROJECT_ROOT / "data" / "cache"
try:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    test_file = _CACHE_DIR / ".write_test"
    test_file.touch()
    test_file.unlink()
except (OSError, PermissionError):
    _CACHE_DIR = Path(tempfile.gettempdir()) / "investment_engine_cache"
_DEFAULT_CACHE = str(_CACHE_DIR)


def run_backtest(
    symbols: list[str] | None = None,
    start: str = "2020-01-01",
    end: str = "2024-12-31",
    initial_cash: float = 10000.0,
    stop_loss_pct: float = 0.20,
    take_profit_pct: float = 0.20,
    allocation_per_asset: float = 0.25,
    cache_dir: str | None = None,
    use_cache: bool = True,
    commission: float = 0.0,
) -> tuple[bt.Cerebro, list, dict]:
    """
    מריץ backtest ומחזיר (cerebro, results, metrics).
    """
    if symbols is None:
        symbols = ["SPY", "QQQ", "VOO", "VTI"]
    if cache_dir is None:
        cache_dir = _DEFAULT_CACHE

    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    # טען נתונים
    data_dict = _load_data(symbols, start, end, cache_dir, use_cache)

    for sym, df in data_dict.items():
        feed = df_to_backtrader_feed(df)
        cerebro.adddata(feed, name=sym)

    if not cerebro.datas:
        raise ValueError("No data loaded. Check symbols and date range.")

    cerebro.addstrategy(
        IndexRulesStrategy,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        allocation_per_asset=allocation_per_asset,
    )

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(EquityRecorder, _name="equity")

    results = cerebro.run()
    metrics = compute_metrics(cerebro, results)
    return cerebro, results, metrics


def _load_data(
    symbols: list[str],
    start: str,
    end: str,
    cache_dir: str,
    use_cache: bool,
) -> dict:
    """טוען נתונים מ-cache או מ-yfinance"""
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    data_dict = {}

    for sym in symbols:
        df = None
        if use_cache:
            df = load_from_cache(sym, cache_dir)
            if df is not None and not df.empty:
                try:
                    df = df.loc[start:end]
                except Exception:
                    pass
                if df.empty:
                    df = None

        if df is None or df.empty:
            fetched = fetch_ohlcv([sym], start, end)
            df = fetched.get(sym)
            if df is not None and not df.empty:
                if use_cache:
                    save_to_cache(sym, df, cache_dir)
                data_dict[sym] = df
        else:
            data_dict[sym] = df

    if not data_dict:
        fetched = fetch_ohlcv(symbols, start, end)
        for sym, df in fetched.items():
            if df is not None and not df.empty:
                if use_cache:
                    save_to_cache(sym, df, cache_dir)
                data_dict[sym] = prepare_dataframe_for_backtrader(df)

    return data_dict
