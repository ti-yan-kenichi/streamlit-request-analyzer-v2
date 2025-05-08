import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import os

font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
jp_font = fm.FontProperties(fname=font_path) if os.path.exists(font_path) else None

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "clear_triggered" not in st.session_state:
    st.session_state.clear_triggered = False

st.set_page_config(page_title="リクエスト分析", layout="wide")
st.title("📊 リクエスト分析ダッシュボード")

with st.sidebar:
    st.header("⚙️ 分析設定")
    auto_reload = st.checkbox("設定変更で自動更新", value=True)
    threshold = st.number_input("制限値", min_value=1, step=1, value=360)
    y_tick_label = st.selectbox("Y軸目盛", [1000, 500, 300, 200, 100, 50], index=3)
    x_tick_label = st.selectbox(
        "X軸目盛",
        ["1ヶ月", "7日", "1日", "12時間", "6時間", "3時間", "1時間", "30分", "15分", "5分"],
        index=6,
    )
    xaxis_type = st.radio("結合グラフのX軸", ["📅 時系列", "➡️ 詰めた順序"], horizontal=True)
    if st.button("🧹 入力ファイルをクリア"):
        st.session_state.uploaded_files = []
        st.session_state.clear_triggered = True
        st.rerun()