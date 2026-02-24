"""הרצת מנוע הכללים מול חשבון Alpaca חי"""

from datetime import datetime
from pathlib import Path

from src.broker.alpaca_client import AlpacaClient
from src.strategy.rules_engine import (
    evaluate_rules,
    RuleAction,
    calc_sell_profit_quantity,
    PositionState,
)


def run_live_rules(
    paper: bool = True,
    rules_config: dict = None,
    dry_run: bool = False,
):
    """
    מריץ את כללי Stop-Loss ו-Take-Profit על פוזיציות פתוחות.
    paper: True = Paper Trading, False = כסף אמיתי
    dry_run: True = רק הדפסה, בלי ביצוע פקודות
    """
    rules_config = rules_config or {
        "stop_loss_pct": 0.25,
        "take_profit_pct": 0.20,
    }
    client = AlpacaClient(paper=paper)

    account = client.get_account()
    positions = client.get_positions()

    mode = "PAPER" if paper else "LIVE"
    print(f"[{datetime.now().isoformat()}] {mode} | Cash: ${account.cash:,.0f} | Equity: ${account.equity:,.0f}")
    print(f"פוזיציות פתוחות: {len(positions)}")

    for pos in positions:
        state = PositionState(
            symbol=pos.symbol,
            entry_price=pos.avg_entry_price,
            current_price=pos.current_price,
            quantity=pos.qty,
            entry_date="",
        )
        action = evaluate_rules(state, rules_config)
        pct = (state.current_price - state.entry_price) / state.entry_price * 100

        if action == RuleAction.HOLD:
            print(f"  {pos.symbol}: HOLD ({pct:+.1f}%)")
            continue

        if action == RuleAction.SELL_ALL:
            if dry_run:
                print(f"  {pos.symbol}: [DRY-RUN] SELL_ALL (Stop-Loss, {pct:+.1f}%)")
            else:
                r = client.close_position(pos.symbol)
                print(f"  {pos.symbol}: SELL_ALL → {r}")
        elif action == RuleAction.SELL_PROFIT:
            qty = calc_sell_profit_quantity(state)
            if qty <= 0:
                continue
            if dry_run:
                print(f"  {pos.symbol}: [DRY-RUN] SELL_PROFIT qty={qty:.4f} ({pct:+.1f}%)")
            else:
                r = client.sell(pos.symbol, qty)
                print(f"  {pos.symbol}: SELL_PROFIT qty={qty:.4f} → {r}")
