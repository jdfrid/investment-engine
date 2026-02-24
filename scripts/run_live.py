#!/usr/bin/env python3
"""הרצת מנוע הכללים מול חשבון Alpaca – Paper או Live"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.live.runner import run_live_rules


def main():
    import argparse
    p = argparse.ArgumentParser(description="מנוע השקעות – Paper/Live")
    p.add_argument("--live", action="store_true", help="מסחר אמיתי (ברירת מחדל: paper)")
    p.add_argument("--dry-run", action="store_true", help="רק הדפסה, בלי ביצוע פקודות")
    args = p.parse_args()

    paper = not args.live
    if not paper and not args.dry_run:
        confirm = input("⚠️ אתה עומד לבצע מסחר אמיתי. הקלד 'yes' לאישור: ")
        if confirm.lower() != "yes":
            print("בוטל.")
            return

    run_live_rules(paper=paper, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
