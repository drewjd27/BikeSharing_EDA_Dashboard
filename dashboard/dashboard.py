import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------- KONFIGURASI DASHBOARD --------------------
st.set_page_config(
    page_title="Dashboard Penyewaan Sepeda",
    layout="wide"
)
sns.set_style('whitegrid')

# -------------------- FUNGSI LOAD DATA --------------------
@st.cache_data
def load_daily_data():
    df = pd.read_csv("dashboard/main_data.csv")
    df['dteday'] = pd.to_datetime(df['dteday'], errors='coerce')
    return df

@st.cache_data
def load_hourly_data():
    df = pd.read_csv("dashboard/hour.csv")
    if 'dteday' in df.columns:
        df['dteday'] = pd.to_datetime(df['dteday'], errors='coerce')
    return df

# -------------------- LOAD DATA --------------------
day_df_original = load_daily_data()
hour_df_original = load_hourly_data()

# -------------------- SIDEBAR FILTER: RENTANG TANGGAL --------------------
st.sidebar.header("Filter Global")

# Ambil min dan max date dari data harian; ubah ke date agar kompatibel dengan date_input
min_date = day_df_original['dteday'].min().date()
max_date = day_df_original['dteday'].max().date()

# Pilih rentang tanggal (pastikan memilih dua tanggal)
date_range = st.sidebar.date_input("Pilih Rentang Tanggal", value=[min_date, max_date])

if len(date_range) == 2:
    start_date, end_date = date_range
    if start_date > end_date:
        st.sidebar.error("Tanggal Mulai tidak boleh melebihi Tanggal Akhir.")
    # Filter data harian berdasarkan rentang tanggal yang dipilih
    day_df = day_df_original[
        (day_df_original['dteday'] >= pd.to_datetime(start_date)) &
        (day_df_original['dteday'] <= pd.to_datetime(end_date))
    ].copy()
    # Filter data hourly jika kolom 'dteday' ada
    if 'dteday' in hour_df_original.columns:
        hour_df = hour_df_original[
            (hour_df_original['dteday'] >= pd.to_datetime(start_date)) &
            (hour_df_original['dteday'] <= pd.to_datetime(end_date))
        ].copy()
    else:
        hour_df = hour_df_original.copy()
else:
    day_df = day_df_original.copy()
    hour_df = hour_df_original.copy()

# Debug: Tampilkan rentang tanggal yang dipilih dan jumlah data setelah filter
st.sidebar.markdown(f"**Data Tanggal:** {start_date} s/d {end_date}")
st.sidebar.markdown(f"**Jumlah data harian setelah filter:** {day_df.shape[0]} baris")

# -------------------- BUAT KOLOM KATEGORI SUHU (JIKA BELUM ADA) --------------------
def temp_cluster(temp):
    if temp < 0.3:
        return 'Dingin'
    elif temp < 0.6:
        return 'Biasa'
    else:
        return 'Panas'

if 'temp_cat' not in day_df.columns:
    day_df['temp_cat'] = day_df['temp'].apply(temp_cluster)
    day_df['temp_cat'] = day_df['temp_cat'].astype('category')

# -------------------- AGREGASI DATAFRAME (BERDASARKAN DATA YANG SUDAH TERFILTER) --------------------
# 1) Penyewaan Per Jam
hourly_df = hour_df.groupby('hr').agg({
    "cnt": ["max", "min", "mean", "std"]
})
hourly_df.columns = ["max_cnt", "min_cnt", "mean_cnt", "std_cnt"]
hourly_df = hourly_df.round(2)

# 2) Penyewaan Per Hari
day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
daily_agg_df = day_df.groupby('weekday').agg({
    "instant": "nunique",
    "cnt": ["max", "min", "mean", "std"]
}).reindex(day_order)
daily_agg_df.columns = ["unique_instant", "max_cnt", "min_cnt", "mean_cnt", "std_cnt"]
daily_agg_df = daily_agg_df.round(2)

