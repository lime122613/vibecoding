import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

st.title("글로벌 시가총액 TOP10 기업의 최근 1년간 주가 변화")

top10 = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Alphabet (Google)',
    'AMZN': 'Amazon',
    'NVDA': 'Nvidia',
    'META': 'Meta Platforms',
    'BRK-B': 'Berkshire Hathaway',
    'TSLA': 'Tesla',
    'LLY': 'Eli Lilly',
    'TSM': 'TSMC'
}

st.write("조회 기업:")
st.write(", ".join([f"{v}({k})" for k, v in top10.items()]))

end = datetime.today()
start = end - timedelta(days=365)

with st.spinner("데이터를 가져오고 있습니다..."):
    data = yf.download(list(top10.keys()), start=start, end=end)

# "Adj Close"만 추출 (MultiIndex 구조!)
if isinstance(data.columns, pd.MultiIndex):
    data = data.xs('Adj Close', axis=1, level=1)
else:
    data = data["Adj Close"]

data = data.fillna(method="ffill")

fig = go.Figure()
for ticker, name in top10.items():
    if ticker in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data[ticker], mode='lines', name=name
        ))
fig.update_layout(
    title='글로벌 시가총액 TOP10 기업 주가 변화 (최근 1년)',
    xaxis_title='날짜',
    yaxis_title='종가(USD)',
    legend_title='기업명',
    height=600
)
st.plotly_chart(fig, use_container_width=True)
