#!/usr/bin/env python3
"""ממשק Web – מנוע השקעות"""

import sys
from pathlib import Path

# הוספת נתיב הפרויקט – נדרש ל-Streamlit Cloud
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from backtest.runner import run_backtest
from config.symbols import DEFAULT_SYMBOLS


st.set_page_config(
    page_title="מנוע השקעות",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 מנוע השקעות אוטומטי")
st.subheader("Backtest – בדיקת אסטרטגיה על נתוני עבר")

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
    stop_loss = st.slider("מכור כשהמחיר ירד ב-%", 5, 50, 20) / 100

    st.subheader("כלל Take-Profit")
    take_profit = st.slider("מכור רווח כשהמחיר עלה ב-%", 5, 50, 20) / 100

    st.divider()
    use_cache = st.checkbox("שימוש ב-cache (מהיר יותר)", value=True)

    run_btn = st.button("▶️ הרץ Backtest", type="primary", use_container_width=True)
    if st.button("🗑️ נקה תוצאות", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("last_"):
                del st.session_state[k]
        st.rerun()


# --- Main: תוצאות ---
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
                    allocation_per_asset=1.0 / len(symbols),
                    use_cache=use_cache,
                )
                st.session_state["last_metrics"] = metrics
                st.session_state["last_results"] = results
                st.session_state["last_cerebro"] = cerebro
                st.success("✅ Backtest הושלם בהצלחה!")
            except Exception as e:
                st.error(f"❌ שגיאה: {e}")
                st.exception(e)

if "last_metrics" in st.session_state:
    metrics = st.session_state["last_metrics"]

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

else:
    st.info("👈 בחר הגדרות ולחץ על **הרץ Backtest** כדי להתחיל")

st.divider()
st.caption("מנוע השקעות – Stop-Loss 20% | Take-Profit 20% | מדדים: SPY, QQQ, VOO, VTI")
