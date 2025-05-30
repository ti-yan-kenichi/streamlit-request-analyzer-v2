
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
if "analyzed_data" not in st.session_state:
    st.session_state.analyzed_data = {}
if "draw_lines" not in st.session_state:
    st.session_state.draw_lines = True

with st.sidebar:
    st.header("⚙️ 分析設定（実行ボタンを押してください）")
    threshold = st.number_input("制限値", min_value=1, step=1, value=360)
    y_tick_label = st.selectbox("Y軸目盛", [1000, 500, 300, 200, 100, 50, 10, 5], index=5)
    draw_lines = st.checkbox("線を表示", value=st.session_state.draw_lines)
    st.session_state.draw_lines = draw_lines
    if st.button("🧹 入力ファイルをクリア"):
        st.session_state.uploaded_files = []
        st.session_state.analyzed_data = {}
        st.session_state.clear_triggered = False
        if "file_uploader" in st.session_state:
            del st.session_state["file_uploader"]
        st.success("✅ 入力内容を初期化しました。")
        st.experimental_rerun()

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
    below = df[df["1時間前までの件数"] <= threshold]
    above = df[df["1時間前までの件数"] > threshold]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=below[x_col], y=below["1時間前までの件数"],
                             mode='lines+markers' if st.session_state.draw_lines else 'markers',
                             connectgaps=False, name="正常", marker=dict(color='blue', size=5),
                             hovertemplate="日時: %{x}<br>件数: %{y}"))
    fig.add_trace(go.Scatter(x=above[x_col], y=above["1時間前までの件数"], mode='markers',
                             name="超過", marker=dict(color='red', size=7),
                             hovertemplate="日時: %{x}<br>件数: %{y}"))
    fig.update_layout(title=title, xaxis_title="時刻", yaxis_title="件数",
                      xaxis=dict(rangeslider=dict(visible=True), type='date'),
                      yaxis=dict(dtick=y_tick_label), height=500)
    st.plotly_chart(fig, use_container_width=True)
    return df

def summarize_peak(df_result):
    if df_result.empty or "1時間前までの件数" not in df_result.columns or df_result["1時間前までの件数"].isnull().all():
        st.info("📉 ピーク情報はありません（データが空またはすべて0件です）。")
        return
    max_val = df_result["1時間前までの件数"].max()
    peak_time = df_result.loc[df_result["1時間前までの件数"].idxmax(), "リクエスト日時"]
    peak_time_str = pd.to_datetime(peak_time).strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"📈 **ピーク件数：{max_val} 件**")
    st.markdown(f"🕒 **ピーク時刻：{peak_time_str}**")

if uploaded_files:
    for file in uploaded_files:
        try:
            if file.getbuffer().nbytes == 0:
                raise ValueError("空のファイルです")
            df = pd.read_csv(file, skiprows=3, encoding="shift_jis", encoding_errors="replace", engine="python")
            if df.empty:
                raise ValueError("データが空のためスキップ")
        except Exception as e:
            st.warning(f"⚠️ ファイル '{file.name}' はスキップされました（{e}）")
            continue

        if "リクエスト日時" not in df.columns:
            st.warning(f"⚠️ ファイル '{file.name}' に 'リクエスト日時' 列が見つかりません。")
            continue

        df["リクエスト日時"] = pd.to_datetime(df["リクエスト日時"].astype(str).str.strip("'"), errors="coerce")
        df = df.sort_values("リクエスト日時")
        st.session_state.analyzed_data[file.name] = df

    for fname, df in st.session_state.analyzed_data.items():
        st.subheader(f"📁 {fname}")
        df_result = analyze_and_plot(df, f"{fname} のリクエスト件数", "リクエスト日時")
        summarize_peak(df_result)
