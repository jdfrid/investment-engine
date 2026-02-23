"""חישוב מדדי ביצועים מתוצאות Backtrader"""

from typing import Any


def compute_metrics(cerebro, results: list) -> dict[str, Any]:
    """מחשב מדדי ביצועים מתוצאות backtest"""
    if not results:
        return {}
    strat = results[0]
    metrics = {
        "initial_value": cerebro.broker.startingcash,
        "final_value": cerebro.broker.getvalue(),
    }
    try:
        sharpe = strat.analyzers.sharpe.get_analysis()
        metrics["sharpe_ratio"] = sharpe.get("sharperatio") or 0
    except Exception:
        metrics["sharpe_ratio"] = 0
    try:
        dd = strat.analyzers.drawdown.get_analysis()
        metrics["max_drawdown_pct"] = dd.get("max", {}).get("drawdown", 0) or 0
        metrics["max_drawdown_len"] = dd.get("max", {}).get("len", 0) or 0
    except Exception:
        metrics["max_drawdown_pct"] = 0
        metrics["max_drawdown_len"] = 0
    try:
        ret = strat.analyzers.returns.get_analysis()
        metrics["total_return_pct"] = (ret.get("rtot", 0) or 0) * 100
    except Exception:
        metrics["total_return_pct"] = 0
    try:
        trades = strat.analyzers.trades.get_analysis()
        total = trades.get("total", {}) or {}
        metrics["num_trades"] = total.get("closed", 0) or 0
        metrics["won"] = total.get("won", 0) or 0
        metrics["lost"] = total.get("lost", 0) or 0
    except Exception:
        metrics["num_trades"] = 0
        metrics["won"] = 0
        metrics["lost"] = 0
    try:
        equity = strat.analyzers.equity.get_analysis()
        metrics["equity_curve"] = equity.get("equity_curve", [])
    except Exception:
        metrics["equity_curve"] = []
    return metrics
