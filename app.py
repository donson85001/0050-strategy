import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt

st.title("🔍 0050 動態配置投資策略模擬器")

# 1. 使用者參數
monthly_invest = st.number_input("每月投入金額 (TWD)", value=35000)
start_year = st.slider("起始年份", min_value=2004, max_value=2024, value=2004)
mom_period = st.slider("動能觀察期 (月)", 3, 24, 12)
vol_period = st.slider("波動觀察期 (月)", 1, 12, 3)
cash_rate = st.slider("閒置資金年利率", 0.0, 0.05, 0.02)

# 2. 取得歷史資料
etf = yf.Ticker("0050.TW")
df = etf.history(period="max", interval="1mo")[["Close"]].dropna()
df = df[df.index.year >= start_year].copy()
df.rename(columns={"Close": "Price"}, inplace=True)

# 3. 計算策略指標
df["Momentum"] = df["Price"].pct_change(mom_period)
df["Volatility"] = df["Price"].pct_change().rolling(vol_period).std()
df["Mom_z"] = (df["Momentum"] - df["Momentum"].rolling(12).mean()) / df["Momentum"].rolling(12).std()
df["Vol_z"] = (df["Volatility"] - df["Volatility"].rolling(12).mean()) / df["Volatility"].rolling(12).std()
df["Weight"] = 1 / (1 + np.exp(-(df["Mom_z"] - df["Vol_z"])))

# 4. 模擬每月投資
shares = 0.0; cash = 0.0
monthly_rate = (1 + cash_rate)**(1/12) - 1
records = []

for dt, row in df.iterrows():
    w = 0 if np.isnan(row.Weight) else row.Weight
    invest = monthly_invest * w
    shares += invest / row.Price
    cash = cash * (1 + monthly_rate) + monthly_invest * (1 - w)
    total = shares * row.Price + cash
    records.append({"Date": dt, "Weight": w, "Total": total})

res = pd.DataFrame(records).set_index("Date")

# 5. 畫圖 & 年報酬 & 回撤分析
st.line_chart(res["Total"])
res["Year"] = res.index.year
ann = res.groupby("Year")["Total"].last().pct_change().fillna(0)
st.subheader("📅 年報酬率")
st.write(ann.apply(lambda x: f"{x:.2%}"))

# 最大回撤
ec = res["Total"].cummax()
dd = (res["Total"] - ec) / ec
max_dd = dd.min()
st.write(f"最大回撤：{max_dd:.2%}")
st.line_chart(dd, use_container_width=True)
