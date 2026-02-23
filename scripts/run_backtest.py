#!/usr/bin/env python3
"""הרצת Backtest – סקריפט ראשי"""

import sys
from pathlib import Path

# הוספת נתיב הפרויקט
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from src.backtest.runner import run_backtest
from src.config.symbols import DEFAULT_SYMBOLS


def main():
    print("=" * 60)
    print("מנוע השקעות – Backtest")
    print("=" * 60)

    cerebro, results, metrics = run_backtest(
        symbols=DEFAULT_SYMBOLS,
        start="2020-01-01",
        end="2024-12-31",
        initial_cash=10000.0,
        stop_loss_pct=0.20,
        take_profit_pct=0.20,
        allocation_per_asset=0.25,
        use_cache=True,
        commission=0.0,
    )

    print("\n--- תוצאות ---")
    print(f"ערך התחלתי:    ${metrics.get('initial_value', 0):,.2f}")
    print(f"ערך סופי:      ${metrics.get('final_value', 0):,.2f}")
    print(f"תשואה כוללת:   {metrics.get('total_return_pct', 0):.2f}%")
    print(f"Sharpe Ratio:  {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown:  {metrics.get('max_drawdown_pct', 0):.2f}%")
    print(f"מספר עסקאות:  {metrics.get('num_trades', 0)} (ניצחונות: {metrics.get('won', 0)}, הפסדים: {metrics.get('lost', 0)})")

    # שמירת plot (אופציונלי – דורש matplotlib)
    # cerebro.plot(savefig="output/plots/backtest_result.png")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
