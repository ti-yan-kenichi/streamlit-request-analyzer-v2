import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import plotly.graph_objects as go
import os

font_path = "fonts/NotoSansJP-Regular.ttf"
jp_font = fm.FontProperties(fname=font_path) if os.path.exists(font_path) else None

st.set_page_config(page_title="リクエスト分析", layout="wide")
st.title("📊 リクエスト分析ダッシュボード")

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "clear_triggered" not in st.session_state:
    st.session_state.clear_triggered = False

with st.sidebar:
    st.header("⚙️ 分析設定（実行ボタンを押してください）")
    threshold = st.number_input("制限値", min_value=1, step=1, value=360)
    y_tick_label = st.selectbox("Y軸目盛", [1000, 500, 300, 200, 100, 50, 10, 5], index=5)
    if st.button("🧹 入力ファイルをクリア"):
        st.session_state.uploaded_files = []
        st.session_state.clear_triggered = False
        if "file_uploader" in st.session_state:
            del st.session_state["file_uploader"]
        st.success("✅ 入力内容を初期化しました。")

uploaded = st.file_uploader("📁 CSVファイルをアップロード（複数可）", type="csv", accept_multiple_files=True, key="file_uploader")
if uploaded and not st.session_state.clear_triggered:
    st.session_state.uploaded_files = uploaded
uploaded_files = st.session_state.uploaded_files

if not uploaded and not uploaded_files:
    st.info("📂 『Browse files』ボタンからCSVファイルをアップロードしてください。")

def analyze_and_plot(df, title, x_col):
    df["1時間前までの件数"] = df["リクエスト日時"].apply(
        lambda t: df[(df["リクエスト日時"] < t) & (df["リクエスト日時"] >= t - pd.Timedelta(hours=1))].shape[0]
    )
    df["1時間前までの件数"] = df["1時間前までの件数"].apply(lambda x: x if x > 0 else None)
    df["超過フラグ"] = df["1時間前までの件数"].apply(lambda x: x > threshold if pd.notnull(x) else False)

    fig = go.Figure()

    over_indexes = df[df["超過フラグ"]].index.tolist()
    cut_indexes = []
    for idx in over_indexes:
        next_idx = idx + 1
        if next_idx in df.index:
            cut_indexes.append(next_idx)

    df_normal = df[~df["超過フラグ"]].copy()
    df_normal.loc[cut_indexes, "1時間前までの件数"] = None
    df_normal["1時間前までの件数"] = df_normal["1時間前までの件数"].astype(float)

    fig.add_trace(go.Scatter(
        x=df_normal[x_col],
        y=df_normal["1時間前までの件数"],
        mode="lines+markers",
        name="正常",
        marker=dict(color="blue", size=5),
        connectgaps=False,
        hovertemplate="日時: %{x}<br>件数: %{y}"
    ))

    exceed = df[df["超過フラグ"]]
    fig.add_trace(go.Scatter(
        x=exceed[x_col],
        y=exceed["1時間前までの件数"],
        mode="markers",
        name="超過",
        marker=dict(color="red", size=7),
        hovertemplate="日時: %{x}<br>件数: %{y}"
    ))

    fig.update_layout(
        title=title,
        xaxis_title="時刻",
        yaxis_title="件数",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        yaxis=dict(dtick=y_tick_label),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    return df
