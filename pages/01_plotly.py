import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.title("서울특별시 연령별 남녀 인구 피라미드 시각화 (2025년 4월)")

uploaded_file = st.file_uploader("남녀구분 연령별 인구 파일(csv)을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    # 데이터프레임 불러오기 (euc-kr 인코딩)
    df = pd.read_csv(uploaded_file, encoding="euc-kr")
    
    # 서울 전체(첫 행)만 사용
    row = df.iloc[0]
    ages = [f"{i}세" for i in range(0, 100)] + ["100세 이상"]
    male_cols = [col for col in df.columns if "_남_" in col and col.split('_')[-1] in ages]
    female_cols = [col for col in df.columns if "_여_" in col and col.split('_')[-1] in ages]
    age_labels = [col.split('_')[-1] for col in male_cols]
    
    # 숫자 변환 함수
    def to_int(val):
        if isinstance(val, str):
            return int(val.replace(',', ''))
        return int(val)
    male_pop = [to_int(row[c]) for c in male_cols]
    female_pop = [to_int(row[c]) for c in female_cols]

    # Plotly 인구 피라미드
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=age_labels,
        x=[-v for v in male_pop],
        name='남',
        orientation='h',
        marker_color='blue'
    ))
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_pop,
        name='여',
        orientation='h',
        marker_color='pink'
    ))
    fig.update_layout(
        title='서울특별시 연령별 남녀 인구 피라미드 (2025년 4월)',
        barmode='relative',
        xaxis=dict(
            title='인구수',
            tickvals=[-40000, -20000, 0, 20000, 40000, 60000],
            ticktext=[str(abs(v)) for v in [-40000, -20000, 0, 20000, 40000, 60000]],
        ),
        yaxis=dict(title='연령'),
        legend=dict(title='성별'),
        height=900
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("csv 파일을 업로드하면 인구 피라미드가 자동으로 생성됩니다.")

