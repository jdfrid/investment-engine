# התחברות ל־Alpaca – מדריך הגדרה

## 1. קבלת API Keys

1. היכנס ל־[Alpaca Paper Trading](https://app.alpaca.markets/paper/dashboard/overview)
2. צור חשבון (או התחבר)
3. עבור ל־**API Keys** – צור מפתח חדש
4. שמור את **API Key** וה־**Secret Key** (הסוד מוצג פעם אחת בלבד)

## 2. הגדרת הפרויקט

```bash
cd investment-engine

# יצירת קובץ .env
cp .env.example .env

# ערוך את .env והוסף את המפתחות
# ALPACA_API_KEY=PK...
# ALPACA_API_SECRET=...
```

## 3. הרצת Paper Trading

```bash
# התקנת תלויות (כולל alpaca-py)
pip install -r requirements.txt

# הרצה – Paper בלבד (ברירת מחדל)
python scripts/run_live.py

# בדיקה ללא ביצוע פקודות (dry-run)
python scripts/run_live.py --dry-run
```

## 4. הרצה אוטומטית (Cron / Task Scheduler)

המלצה: הרץ פעם ביום בשעות המסחר (09:30–16:00 Eastern):

**Windows (Task Scheduler):**
```
פעולה: python C:\path\to\investment-engine\scripts\run_live.py
טריגר: מדי יום 10:00
```

**Linux/Mac (cron):**
```cron
0 10 * * 1-5 cd /path/to/investment-engine && python scripts/run_live.py
```

## 5. מעבר ל־Live (כסף אמיתי)

1. פתח חשבון Live ב־[Alpaca Live](https://app.alpaca.markets/live/dashboard/overview)
2. קבל API Keys של Live (לא אותם של Paper)
3. עדכן את `.env` עם מפתחות Live
4. הרץ:
   ```bash
   python scripts/run_live.py --live
   ```
5. תקבל אישור – הקלד `yes` להפעלת מסחר אמיתי

## 6. כללים

- **Stop-Loss:** 25% – מכירה אוטומטית כשהירידה מגיעה ל־25%
- **Take-Profit:** 20% – מכירת הרווח בלבד כש־20% רווח

אפשר לשנות את הערכים ב־`src/config/rules_config.py` או ב־`src/live/runner.py`.
