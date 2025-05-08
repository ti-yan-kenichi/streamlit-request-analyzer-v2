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

uploaded = st.file_uploader("📁 CSVファイルをアップロード（複数可）", type="csv", accept_multiple_files=True)
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

def analyze_and_plot(df, title, x_col, use_locator=True):
    df["1時間前までの件数"] = df["リクエスト日時"].apply(
        lambda t: df[(df["リクエスト日時"] < t) & (df["リクエスト日時"] >= t - pd.Timedelta(hours=1))].shape[0]
    )
    fig, ax = plt.subplots(figsize=(min(24, max(10, len(df) / 100)), 6), dpi=120)
    below = df[df["1時間前までの件数"] <= threshold]
    above = df[df["1時間前までの件数"] > threshold]
    ax.plot(below[x_col], below["1時間前までの件数"], 'o-', label="正常", markersize=3)
    ax.plot(above[x_col], above["1時間前までの件数"], 'o', color='red', label="超過", markersize=5)
    ax.set_title(title, fontproperties=jp_font)
    ax.set_ylabel("件数", fontproperties=jp_font)
    ax.set_xlabel("順序" if x_col == "index" else "時刻", fontproperties=jp_font)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_yticks(range(0, int(df["1時間前までの件数"].max()) + y_tick_label, y_tick_label))
    if use_locator and x_col == "リクエスト日時":
        ax.xaxis.set_major_locator(locator_map[x_tick_label])
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)
    return df

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

        with tabs[-1]:
            st.subheader("🔗 結合分析")
            combined_df = pd.concat(file_data.values()).sort_values("リクエスト日時").reset_index(drop=True)
            min_dt = combined_df["リクエスト日時"].min()
            max_dt = combined_df["リクエスト日時"].max()
            col1, col2 = st.columns(2)
            with col1:
                s_date = st.date_input("開始日（結合）", min_dt.date(), key="sdate_all")
                s_time = st.time_input("開始時刻（結合）", min_dt.time(), key="stime_all")
            with col2:
                e_date = st.date_input("終了日（結合）", max_dt.date(), key="edate_all")
                e_time = st.time_input("終了時刻（結合）", max_dt.time(), key="etime_all")
            start_dt = pd.to_datetime(f"{s_date} {s_time}")
            end_dt = pd.to_datetime(f"{e_date} {e_time}")
            if start_dt < end_dt:
                df = combined_df[(combined_df["リクエスト日時"] >= start_dt) & (combined_df["リクエスト日時"] <= end_dt)].copy()
                if xaxis_type == "➡️ 詰めた順序":
                    df["index"] = range(len(df))
                    analyze_and_plot(df, "結合リクエスト件数（詰め表示）", "index", use_locator=False)
                else:
                    analyze_and_plot(df, "結合リクエスト件数（時系列）", "リクエスト日時", use_locator=True)