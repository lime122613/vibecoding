import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import xml.etree.ElementTree as ET

st.set_page_config(layout="wide")
st.title("🚗서울시 공영주차장 요금 추천앱🪄")

# 🚨 1. API KEY와 기본 주소를 입력하세요
API_KEY = "59534c67436c696d323474466b4275"  # <- 본인 API KEY로 교체
API_URL = "https://openapi.seoul.go.kr:8088/"  # 실제 엔드포인트는 데이터포털에서 확인

def get_parking_api_df(api_key, start=1, end=1000):
    # 예시: openapi.seoul.go.kr:8088/(인증키)/xml/GetParkInfo/1/1000/
    url = f"https://openapi.seoul.go.kr:8088/{api_key}/xml/GetParkInfo/{start}/{end}/"
    response = requests.get(url)
    response.encoding = 'utf-8'
    root = ET.fromstring(response.text)
    rows = root.findall('.//row')
    data = []
    for row in rows:
        record = {}
        for col in row:
            record[col.tag] = col.text
        data.append(record)
    df = pd.DataFrame(data)
    return df

def format_time(hhmm):
    if pd.isnull(hhmm) or hhmm is None or hhmm == "":
        return "-"
    s = str(hhmm).zfill(4)
    h = int(s[:2])
    m = int(s[2:])
    return f"{h}:{m:02d}"

