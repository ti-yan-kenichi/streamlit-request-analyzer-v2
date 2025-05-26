import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import plotly.graph_objects as go
import os

# フォント設定（存在しなければ無視）
font_path = "fonts/NotoSansJP-Regular.ttf"
jp_font = fm.FontProperties(fname=font_path) if os.path.exists(font_path) else None

st.set_page_config(page_title="リクエスト分析", layout="wide")
st.title("📊 リクエスト分析ダッシュボード")

# 初期化ステート
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "clear_triggered" not in st.session_state:
    st.session_state.clear_triggered = False

# サイドバー設定
with st.sidebar:
    st.header("⚙️ 分析設定（実行ボタンを押してください）")
    threshold = st.number_input("制限値", min_value=1, step=1, value=360)
    y_tick_label = st.selectbox("Y軸目盛", [1000, 500, 300, 200, 100, 50, 10, 5], index=5)
    if st.button("🧹 入力ファイルをクリア"):
        st.session_state.uploaded_files = []
        st.session_state.clear_triggered = False
        st.session_state["file_uploader"] = None
        st.experimental_rerun()

# 残りのロジックは既存コードと同様に継続...