import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Global Top10 Market Cap Dashboard",
    layout="wide"
)

st.title("🌍 Global Market Cap Top10 Stock Dashboard")
st.markdown("최근 주가 변화를 Plotly로 시각화합니다.")

# 최근 글로벌 시가총액 Top10 (2025 기준)
companies = {
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Apple": "AAPL",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "Broadcom": "AVGO",
    "Tesla": "TSLA",
    "TSMC": "TSM"
}

# Sidebar
st.sidebar.header("설정")

period = st.sidebar.selectbox(
    "기간 선택",
    [
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y"
    ],
    index=3
)

normalize = st.sidebar.checkbox(
    "첫날 가격을 100으로 정규화",
    value=True
)

selected = st.sidebar.multiselect(
    "기업 선택",
    list(companies.keys()),
    default=list(companies.keys())
)

@st.cache_data
def load_data(period):

    df = pd.DataFrame()

    for name, ticker in companies.items():

        try:
            data = yf.download(
                ticker,
                period=period,
                progress=False,
                auto_adjust=True
            )

            df[name] = data["Close"]

        except:
            pass

    return df

price = load_data(period)

price = price[selected]

if normalize:
    price = price / price.iloc[0] * 100

fig = go.Figure()

for company in price.columns:

    fig.add_trace(
        go.Scatter(
            x=price.index,
            y=price[company],
            mode="lines",
            name=company,
            hovertemplate=
            "<b>%{fullData.name}</b><br>" +
            "Date=%{x}<br>" +
            "Value=%{y:.2f}<extra></extra>"
        )
    )

title = "최근 주가 비교"

if normalize:
    title += " (첫날=100)"

fig.update_layout(
    title=title,
    template="plotly_white",
    hovermode="x unified",
    height=700,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    )
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("가격 데이터")

st.dataframe(price.tail(20), use_container_width=True)

returns = (price.iloc[-1] / price.iloc[0] - 1) * 100

result = pd.DataFrame({
    "Return (%)": returns
}).sort_values("Return (%)", ascending=False)

st.subheader("수익률 순위")

st.dataframe(
    result.style.format("{:.2f}%"),
    use_container_width=True
)
