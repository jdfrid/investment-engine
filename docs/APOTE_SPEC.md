# APOTE – התאמה למפרט

המערכת מותאמת למסמך `automated_trading_system_full_spec_EN.pdf`.

## רכיבים שמומשו

### 1. מבנה תיק (Portfolio Structure)
- **High Risk 33%** – QQQ, VGT, XLK
- **Medium Risk 33%** – SPY, VOO, IVV
- **Low Risk 33%** – VTI, BND, AGG

### 2. זיהוי מצב שוק (Market Regime)
- **Risk-On:** מגמה חיובית (מחיר מעל MA-50), תנודתיות נמוכה
- **Risk-Off:** מגמה שלילית או תנודתיות גבוהה – הפחתת חשיפה לנכסים בסיכון גבוה

### 3. דירוג נכסים (Asset Ranking)
- **Momentum:** Return20 (50%), Return60 (30%), Return120 (20%)
- **Score:** MomentumScore / Volatility
- כניסה רק לנכסים בדירוג העליון

### 4. ניהול סיכונים
- מקסימום סיכון לעסקה: 1%
- מקסימום Drawdown: 15%
- Stop-Loss דינמי לפי ATR (מכפיל 2)
- Trailing Stop: 10%

### 5. כללי כניסה
- נכס ברשימת הדירוג העליון
- מצב שוק מאפשר (ב-Risk-Off לא נכנסים לנכסים בסיכון גבוה)
- מגבלת Drawdown לא חריגה

### 6. כללי יציאה
- היפוך מגמה (מחיר מתחת ל-MA-20)
- Stop-Loss (ATR)
- Trailing Stop

### 7. לוג מלא
- timestamp, symbol, action, quantity, price, reason

### 8. תצורה (Config)
- `src/config/apote_config.py` – כל הפרמטרים

## שימוש

1. **בדשבורד:** בחר "APOTE (מפרט מלא)" במצב אסטרטגיה
2. **Backtest:** הרץ כרגיל – המערכת תטען את כל הנכסים ותריץ את אסטרטגיית APOTE

## הערות
- **מחזורי ביצוע:** במפרט – 4 מחזורים ביום. ב-Backtest עם נתונים יומיים – מחזור אחד ליום
- **סוג פקודה:** במפרט – LIMIT כברירת מחדל. כרגע הברוקר משתמש ב-MARKET (ניתן להרחיב)
- **מצבי מערכת:** AUTO/PAUSE/MANUAL/KILL_SWITCH – מוגדרים ב-config, יישום מלא ב-Live
