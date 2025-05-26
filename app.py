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


# ファイルアップロード欄
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
    df = df[df["1時間前までの件数"] > 0]  # リクエストが0の行を除外
    below = df[df["1時間前までの件数"] <= threshold]
    above = df[df["1時間前までの件数"] > threshold]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=below[x_col], y=below["1時間前までの件数"], mode='lines+markers',
                             name="正常", marker=dict(color='blue', size=5),
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
    if df_result.empty or "1時間前までの件数" not in df_result.columns:
        st.info("📉 ピーク情報はありません（データが空またはすべて0件です）。")
        return
    max_val = df_result["1時間前までの件数"].max()
    peak_time = df_result.loc[df_result["1時間前までの件数"].idxmax(), "リクエスト日時"].strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"📈 **ピーク件数：{max_val} 件**")
    st.markdown(f"🕒 **ピーク時刻：{peak_time}**")

if uploaded_files:
    file_data = {}
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
        file_data[file.name] = df

    if file_data:
        file_names = list(file_data.keys())
        tabs = st.tabs(file_names + (["🔗 結合分析"] if len(file_names) > 1 else []))

        for i, (fname, df_all) in enumerate(file_data.items()):
            with tabs[i]:
                st.subheader(f"📁 {fname}")
                min_dt, max_dt = df_all["リクエスト日時"].min(), df_all["リクエスト日時"].max()
                col1, col2 = st.columns(2)
                with col1:
                    s_date = st.date_input(f"[{fname}] 開始日", min_dt.date(), key=f"sdate_{fname}")
                    s_time = st.time_input(f"[{fname}] 開始時刻", min_dt.time(), key=f"stime_{fname}")
                with col2:
                    e_date = st.date_input(f"[{fname}] 終了日", max_dt.date(), key=f"edate_{fname}")
                    e_time = st.time_input(f"[{fname}] 終了時刻", max_dt.time(), key=f"etime_{fname}")
                start_dt = pd.to_datetime(f"{s_date} {s_time}")
                end_dt = pd.to_datetime(f"{e_date} {e_time}")
                if start_dt < end_dt and st.button(f"✅ 分析する", key=f"run_{fname}"):
                    df_filtered = df_all[(df_all["リクエスト日時"] >= start_dt) & (df_all["リクエスト日時"] <= end_dt)].copy()
                    df_result = analyze_and_plot(df_filtered, f"{fname} のリクエスト件数", "リクエスト日時")
                    summarize_peak(df_result)
                    df_exceed = df_result[df_result["1時間前までの件数"] > threshold][["リクエスト日時", "1時間前までの件数"]]
                    if not df_exceed.empty:
                        st.subheader("⚠️ 制限値を超えた時間帯")
                        st.dataframe(df_exceed, use_container_width=True)
                        st.download_button("📥 超過リストCSV", df_exceed.to_csv(index=False).encode("utf-8"),
                                           file_name=f"{fname}_exceed.csv", mime="text/csv")
                    else:
                        st.info("✅ 制限値を超えたデータはありませんでした。")

        if len(file_data) > 1:
            with tabs[-1]:
                st.subheader("📊 結合グラフ")
                df_combined = pd.concat(file_data.values()).sort_values("リクエスト日時")
                min_dt, max_dt = df_combined["リクエスト日時"].min(), df_combined["リクエスト日時"].max()
                col1, col2 = st.columns(2)
                with col1:
                    s_date = st.date_input("🔗 開始日", min_dt.date(), key="sdate_combined")
                    s_time = st.time_input("🔗 開始時刻", min_dt.time(), key="stime_combined")
                with col2:
                    e_date = st.date_input("🔗 終了日", max_dt.date(), key="edate_combined")
                    e_time = st.time_input("🔗 終了時刻", max_dt.time(), key="etime_combined")
                start_dt = pd.to_datetime(f"{s_date} {s_time}")
                end_dt = pd.to_datetime(f"{e_date} {e_time}")
                if start_dt < end_dt and st.button("✅ 結合分析する", key="run_combined"):
                    df_filtered = df_combined[(df_combined["リクエスト日時"] >= start_dt) & (df_combined["リクエスト日時"] <= end_dt)].copy()
                    df_result = analyze_and_plot(df_filtered, "結合グラフ", "リクエスト日時")
                    summarize_peak(df_result)
                    df_exceed = df_result[df_result["1時間前までの件数"] > threshold][["リクエスト日時", "1時間前までの件数"]]
                    if not df_exceed.empty:
                        st.subheader("⚠️ 制限値を超えた時間帯")
                        st.dataframe(df_exceed, use_container_width=True)
                        st.download_button("📥 超過リストCSV", df_exceed.to_csv(index=False).encode("utf-8"),
                                           file_name="combined_exceed.csv", mime="text/csv")
                    else:
                        st.info("✅ 制限値を超えたデータはありませんでした。")


if st.session_state.get("force_rerun", False):
    st.session_state["force_rerun"] = False
    st.experimental_rerun()