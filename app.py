#!/usr/bin/env python3
"""ממשק Web – מנוע השקעות"""

import sys
from pathlib import Path

# הוספת נתיב הפרויקט – נדרש ל-Streamlit Cloud
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from src.backtest.runner import run_backtest, run_optimization
from src.config.symbols import DEFAULT_SYMBOLS
from src.config.apote_config import HIGH_RISK_SYMBOLS, MEDIUM_RISK_SYMBOLS, LOW_RISK_SYMBOLS


def _symbol_to_level(symbol: str) -> str:
    """מחזיר רמת סיכון לפי סימול"""
    s = str(symbol).upper()
    if s in HIGH_RISK_SYMBOLS:
        return "סיכון גבוה"
    if s in MEDIUM_RISK_SYMBOLS:
        return "סיכון בינוני"
    if s in LOW_RISK_SYMBOLS:
        return "סיכון נמוך"
    return "—"


st.set_page_config(
    page_title="מנוע השקעות",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 מנוע השקעות אוטומטי")
st.subheader("Backtest – בדיקת אסטרטגיה על נתוני עבר")

# תאריך ושעה מלאים – מתי הרצה אחרונה
_run_time = st.session_state.get("last_run_timestamp")
if _run_time:
    st.caption(f"🕐 **רץ אחרון:** {_run_time}")
else:
    st.caption(f"🕐 **זמן עדכון:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- Sidebar: הגדרות ---
with st.sidebar:
    st.header("⚙️ הגדרות")

    symbols_input = st.text_input(
        "מניות/ETF (מופרדות בפסיק)",
        value=", ".join(DEFAULT_SYMBOLS),
        help="לדוגמה: SPY, QQQ, VOO, VTI",
    )
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("תאריך התחלה", value=datetime(2020, 1, 1))
    with col2:
        end_date = st.date_input("תאריך סיום", value=datetime(2024, 12, 31))

    initial_cash = st.number_input(
        "סכום התחלתי ($)",
        min_value=100,
        value=10000,
        step=1000,
    )

    st.divider()
    st.subheader("כלל Stop-Loss")
    stop_loss = st.slider("מכור כשהמחיר ירד ב-%", 5, 50, 25) / 100

    st.subheader("כלל Take-Profit")
    take_profit = st.slider("מכור רווח כשהמחיר עלה ב-%", 5, 50, 20) / 100

    st.subheader("Re-Entry")
    re_entry_days = st.slider("ממתין ימים לפני כניסה מחדש אחרי Stop-Loss", 1, 30, 3)

    st.divider()
    strategy_mode = st.selectbox(
        "מצב אסטרטגיה",
        ["index", "apote"],
        format_func=lambda x: "מקורי (Index + Stop-Loss)" if x == "index" else "APOTE (מפרט מלא)",
        help="APOTE: דירוג נכסים, מצב שוק, ניהול סיכונים, מקטעי סיכון",
    )
    use_cache = st.checkbox("שימוש ב-cache (מהיר יותר)", value=True)

    run_btn = st.button("▶️ הרץ Backtest", type="primary", use_container_width=True)
    optimize_btn = st.button("🎯 אופטימיזציה – מצא פרמטרים אופטימליים", use_container_width=True)
    if st.button("🗑️ נקה תוצאות", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("last_"):
                del st.session_state[k]
        st.rerun()


# --- Main: תוצאות ---
if optimize_btn:
    if not symbols:
        st.error("❌ יש להזין לפחות מניה אחת")
    else:
        with st.spinner("מריץ אופטימיזציה על 27 קומבינציות... (2–5 דקות)"):
            try:
                best_params, best_metrics = run_optimization(
                    symbols=symbols,
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    initial_cash=float(initial_cash),
                    use_cache=use_cache,
                )
                st.session_state["last_metrics"] = best_metrics
                st.session_state["best_params"] = best_params
                st.session_state["optimized"] = True
                st.session_state["last_run_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("✅ אופטימיזציה הושלמה! פרמטרים אופטימליים:")
                st.json({
                    "Stop-Loss": f"{int(best_params.get('stop_loss_pct', 0)*100)}%",
                    "Take-Profit": f"{int(best_params.get('take_profit_pct', 0)*100)}%",
                    "Re-Entry ימים": best_params.get("re_entry_days", 5),
                })
            except Exception as e:
                st.error(f"❌ שגיאה: {e}")
                st.exception(e)

if run_btn:
    if not symbols:
        st.error("❌ יש להזין לפחות מניה אחת")
    else:
        with st.spinner("מריץ backtest... (זה עלול לקחת דקה בפעם הראשונה)"):
            try:
                cerebro, results, metrics = run_backtest(
                    symbols=symbols,
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    initial_cash=float(initial_cash),
                    stop_loss_pct=stop_loss,
                    take_profit_pct=take_profit,
                    re_entry_days=re_entry_days,
                    allocation_per_asset=1.0 / len(symbols),
                    use_cache=use_cache,
                    strategy_mode=strategy_mode,
                )
                st.session_state["last_metrics"] = metrics
                st.session_state["last_results"] = results
                st.session_state["last_cerebro"] = cerebro
                st.session_state["optimized"] = False
                st.session_state["last_run_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("✅ Backtest הושלם בהצלחה!")
            except Exception as e:
                st.error(f"❌ שגיאה: {e}")
                st.exception(e)

if "last_metrics" in st.session_state:
    metrics = st.session_state["last_metrics"]

    if st.session_state.get("optimized"):
        st.info("🎯 **פרמטרים אופטימליים:** " + str(st.session_state.get("best_params", {})))

    st.header("📊 תוצאות")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("ערך התחלתי", f"${metrics.get('initial_value', 0):,.0f}")
    with col2:
        st.metric("ערך סופי", f"${metrics.get('final_value', 0):,.0f}")
    with col3:
        ret = metrics.get("total_return_pct", 0)
        st.metric("תשואה כוללת", f"{ret:.1f}%", delta=f"{ret:.1f}%" if ret else None)
    with col4:
        st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
    with col5:
        st.metric("Max Drawdown", f"{metrics.get('max_drawdown_pct', 0):.1f}%")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("מצב עסקאות")
        trades_df = pd.DataFrame([
            {"מדד": "סה\"כ עסקאות", "ערך": metrics.get("num_trades", 0)},
            {"מדד": "ניצחונות", "ערך": metrics.get("won", 0)},
            {"מדד": "הפסדים", "ערך": metrics.get("lost", 0)},
        ])
        st.dataframe(trades_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("סיכום")
        initial = metrics.get("initial_value", 0)
        final = metrics.get("final_value", 0)
        if initial > 0:
            pct = ((final - initial) / initial) * 100
            st.info(f"התיק צמח מ-${initial:,.0f} ל-${final:,.0f} ({pct:+.1f}%)")

    # גרף עקומת equity
    equity_curve = metrics.get("equity_curve", [])
    if equity_curve:
        df_eq = pd.DataFrame(equity_curve, columns=["תאריך", "שווי"])
        df_eq["תאריך"] = pd.to_datetime(df_eq["תאריך"])
        fig = px.line(df_eq, x="תאריך", y="שווי", title="עקומת שווי התיק")
        fig.update_layout(height=400, margin=dict(l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    # פירוט עסקאות
    trades_detail = metrics.get("trades_detail", [])
    if trades_detail:
        st.subheader("📋 פירוט עסקאות")
        # סיכום לפי רמה
        _levels = [t.get("symbol") for t in trades_detail]
        _level_counts = {}
        for s in _levels:
            lvl = _symbol_to_level(s)
            _level_counts[lvl] = _level_counts.get(lvl, 0) + 1
        if _level_counts:
            st.caption(" | ".join([f"{k}: {v} עסקאות" for k, v in _level_counts.items()]))
        df_trades = pd.DataFrame(trades_detail)

        def _fix_date(val):
            """ממיר תאריך מספרי (737501) לפורמט YYYY-MM-DD"""
            if val is None or (isinstance(val, str) and not val):
                return ""
            if isinstance(val, (int, float)) and 700000 < val < 800000:
                try:
                    return pd.Timestamp.fromordinal(int(val)).strftime("%Y-%m-%d")
                except Exception:
                    pass
            if isinstance(val, str) and len(val) >= 10 and val[:10].replace("-", "").isdigit():
                return val[:10]
            return str(val)[:10] if len(str(val)) >= 10 else str(val)

        if "entry_date" in df_trades.columns:
            df_trades["entry_date"] = df_trades["entry_date"].apply(_fix_date)
        if "exit_date" in df_trades.columns:
            df_trades["exit_date"] = df_trades["exit_date"].apply(_fix_date)

        # הוספת רמת סיכון לכל עסקה
        df_trades["level"] = df_trades["symbol"].apply(_symbol_to_level)

        # הוספת "מה קרה" – מה באמת קרה בהיסטוריה: קניה/מכירה, שיא/שפל, תוצאה
        if "what_happened" not in df_trades.columns:
            def _build_what_happened(row):
                ed = row.get("entry_date") or ""
                exd = row.get("exit_date") or ""
                ep = row.get("entry_price") or 0
                exp = row.get("exit_price") or 0
                pnl = row.get("pnl", 0) or 0
                pct = row.get("pct", 0) or 0
                return f"קניה {ed} ב-${ep:.2f} → מכירה {exd} ב-${exp:.2f}. תוצאה: {'רווח' if pnl >= 0 else 'הפסד'} ${abs(pnl):,.2f} ({pct:+.1f}%)"
            df_trades["what_happened"] = df_trades.apply(_build_what_happened, axis=1)

        # מיפוי עמודות לעברית
        col_map = {
            "symbol": "מוצר",
            "level": "רמה",
            "what_happened": "מה קרה",
            "entry_price": "מחיר קניה",
            "exit_price": "מחיר מכירה",
            "qty": "כמות",
            "cost_buy": "עלות קניה",
            "cost_sell": "עלות מכירה",
            "pnl": "רווח/הפסד",
            "pct": "אחוז",
            "trend": "מגמה",
            "type": "סוג",
            "entry_date": "תאריך קניה",
            "exit_date": "תאריך מכירה",
        }
        df_display = df_trades.rename(columns=col_map)
        # סדר עמודות מועדף – כולל "מה קרה"
        display_cols = ["מוצר", "רמה", "מה קרה", "תאריך קניה", "תאריך מכירה", "מחיר קניה", "מחיר מכירה", "כמות", "עלות קניה", "עלות מכירה", "אחוז", "רווח/הפסד", "מגמה", "סוג"]
        display_cols = [c for c in display_cols if c in df_display.columns]
        df_display = df_display[display_cols]

        # עיצוב וצביעה – Styler (column_config עלול לדרוס צבעים)
        def _color_negative(val):
            if isinstance(val, (int, float)) and val < 0:
                return "color: #dc3545; font-weight: bold"
            return ""

        fmt_dict = {
            "מחיר קניה": "${:.2f}",
            "מחיר מכירה": "${:.2f}",
            "עלות קניה": "${:,.2f}",
            "עלות מכירה": "${:,.2f}",
            "אחוז": "{:+.1f}%",
            "רווח/הפסד": "${:+,.2f}",
        }
        fmt_dict = {k: v for k, v in fmt_dict.items() if k in df_display.columns}
        styled = (
            df_display.style.format(fmt_dict, na_rep="-")
            .map(_color_negative, subset=["אחוז", "רווח/הפסד"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.caption("אין פירוט עסקאות (לא בוצעו מכירות)")

else:
    st.info("👈 בחר הגדרות ולחץ על **הרץ Backtest** כדי להתחיל")

st.divider()
st.caption("מנוע השקעות | Index: Stop-Loss 25% | Take-Profit 20% | APOTE: מפרט מלא")