def calc_fee(row, total_minutes, day_type):
    # 컬럼명은 실제 DataFrame의 XML 태그명 기준!
    if day_type == "평일":
        base_fee_col = 'PRK_CRG'
        base_time_col = 'PRK_HM'
        add_unit_fee_col = 'ADD_CRG'
        add_unit_time_col = 'ADD_UNIT_TM_MNT'
        max_fee_col = 'DLY_MAX_CRG'
    elif day_type == "토요일":
        # 실제로 별도 컬럼이 없으면 평일과 동일하게 설정!
        base_fee_col = 'PRK_CRG'
        base_time_col = 'PRK_HM'
        add_unit_fee_col = 'ADD_CRG'
        add_unit_time_col = 'ADD_UNIT_TM_MNT'
        max_fee_col = 'DLY_MAX_CRG'
    else:  # 공휴일
        base_fee_col = 'PRK_CRG'
        base_time_col = 'PRK_HM'
        add_unit_fee_col = 'ADD_CRG'
        add_unit_time_col = 'ADD_UNIT_TM_MNT'
        max_fee_col = 'DLY_MAX_CRG'

    try:
        기본시간 = float(row.get(base_time_col, 0))
        기본요금 = float(row.get(base_fee_col, 0))
        추가단위시간 = float(row.get(add_unit_time_col, 0))
        추가단위요금 = float(row.get(add_unit_fee_col, 0))
        일최대요금 = float(row.get(max_fee_col, 0)) if row.get(max_fee_col) not in [None, '', '0'] else None
        total_minutes = float(total_minutes)
    except Exception as e:
        return float('inf')

    # 필수값 체크 (추가단위시간 0, NaN 등 예외)
    if any([
        pd.isnull(기본시간), 기본시간 < 0,
        pd.isnull(기본요금), 기본요금 < 0,
        pd.isnull(추가단위시간), 추가단위시간 <= 0,
        pd.isnull(추가단위요금), 추가단위요금 < 0
    ]):
        return float('inf')

    if total_minutes <= 기본시간:
        fee = 기본요금
    else:
        extra_minutes = total_minutes - 기본시간
        units = int((extra_minutes + 추가단위시간 - 1) // 추가단위시간)
        fee = 기본요금 + units * 추가단위요금

    if 일최대요금 and fee > 일최대요금:
        fee = 일최대요금

    return fee

# 🚨 2. 데이터 불러오기
st.info("서울시 공영주차장 실시간 데이터를 API로 불러옵니다.")
with st.spinner("데이터 불러오는 중... (잠시만 기다려주세요)"):
    df = get_parking_api_df(API_KEY, start=1, end=1000)  # 한 번에 1000개, 필요시 반복 호출로 전체 사용 가능

# 🚨 3. 컬럼 가공 및 결측값 처리
if not df.empty:
    # 위경도 전처리 및 결측 제거
    df['위도'] = pd.to_numeric(df['LAT'], errors='coerce')
    df['경도'] = pd.to_numeric(df['LOT'], errors='coerce')
    df = df.dropna(subset=['위도', '경도'])
    df['구'] = df['ADDR'].apply(lambda x: x.split()[0] if x and '구' in x else '')
    df['총 주차면'] = pd.to_numeric(df['TPKCT'], errors='coerce')

    gu_list = sorted(df['구'].unique())
    selected_gu = st.selectbox("구를 선택하세요", gu_list)
    filtered = df[df['구'] == selected_gu]

    st.markdown("---")
    st.subheader("💸주차 요금 비교하기")
    day_type = st.radio("주차할 요일을 선택해주세요", ["평일", "토요일", "공휴일"])
    total_minutes = st.slider(
        "주차할 시간(분)을 선택하세요",
        min_value=10,
        max_value=720,
        step=10,
        value=60
    )

    filtered['예상요금'] = filtered.apply(lambda row: calc_fee(row, total_minutes, day_type), axis=1)
    filtered = filtered[filtered['예상요금'] != float('inf')]
    filtered = filtered.sort_values('예상요금')
    filtered['추천'] = ""
    if not filtered.empty:
        filtered.iloc[0, filtered.columns.get_loc('추천')] = "⭐️추천"

    st.write(f"총 {len(filtered)}개 주차장 검색됨 (예상 요금 오름차순)")
    st.dataframe(filtered[['추천', 'PKLT_NM', 'ADDR', '예상요금', 'PRK_HM', 'PRK_CRG',
                          'ADD_CRG', 'ADD_UNIT_TM_MNT', 'DLY_MAX_CRG']].rename(
        columns={
            'PKLT_NM': '주차장명',
            'ADDR': '주소',
            'PRK_HM': '기본 주차 시간(분 단위)',
            'PRK_CRG': '기본 주차 요금',
            'ADD_CRG': '추가 단위 요금',
            'ADD_UNIT_TM_MNT': '추가 단위 시간(분 단위)',
            'DLY_MAX_CRG': '일 최대 요금'
        }
    ))

    # 지도
    center_lat = filtered['위도'].astype(float).mean() if not filtered.empty else 37.5665
    center_lon = filtered['경도'].astype(float).mean() if not filtered.empty else 126.9780
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    for _, row in filtered.iterrows():
        tooltip_text = (
            f"총 주차면: {int(row['총 주차면']) if not pd.isnull(row['총 주차면']) else '-'}개<br>"
            f"기본 주차 요금: {int(row['PRK_CRG']) if not pd.isnull(row['PRK_CRG']) else '-'}원 ({int(row['PRK_HM']) if not pd.isnull(row['PRK_HM']) else '-'}분당)<br>"
            f"평일: {format_time(row['WD_OPER_BGNG_TM'])} ~ {format_time(row['WD_OPER_END_TM'])}<br>"
            f"주말: {format_time(row['WE_OPER_BGNG_TM'])} ~ {format_time(row['WE_OPER_END_TM'])}<br>"
            f"공휴일: {format_time(row['LHLDY_BGNG'])} ~ {format_time(row['LHLDY'])}<br>"
        )
        popup_text = (
            f"<b>{row['PKLT_NM']}</b><br>"
            f"주소: {row['ADDR']}<br>"
            f"전화번호: {row['TELNO']}<br>"
            f"운영구분: {row['OPER_SE_NM']}<br>"
            f"예상요금: {int(row['예상요금']) if not pd.isnull(row['예상요금']) else '-'}원<br>"
            f"기본 주차 시간: {row['PRK_HM']}분<br>"
            f"기본 주차 요금: {row['PRK_CRG']}원<br>"
            f"추가 단위 요금: {row['ADD_CRG']}원<br>"
            f"추가 단위 시간: {row['ADD_UNIT_TM_MNT']}분<br>"
            f"일 최대 요금: {row['DLY_MAX_CRG']}"
        )
        folium.Marker(
            location=[float(row['위도']), float(row['경도'])],
            popup=folium.Popup(popup_text, max_width=350, min_width=200),
            tooltip=tooltip_text,
            icon=folium.Icon(color='blue' if row['추천'] == "" else 'red')
        ).add_to(m)

    st_folium(m, width=1200, height=650)
else:
    st.error("API에서 데이터를 불러올 수 없습니다. (키 오류 등 확인)")