# 3) Penyewaan Per Bulan
monthly_df = day_df.groupby('mnth').agg({
    "instant": "nunique",
    "cnt": ["max", "min", "mean", "std"]
})
monthly_df.columns = ["unique_instant", "max_cnt", "min_cnt", "mean_cnt", "std_cnt"]
monthly_df = monthly_df.round(2)

# 4) Penyewaan per Musim
season_df = day_df.groupby('season').agg({
    "instant": "nunique",
    "cnt": ["max", "min", "mean", "std"]
})
season_df.columns = ["unique_instant", "max_cnt", "min_cnt", "mean_cnt", "std_cnt"]
season_df = season_df.round(2)
season_avg = day_df.groupby('season')['cnt'].mean().round(2)

# 5) Penyewaan Berdasarkan Kategori Suhu
temp_df = day_df.groupby('temp_cat').agg({
    "instant": "nunique",
    "cnt": ["max", "min", "mean", "std"]
})
temp_df.columns = ["unique_instant", "max_cnt", "min_cnt", "mean_cnt", "std_cnt"]
temp_df = temp_df.round(2)
temp_avg = day_df.groupby('temp_cat')['cnt'].mean().round(2)

# 6) Penyewaan Berdasarkan Hari Kerja
working_day_df = day_df.groupby('workingday').agg({
    "instant": "nunique",
    "cnt": ["max", "min", "mean", "std"]
})
working_day_df.columns = ["unique_instant", "max_cnt", "min_cnt", "mean_cnt", "std_cnt"]
working_day_df = working_day_df.round(2)
workday_avg = day_df.groupby('workingday')['cnt'].mean().round(2)

# 7) Penyewaan Berdasarkan Hari Libur
holiday_df = day_df.groupby('holiday').agg({
    "instant": "nunique",
    "cnt": ["max", "min", "mean", "std"]
})
holiday_df.columns = ["unique_instant", "max_cnt", "min_cnt", "mean_cnt", "std_cnt"]
holiday_df = holiday_df.round(2)
holiday_avg = day_df.groupby('holiday')['cnt'].mean().round(2)

# -------------------- Data Rata-Rata untuk Visualisasi --------------------
monthly_avg = day_df.groupby('mnth')['cnt'].mean().round(2)
daily_avg = day_df.groupby('weekday')['cnt'].mean().reindex(day_order).round(2)
hourly_avg = hour_df.groupby('hr')['cnt'].mean().sort_index().round(2)

# -------------------- FUNGSI PLOT --------------------
def bar_plot(data, title, x_label, y_label):
    fig, ax = plt.subplots(figsize=(14, 7))
    sns.barplot(x=data.index, y=data.values, ax=ax)
    ax.set_title(title, fontsize=20)
    ax.set_xlabel(x_label, fontsize=14)
    ax.set_ylabel(y_label, fontsize=14)
    return fig

def line_plot(data, title, x_label, y_label):
    fig, ax = plt.subplots(figsize=(14, 7))
    sns.lineplot(x=data.index, y=data.values, marker='o', linewidth=2, markersize=8, ax=ax)
    ax.set_title(title, fontsize=20)
    ax.set_xlabel(x_label, fontsize=14)
    ax.set_ylabel(y_label, fontsize=14)
    ax.set_xticks(range(0, 24))
    return fig

# -------------------- LAYOUT DASHBOARD --------------------
st.title("Dashboard Analisis Data Penyewaan Sepeda")

# Radio button untuk menentukan apakah akan menampilkan tabel dataframe
show_table = st.sidebar.radio("Tampilkan dataframe?", ("Iya", "Tidak"))

# Buat tab untuk setiap topik
tab_names = [
    "Perbulan",
    "Perhari",
    "Perjam",
    "Per Musim",
    "Kategori Suhu",
    "Hari Kerja",
    "Hari Libur"
]
tabs = st.tabs(tab_names)

