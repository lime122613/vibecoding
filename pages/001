import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(layout="wide")

def get_parking_api_df(api_url, api_key, params=None):
    params = params or {}
    params['serviceKey'] = api_key
    params['type'] = 'xml'
    res = requests.get(api_url, params=params)
    res.encoding = 'utf-8'
    root = ET.fromstring(res.text)
    rows = root.findall('.//row')
    data = []
    for row in rows:
        record = {}
        for col in row:
            record[col.tag] = col.text
        data.append(record)
    df = pd.DataFrame(data)
    return df

# 여기에 본인 api_url, api_key 입력
api_url = 'https://your_api_url_here'
api_key = 'import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(layout="wide")

def get_parking_api_df(api_url, api_key, params=None):
    params = params or {}
    params['serviceKey'] = api_key
    params['type'] = 'xml'
    res = requests.get(api_url, params=params)
    res.encoding = 'utf-8'
    root = ET.fromstring(res.text)
    rows = root.findall('.//row')
    data = []
    for row in rows:
        record = {}
        for col in row:
            record[col.tag] = col.text
        data.append(record)
    df = pd.DataFrame(data)
    return df

# 여기에 본인 api_url, api_key 입력
api_url = 'http://openapi.seoul.go.kr:8088/sample/xml/GetParkInfo/1/5/'
api_key = '59534c67436c696d323474466b4275'
df = get_parking_api_df(api_url, api_key)

# 컬럼명/타입 등 정리 (df.rename, to_numeric 등 활용)
# 이후 기존 Streamlit 코드와 완전히 동일하게 사용

st.write(df.head())
'
df = get_parking_api_df(api_url, api_key)

# 컬럼명/타입 등 정리 (df.rename, to_numeric 등 활용)
# 이후 기존 Streamlit 코드와 완전히 동일하게 사용

st.write(df.head())
