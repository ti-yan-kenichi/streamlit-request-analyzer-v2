import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import plotly.graph_objects as go
import os

font_path = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(font_path):
    jp_font = fm.FontProperties(fname=font_path)
else:
    jp_font = None  # fallback

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "clear_triggered" not in st.session_state:
    st.session_state.clear_triggered = False

st.set_page_config(page_title="リクエスト分析", layout="wide")
st.title("📊 リクエスト分析ダッシュボード")

with st.sidebar:
    st.header("⚙️ 分析設定（実行ボタンを押してください）")
    threshold = st.number_input("制限値", min_value=1, step=1, value=360)
    y_tick_label = st.selectbox("Y軸目盛", [1000, 500, 300, 200, 100, 50, 10, 5], index=5)
    if st.button("🧹 入力ファイルをクリア"):
        st.session_state.uploaded_files = []
        st.session_state.clear_triggered = False
        st.session_state["file_uploader"] = None
        st.stop()

def analyze_and_plot(df, title, x_col):
    timestamps = df["リクエスト日時"]
    counts = []
    for i in range(len(timestamps)):
        start_time = timestamps.iloc[i] - pd.Timedelta(hours=1)
        count = timestamps[(timestamps >= start_time) & (timestamps < timestamps.iloc[i])].count()
        counts.append(count)
    df["1時間前までの件数"] = counts

    y_vals = df["1時間前までの件数"].tolist()
    x_vals = df[x_col].tolist()
    below_x, below_y, above_x, above_y = [], [], [], []
    for x, y in zip(x_vals, y_vals):
        if y > threshold:
            above_x.append(x)
            above_y.append(y)
            below_x.append(None)
            below_y.append(None)
        elif y > 0:
            below_x.append(x)
            below_y.append(y)
            above_x.append(None)
            above_y.append(None)
        else:
            above_x.append(None)
            above_y.append(None)
            below_x.append(None)
            below_y.append(None)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=below_x, y=below_y, mode='lines+markers', name="正常",
                             marker=dict(color='blue', size=5),
                             hovertemplate="日時: %{x}<br>件数: %{y}"))
    fig.add_trace(go.Scatter(x=above_x, y=above_y, mode='markers', name="超過",
                             marker=dict(color='red', size=7),
                             hovertemplate="日時: %{x}<br>件数: %{y}"))
    fig.update_layout(
        title=title,
        xaxis_title="時刻" if x_col == "リクエスト日時" else "順序",
        yaxis_title="件数",
        height=500,
        xaxis=dict(rangeslider=dict(visible=True), type='date' if x_col == "リクエスト日時" else 'linear'),
        yaxis=dict(dtick=y_tick_label)
    )
    st.plotly_chart(fig, use_container_width=True)
    return df

def summarize_peak(df_result):
    max_val = df_result["1時間前までの件数"].max()
    peak_time = df_result.loc[df_result["1時間前までの件数"].idxmax(), "リクエスト日時"].strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"📈 **ピーク件数：{max_val} 件**")
    st.markdown(f"🕒 **ピーク時刻：{peak_time}**")

uploaded = st.file_uploader("📁 CSVファイルをアップロード（複数可）", type="csv", accept_multiple_files=True, key="file_uploader")
if uploaded:
    st.session_state.clear_triggered = False
if uploaded and not st.session_state.clear_triggered:
    st.session_state.uploaded_files = uploaded
uploaded_files = st.session_state.uploaded_files

if not uploaded_files:
    st.info("📂 『Browse files』ボタンからCSVファイルをアップロードしてください。")

if uploaded_files:
    file_data = {}
    for file in uploaded_files:
        if file.getbuffer().nbytes == 0:
            continue
        try:
            if file.getbuffer().nbytes == 0:
                raise ValueError("空のファイルです")
            df = pd.read_csv(file, skiprows=3, encoding="shift_jis", encoding_errors="replace", engine="python")
            if df.empty:
                raise ValueError("データが空のためスキップされました")
        except Exception as e:
            st.warning(f"⚠️ ファイル '{file.name}' はスキップされました（{e}）")
            continue

        if "リクエスト日時" not in df.columns:
            st.error(f"❌ ファイル '{file.name}' に 'リクエスト日時' 列が見つかりません。")
            continue

        df["リクエスト日時"] = pd.to_datetime(df["リクエスト日時"].astype(str).str.strip("'"), errors="coerce")
        df = df.sort_values("リクエスト日時")
        file_data[file.name] = df

    if file_data:
        tabs = st.tabs(list(file_data.keys()))
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
                if start_dt < end_dt:
                    df_filtered = df_all[(df_all["リクエスト日時"] >= start_dt) & (df_all["リクエスト日時"] <= end_dt)].copy()
                    if st.button(f"✅ 分析する", key=f"run_{fname}"):
                        df_result = analyze_and_plot(df_filtered, f"{fname} のリクエスト件数", "リクエスト日時")
                        summarize_peak(df_result)
                        df_exceed = df_result[df_result["1時間前までの件数"] > threshold][["リクエスト日時", "1時間前までの件数"]]
                        if not df_exceed.empty:
                            st.subheader("⚠️ 制限値を超えた時間帯")
                            st.dataframe(df_exceed, use_container_width=True)
                            exceed_csv = df_exceed.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="📥 超過リストをCSVでダウンロード",
                                data=exceed_csv,
                                file_name=f"{fname}_exceed_list.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("✅ 制限値を超えたデータはありませんでした。")