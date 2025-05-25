import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("🚗서울시 공영주차장 요금 추천 서비스")

def format_time(hhmm):
    if pd.isnull(hhmm):
        return "-"
    s = str(hhmm).zfill(4)
    h = int(s[:2])
    m = int(s[2:])
    return f"{h}:{m:02d}"

def calc_fee(row, total_minutes):
    try:
        기본시간 = float(row['기본 주차 시간(분 단위)'])
        기본요금 = float(row['기본 주차 요금'])
        추가단위시간 = float(row['추가 단위 시간(분 단위)'])
        추가단위요금 = float(row['추가 단위 요금'])
        일최대요금 = float(row['일 최대 요금']) if not pd.isnull(row['일 최대 요금']) else None
        total_minutes = float(total_minutes)
    except Exception as e:
        return float('inf')

    # 필수값이 NaN, 0, 음수인 경우 계산 불가
    if any([
        pd.isnull(기본시간), 기본시간 < 0,
        pd.isnull(기본요금), 기본요금 < 0,
        pd.isnull(추가단위시간), 추가단위시간 <= 0,
        pd.isnull(추가단위요금), 추가단위요금 < 0
    ]):
        return float('inf')

    # 기본 시간 이하면 기본요금만
    if total_minutes <= 기본시간:
        fee = 기본요금
    else:
        extra_minutes = total_minutes - 기본시간
        # 추가단위시간 > 0 이 반드시 보장됨
        units = int((extra_minutes + 추가단위시간 - 1) // 추가단위시간)
        fee = 기본요금 + units * 추가단위요금

    # 일최대요금 있으면 적용
    if 일최대요금 and fee > 일최대요금:
        fee = 일최대요금

    return fee



uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding='cp949')
    df = df.dropna(subset=['위도', '경도'])
    df['구'] = df['주소'].apply(lambda x: x.split()[0] if '구' in x else '')

    # 구 선택
    gu_list = sorted(df['구'].unique())
    selected_gu = st.selectbox("구를 선택하세요", gu_list)

    # 필터링
    filtered = df[df['구'] == selected_gu]

    st.markdown("---")
    st.subheader("주차 요금 추천")
    total_minutes = st.number_input("주차할 시간(분)을 입력하세요", min_value=10, step=10, value=60)

    # 요금 계산 및 정렬
    filtered['예상요금'] = filtered.apply(lambda row: calc_fee(row, total_minutes), axis=1)
    filtered = filtered[filtered['예상요금'] != float('inf')]
    filtered = filtered.sort_values('예상요금')
    filtered['추천'] = ""
    if not filtered.empty:
        filtered.iloc[0, filtered.columns.get_loc('추천')] = "⭐️추천"

    st.write(f"총 {len(filtered)}개 주차장 검색됨 (예상 요금 오름차순)")
    st.dataframe(filtered[['추천', '주차장명', '주소', '예상요금', '기본 주차 시간(분 단위)', '기본 주차 요금',
                          '추가 단위 요금', '추가 단위 시간(분 단위)', '일 최대 요금']])

    # 지도
    center_lat = filtered['위도'].astype(float).mean() if not filtered.empty else 37.5665
    center_lon = filtered['경도'].astype(float).mean() if not filtered.empty else 126.9780
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    for _, row in filtered.iterrows():
        tooltip_text = (
            f"총 주차면: {int(row['총 주차면'])}개<br>"
            f"기본 주차 요금: {int(row['기본 주차 요금'])}원 ({int(row['기본 주차 시간(분 단위)'])}분)<br>"
            f"평일: {format_time(row['평일 운영 시작시각(HHMM)'])} ~ {format_time(row['평일 운영 종료시각(HHMM)'])}<br>"
            f"주말: {format_time(row['주말 운영 시작시각(HHMM)'])} ~ {format_time(row['주말 운영 종료시각(HHMM)'])}<br>"
            f"공휴일: {format_time(row['공휴일 운영 시작시각(HHMM)'])} ~ {format_time(row['공휴일 운영 종료시각(HHMM)'])}<br>"
        )
        popup_text = (
            f"<b>{row['주차장명']}</b><br>"
            f"주소: {row['주소']}<br>"
            f"전화번호: {row['전화번호']}<br>"
            f"운영구분: {row['운영구분명']}<br>"
            f"예상요금: {int(row['예상요금'])}원<br>"
            f"기본 주차 시간: {row['기본 주차 시간(분 단위)']}분<br>"
            f"기본 주차 요금: {row['기본 주차 요금']}원<br>"
            f"추가 단위 요금: {row['추가 단위 요금']}원<br>"
            f"추가 단위 시간: {row['추가 단위 시간(분 단위)']}분<br>"
            f"일 최대 요금: {row['일 최대 요금']}"
        )
        folium.Marker(
            location=[float(row['위도']), float(row['경도'])],
            popup=folium.Popup(popup_text, max_width=350, min_width=200),
            tooltip=tooltip_text,
            icon=folium.Icon(color='blue' if row['추천'] == "" else 'red')
        ).add_to(m)

    st_folium(m, width=1000, height=650)
else:
    st.info("서울시 공영주차장 안내 정보 CSV 파일을 업로드해 주세요.")
