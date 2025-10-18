# app_streamlit.py
import streamlit as st
import pandas as pd
from simulator import MarketSimulator
import plotly.express as px
import time

st.set_page_config(page_title="Fictional Exchange", layout="wide")

st.title("Fictional Stock Exchange — Live Simulation")

# Sidebar controls
with st.sidebar:
    st.header("Simulation settings")
    tickers_text = st.text_area("Tickers (comma separated)", value="AAA,BBB,CCC,DDD")
    tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    start_price = st.number_input("Start price", value=100.0, step=1.0)
    mu = st.number_input("Drift (mu, daily)", value=0.0, format="%.6f")
    sigma = st.number_input("Volatility (sigma, daily)", value=0.02, format="%.6f")
    steps = st.slider("Simulation steps per run", 1, 200, 10)
    tick_speed = st.slider("Auto-tick delay (ms)", 0, 2000, 500)

# Create or reset simulator
if "sim" not in st.session_state or st.button("Reset / (re)start simulator"):
    st.session_state.sim = MarketSimulator(tickers, start_price=start_price, mu=mu, sigma=sigma)
    # advance 1 tick so charts have two points
    st.session_state.sim.step()

# Controls for ticking
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("Step once"):
        st.session_state.sim.step()
with col2:
    if st.button("Step " + str(steps) + " times"):
        for _ in range(steps):
            st.session_state.sim.step()
with col3:
    auto = st.checkbox("Auto-run", value=False)

# Data & charts
df = st.session_state.sim.to_dataframe()
latest = df.groupby("ticker").last().reset_index()
# Leaderboard
st.subheader("Leaderboard (Latest price)")
leader = latest.sort_values("price", ascending=False)
st.table(leader[["ticker", "price"]].set_index("ticker"))

# Multi-select tickers to plot
plot_tickers = st.multiselect("Tickers to plot", options=tickers, default=tickers[:4])
plot_df = df[df["ticker"].isin(plot_tickers)]
fig = px.line(plot_df, x="timestamp", y="price", color="ticker", title="Price history")
st.plotly_chart(fig, use_container_width=True)

# show CSV/Pricing table
if st.checkbox("Show raw data"):
    st.dataframe(df)

# Auto run loop
if auto:
    # run indefinitely until checkbox unchecked — careful!
    while st.session_state.get("auto_running", True):
        st.session_state.sim.step()
        df = st.session_state.sim.to_dataframe()
        fig = px.line(df[df["ticker"].isin(plot_tickers)], x="timestamp", y="price", color="ticker")
        st.plotly_chart(fig, use_container_width=True)
        latest = df.groupby("ticker").last().reset_index().sort_values("price", ascending=False)
        st.table(latest[["ticker", "price"]].set_index("ticker"))
        time.sleep(tick_speed / 1000.0)
        # Streamlit reruns the script; to break you should uncheck "Auto-run" in the UI
        if not st.checkbox("Auto-run (still tick?)", value=True):
            break
