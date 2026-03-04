"""לוג מלא – APOTE"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class LogEntry:
    timestamp: str
    symbol: str
    action: str
    quantity: float
    price: float
    reason: str


class ApoteLogger:
    """רישום כל פעולה – timestamp, symbol, action, quantity, price, reason"""

    def __init__(self):
        self.entries: list[LogEntry] = []

    def log(
        self,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        reason: str,
    ):
        self.entries.append(LogEntry(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            reason=reason,
        ))

    def to_list(self) -> list[dict]:
        return [
            {
                "timestamp": e.timestamp,
                "symbol": e.symbol,
                "action": e.action,
                "quantity": e.quantity,
                "price": e.price,
                "reason": e.reason,
            }
            for e in self.entries
        ]
