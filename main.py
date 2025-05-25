import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 데이터 불러오기 (파일 업로드 시 주석처리 가능)
# df = pd.read_csv('서울시 공영주차장 안내 정보.csv', encoding='cp949')
# Streamlit 파일 업로드 사용시
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding='cp949')

    # 위도/경도 없는 행 제외
    df = df.dropna(subset=['위도', '경도'])

    # 구명 추출(주소에서 '구' 앞까지)
    df['구'] = df['주소'].apply(lambda x: x.split()[0] if '구' in x else '')

    st.title("서울시 공영주차장 안내 서비스")

    # 구 필터
    gu_list = sorted(df['구'].unique())
    selected_gu = st.selectbox("구를 선택하세요", gu_list)

    # 주차장명 검색
    keyword = st.text_input("주차장명 검색 (선택)", "")

    # 필터링
    filtered = df[df['구'] == selected_gu]
    if keyword:
        filtered = filtered[filtered['주차장명'].str.contains(keyword, case=False, na=False)]

    st.write(f"총 {len(filtered)}개 주차장 검색됨")
    st.dataframe(filtered[['주차장명', '주소', '전화번호', '운영구분명', '기본 주차 요금', '일 최대 요금', '위도', '경도']])

    # 지도
    center_lat = filtered['위도'].astype(float).mean() if not filtered.empty else 37.5665
    center_lon = filtered['경도'].astype(float).mean() if not filtered.empty else 126.9780
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # 마커 표시
    for _, row in filtered.iterrows():
        popup_text = f"""
        <b>{row['주차장명']}</b><br>
        주소: {row['주소']}<br>
        전화번호: {row['전화번호']}<br>
        운영구분: {row['운영구분명']}<br>
        기본 주차 요금: {row['기본 주차 요금']}<br>
        일 최대 요금: {row['일 최대 요금']}
        """
        folium.Marker(
            location=[float(row['위도']), float(row['경도'])],
            popup=folium.Popup(popup_text, max_width=350, min_width=200),
            tooltip=row['주차장명']
        ).add_to(m)

    st_folium(m, width=1000, height=650)
else:
    st.info("서울시 공영주차장 안내 정보 CSV 파일을 업로드해 주세요.")