# 1) Penyewaan Sepeda Perbulan
with tabs[0]:
    st.subheader("Penyewaan Sepeda Perbulan")
    col1, col2 = st.columns(2)
    with col1:
        fig_month = bar_plot(
            monthly_avg,
            "Rata-Rata Penyewaan Sepeda Per Bulan",
            "Bulan",
            "Rata-Rata Penyewaan Sepeda"
        )
        st.pyplot(fig_month)
    with col2:
        if show_table == "Iya":
            st.dataframe(monthly_df, height=250)

# 2) Penyewaan Sepeda Perhari
with tabs[1]:
    st.subheader("Penyewaan Sepeda Perhari")
    col1, col2 = st.columns(2)
    with col1:
        fig_day = bar_plot(
            daily_avg,
            "Rata-Rata Penyewaan Sepeda Per Hari",
            "Hari",
            "Rata-Rata Penyewaan Sepeda"
        )
        st.pyplot(fig_day)
    with col2:
        if show_table == "Iya":
            st.dataframe(daily_agg_df, height=250)

# 3) Penyewaan Sepeda Perjam
with tabs[2]:
    st.subheader("Penyewaan Sepeda Perjam")
    col1, col2 = st.columns(2)
    with col1:
        fig_hour = line_plot(
            hourly_avg,
            "Rata-Rata Penyewaan Sepeda Per Jam",
            "Jam",
            "Rata-Rata Penyewaan Sepeda"
        )
        st.pyplot(fig_hour)
    with col2:
        if show_table == "Iya":
            st.dataframe(hourly_df, height=250)

# 4) Penyewaan Sepeda Per Musim
with tabs[3]:
    st.subheader("Penyewaan Sepeda Setiap Musim")
    col1, col2 = st.columns(2)
    with col1:
        fig_season = bar_plot(
            season_avg,
            "Rata-Rata Penyewaan Sepeda Setiap Musim",
            "Musim",
            "Rata-Rata Penyewaan Sepeda"
        )
        st.pyplot(fig_season)
    with col2:
        if show_table == "Iya":
            st.dataframe(season_df, height=250)

# 5) Penyewaan Sepeda Berdasarkan Kategori Suhu
with tabs[4]:
    st.subheader("Penyewaan Sepeda Berdasarkan Kategori Suhu")
    col1, col2 = st.columns(2)
    with col1:
        fig_temp = bar_plot(
            temp_avg,
            "Rata-Rata Penyewaan Sepeda Berdasarkan Kategori Suhu",
            "Kategori Suhu",
            "Rata-Rata Penyewaan Sepeda"
        )
        st.pyplot(fig_temp)
    with col2:
        if show_table == "Iya":
            st.dataframe(temp_df, height=250)

# 6) Penyewaan Sepeda Berdasarkan Hari Kerja
with tabs[5]:
    st.subheader("Penyewaan Sepeda Berdasarkan Hari Kerja")
    col1, col2 = st.columns(2)
    with col1:
        fig_workday = bar_plot(
            workday_avg,
            "Rata-Rata Penyewaan Sepeda Berdasarkan Hari Kerja",
            "Apakah Hari Kerja?",
            "Rata-Rata Penyewaan Sepeda"
        )
        st.pyplot(fig_workday)
    with col2:
        if show_table == "Iya":
            st.dataframe(working_day_df, height=250)

# 7) Penyewaan Sepeda Berdasarkan Hari Libur
with tabs[6]:
    st.subheader("Penyewaan Sepeda Berdasarkan Hari Libur")
    col1, col2 = st.columns(2)
    with col1:
        fig_holiday = bar_plot(
            holiday_avg,
            "Rata-Rata Penyewaan Sepeda Berdasarkan Hari Libur",
            "Apakah Hari Libur?",
            "Rata-Rata Penyewaan Sepeda"
        )
        st.pyplot(fig_holiday)
    with col2:
        if show_table == "Iya":
            st.dataframe(holiday_df, height=250)
