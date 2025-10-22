import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("🚗서울시 공영주차장 요금 추천앱🪄")
def format_time(hhmm): 
    if pd.isnull(hhmm): 
        return "-" 
    s = str(hhmm).zfill(4) 
    h = int(s[:2]) 
    m = int(s[2:]) 
    return f"{h}:{m:02d}"

def calc_fee(row, total_minutes, day_type):
    # 요일별 컬럼명 매핑
    if day_type == "평일":
        base_time_col = '기본 주차 시간(분 단위)'
        base_fee_col = '기본 주차 요금'
        add_unit_time_col = '추가 단위 시간(분 단위)'
        add_unit_fee_col = '추가 단위 요금'
        max_fee_col = '일 최대 요금'
    elif day_type == "토요일":
        base_time_col = '토요일 기본 주차 시간(분 단위)'
        base_fee_col = '토요일 기본 주차 요금'
        add_unit_time_col = '토요일 추가 단위 시간(분 단위)'
        add_unit_fee_col = '토요일 추가 단위 요금'
        max_fee_col = '토요일 일 최대 요금'
    else:  # 공휴일
        base_time_col = '공휴일 기본 주차 시간(분 단위)'
        base_fee_col = '공휴일 기본 주차 요금'
        add_unit_time_col = '공휴일 추가 단위 시간(분 단위)'
        add_unit_fee_col = '공휴일 추가 단위 요금'
        max_fee_col = '공휴일 일 최대 요금'

    try:
        기본시간 = float(row.get(base_time_col, row.get('기본 주차 시간(분 단위)')))
        기본요금 = float(row.get(base_fee_col, row.get('기본 주차 요금')))
        추가단위시간 = float(row.get(add_unit_time_col, row.get('추가 단위 시간(분 단위)')))
        추가단위요금 = float(row.get(add_unit_fee_col, row.get('추가 단위 요금')))
        raw_max = row.get(max_fee_col, row.get('일 최대 요금'))
        일최대요금 = float(raw_max) if pd.notna(raw_max) else None
        total_minutes = float(total_minutes)
    except Exception:
        return float('inf')

    # 필수값 체크
    if any([
        pd.isna(기본시간) or 기본시간 < 0,
        pd.isna(기본요금) or 기본요금 < 0,
        pd.isna(추가단위시간) or 추가단위시간 <= 0,
        pd.isna(추가단위요금) or 추가단위요금 < 0
    ]):
        return float('inf')

    if total_minutes <= 기본시간:
        fee = 기본요금
    else:
        extra_minutes = total_minutes - 기본시간
        units = int((extra_minutes + 추가단위시간 - 1) // 추가단위시간)
        fee = 기본요금 + units * 추가단위요금

    if (일최대요금 is not None) and (fee > 일최대요금):
        fee = 일최대요금

    return fee

# 데이터
df = pd.read_csv("https://raw.githubusercontent.com/lime122613/vibecoding/main/seoul_public_parking.csv", encoding="cp949") 
df = df.dropna(subset=['위도', '경도']) 
df['구'] = df['주소'].apply(lambda x: x.split()[0] if '구' in x else '') 
gu_list = sorted(df['구'].unique()) 
selected_gu = st.selectbox("구를 선택하세요", gu_list) 
filtered = df[df['구'] == selected_gu]

st.markdown("---")
st.subheader("💸주차 요금 비교하기")
day_type = st.radio("주차할 요일을 선택해주세요", ["평일", "토요일", "공휴일"])
total_minutes = st.slider(
    "주차할 시간(분)을 선택하세요",
    min_value=10, max_value=720, step=10, value=60
)

# 요금 계산 및 정렬
filtered['예상요금'] = filtered.apply(lambda row: calc_fee(row, total_minutes, day_type), axis=1)
filtered = filtered[filtered['예상요금'] != float('inf')].copy()
filtered = filtered.sort_values('예상요금')
filtered['추천'] = ""
if not filtered.empty:
    filtered.iloc[0, filtered.columns.get_loc('추천')] = "⭐️추천"

st.write(f"총 {len(filtered)}개 주차장 검색됨 (예상 요금 오름차순)")
st.dataframe(filtered[[
    '추천', '주차장명', '주소', '예상요금', '기본 주차 시간(분 단위)',
    '기본 주차 요금', '추가 단위 요금', '추가 단위 시간(분 단위)', '일 최대 요금'
]])

# 지도
center_lat = filtered['위도'].astype(float).mean() if not filtered.empty else 37.5665
center_lon = filtered['경도'].astype(float).mean() if not filtered.empty else 126.9780
m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

for _, row in filtered.iterrows():
    tooltip_text = (
        f"총 주차면: {int(row['총 주차면'])}개<br>"
        f"기본 주차 요금: {int(row['기본 주차 요금'])}원 ({int(row['기본 주차 시간(분 단위)'])}분당)<br>"
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
        icon=folium.Icon(color='red' if row['추천'] else 'blue')
    ).add_to(m)

st_folium(m, width=1200, height=650)
