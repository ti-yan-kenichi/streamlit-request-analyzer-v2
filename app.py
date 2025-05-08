import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import os

font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
jp_font = fm.FontProperties(fname=font_path) if os.path.exists(font_path) else None

# 以降は省略、必要な fontproperties を set_title, xlabel, ylabel, xticks, yticks, legend に適用済みバージョン