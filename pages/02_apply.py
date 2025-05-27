import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 구글 시트 인증 및 열기
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(
    'google_service_account.json',  # 서비스 계정 키 파일명
    scopes=scope
)
gc = gspread.authorize(creds)
sh = gc.open("상담예약시트명")  # 구글 시트명
worksheet = sh.sheet1

# 이미 신청된 시간대 불러오기
existing = pd.DataFrame(worksheet.get_all_records())
reserved_slots = set(existing["상담일시"]) if not existing.empty else set()

# 예약 가능한 타임슬롯 예시
all_slots = [
    "2024-06-01 10:00", "2024-06-01 10:30", "2024-06-01 11:00",
    "2024-06-01 11:30", "2024-06-01 13:00", "2024-06-01 13:30"
]
available_slots = [slot for slot in all_slots if slot not in reserved_slots]

st.title("학부모 상담 예약 시스템")
with st.form("reserve"):
    name = st.text_input("학생 이름")
    parent = st.text_input("학부모 성함")
    slot = st.selectbox("상담 시간", available_slots)
    submitted = st.form_submit_button("신청하기")
    if submitted:
        # 신청 중복 체크 한 번 더
        existing = pd.DataFrame(worksheet.get_all_records())
        reserved_slots = set(existing["상담일시"]) if not existing.empty else set()
        if slot in reserved_slots:
            st.error("이미 예약된 시간입니다. 다시 시도해주세요.")
        else:
            worksheet.append_row([name, parent, slot])
            st.success("상담 신청이 완료되었습니다!")

st.markdown("#### 이미 예약된 시간")
for rs in sorted(reserved_slots):
    st.write(rs)
