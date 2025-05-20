import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import os
import plotly.graph_objects as go

font_path = "fonts/NotoSansJP-Regular.ttf"
jp_font = fm.FontProperties(fname=font_path)

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
    y_tick_label = st.selectbox("Y軸目盛", [1000, 500, 300, 200, 100, 50, 10, 5], index=5)
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

def analyze_and_plot(df, title, x_col, use_locator=True):
    df["1時間前までの件数"] = df["リクエスト日時"].apply(
        lambda t: df[(df["リクエスト日時"] < t) & (df["リクエスト日時"] >= t - pd.Timedelta(hours=1))].shape[0]
    )
    below = df[df["1時間前までの件数"] <= threshold]
    above = df[df["1時間前までの件数"] > threshold]
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=below[x_col],
        y=below["1時間前までの件数"],
        mode='lines+markers',
        name="正常",
        marker=dict(color='blue', size=5),
        hovertemplate="日時: %{x}<br>件数: %{y}"
    ))

    fig.add_trace(go.Scatter(
        x=above[x_col],
        y=above["1時間前までの件数"],
        mode='markers',
        name="超過",
        marker=dict(color='red', size=7),
        hovertemplate="日時: %{x}<br>件数: %{y}"
    ))

    fig.update_layout(
        title=title,
        xaxis_title="時刻" if x_col == "リクエスト日時" else "順序",
        yaxis_title="件数",
        height=500,
        xaxis=dict(rangeslider=dict(visible=True), type='date' if x_col == "リクエスト日時" else 'linear'),
        yaxis=dict(dtick=y_tick_label)
    )

    st.plotly_chart(fig, use_container_width=True)
    return dfuploaded = st.file_uploader("📁 CSVファイルをアップロード（複数可）", type="csv", accept_multiple_files=True)
if uploaded and not st.session_state.clear_triggered:
    st.session_state.uploaded_files = uploaded
uploaded_files = st.session_state.uploaded_files

locator_map = {
    "1ヶ月": mdates.MonthLocator(),
    "7日": mdates.WeekdayLocator(interval=1),
    "1日": mdates.DayLocator(interval=1),
    "12時間": mdates.HourLocator(interval=12),
    "6時間": mdates.HourLocator(interval=6),
    "3時間": mdates.HourLocator(interval=3),
    "1時間": mdates.HourLocator(interval=1),
    "30分": mdates.MinuteLocator(interval=30),
    "15分": mdates.MinuteLocator(interval=15),
    "5分": mdates.MinuteLocator(interval=5),
}

def summarize_peak(df_result):
    max_val = df_result["1時間前までの件数"].max()
    peak_time = df_result.loc[df_result["1時間前までの件数"].idxmax(), "リクエスト日時"].strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"📈 **ピーク件数：{max_val} 件**")
    st.markdown(f"🕒 **ピーク時刻：{peak_time}**")

if uploaded_files:
    file_data = {}
    for file in uploaded_files:
        try:
            df = pd.read_csv(file, skiprows=3, encoding="shift_jis", encoding_errors="replace", engine="python")
        except Exception as e:
            st.error(f"❌ CSV読み込みに失敗しました: {e}")
            continue

        if "リクエスト日時" not in df.columns:
            st.error(f"❌ ファイル '{file.name}' に 'リクエスト日時' 列が見つかりません。")
            continue

        df["リクエスト日時"] = pd.to_datetime(df["リクエスト日時"].astype(str).str.strip("'"), errors="coerce")
        df = df.sort_values("リクエスト日時")
        file_data[file.name] = df

    if file_data:
        tabs = st.tabs(list(file_data.keys()) + ["🔗 結合分析"])

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
                    if auto_reload or st.button(f"✅ 分析する", key=f"run_{fname}"):
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
    pass
    pass

