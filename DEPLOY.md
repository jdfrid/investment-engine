# פריסה לאינטרנט – Streamlit Community Cloud

## שלב 1: העלאה ל-GitHub

```bash
cd investment-engine
git add .
git commit -m "Add investment engine for deployment"
git push origin main
```

## שלב 2: חיבור ל-Streamlit Cloud

1. היכנס ל־**[share.streamlit.io](https://share.streamlit.io)**
2. התחבר עם חשבון GitHub
3. לחץ על **"New app"**
4. מלא:
   - **Repository:** `YOUR_USERNAME/investment-engine`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **Advanced settings** (אופציונלי):
     - **Python version:** 3.11 (ברירת מחדל)
5. לחץ **"Deploy!"**

## שלב 3: המתנה לפריסה

הפריסה לוקחת כ־2–5 דקות. בסיום תקבל קישור כמו:

```
https://YOUR-APP-NAME.streamlit.app
```

## עדכונים

כל `git push` ל־main מעדכן את האפליקציה אוטומטית.

## חלופות פריסה

| פלטפורמה | הערות |
|----------|--------|
| **Render** | `web: streamlit run investment-engine/app.py` |
| **Railway** | דומה |
| **Hugging Face Spaces** | `streamlit run app.py` |

---

*האפליקציה רצה חינם ב־Streamlit Cloud (עם הגבלות שימוש).*
