import streamlit as st
import pandas as pd
import io
import os
import base64
import re

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(
    page_title="Görükle Acente - Kurye Performans",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. OTURUM DURUMU (Session State)
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Ana Panel"
if 'perf_df' not in st.session_state:
    st.session_state.perf_df = None
if 'raw_df' not in st.session_state:
    st.session_state.raw_df = None

KULLANICI_ISIM = "Celal ŞENOL"
KULLANICI_GOREV = "Şube Şefi"

# ==========================================
# CSS VE MODERN GÖRSEL BİLEŞEN TASARIMLARI
# ==========================================
custom_css = """
<style>
    .notranslate { translate: no !important; }
    .stApp { background-color: #0B192C !important; color: #FFFFFF !important; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #FFFFFF !important; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1E3E62 !important; border-right: 1px solid rgba(255, 255, 255, 0.08); }
    [data-testid="stSidebar"] div.stButton > button { width: 100% !important; height: 48px !important; border-radius: 10px !important; font-weight: 600 !important; background: linear-gradient(135deg, #00B4D8 0%, #0077B6 100%) !important; color: #FFFFFF !important; border: 1px solid #90E0EF !important; box-shadow: 0 6px 0 #03045E, 0 8px 10px rgba(0, 0, 0, 0.4) !important; margin-bottom: 10px !important; text-align: left !important; padding-left: 15px !important; }
    [data-testid="stFileUploader"] section { background: linear-gradient(135deg, #FFD166 0%, #FFB703) !important; border: 2px dashed #FB8500 !important; border-radius: 12px !important; }
    [data-testid="stFileUploader"] section * { color: #000000 !important; }
    .person-card { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); }
    .dashboard-card { background: linear-gradient(135deg, #162A45 0%, #0B192C 100%); border: 1px solid rgba(255, 183, 3, 0.3); border-radius: 16px; padding: 24px; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
    .progress-bar-fill-orange { background: linear-gradient(90deg, #FB8500 0%, #FFB703 100%); height: 10px; border-radius: 6px; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================
def clean_string(text):
    if pd.isna(text) or not text: return ""
    text = str(text).upper().strip()
    replacements = {'İ': 'I', 'I': 'I', 'Ş': 'S', 'Ğ': 'G', 'Ü': 'U', 'Ö': 'O', 'Ç': 'C'}
    for search, replace in replacements.items(): text = text.replace(search, replace)
    return re.sub(r'[^A-Z0-9]', '', text)

def norm_name(val):
    if pd.isna(val) or not val: return ""
    return " ".join(str(val).upper().split())

def get_courier_photo(courier_name):
    # Basit bir placeholder dönüşü
    return f"https://ui-avatars.com/api/?name={courier_name.replace(' ', '+')}&background=1E3E62&color=FFB703&bold=true&size=80"

# ==========================================
# İŞLEME MOTORU (GÜNCELLENDİ)
# ==========================================
def process_excel_data(df):
    df.columns = df.columns.astype(str).str.strip()
    req_cols = ["AT Zimmet Personel Adı", "Teslim Eden Personel"]
    if any(col not in df.columns for col in req_cols):
        return None, req_cols

    # Sadece geçerli personeli olan satırları al
    valid_df = df[df["AT Zimmet Personel Adı"].notna() & (df["AT Zimmet Personel Adı"].astype(str).str.strip() != "")].copy()

    valid_df["Norm_Zimmet"] = valid_df["AT Zimmet Personel Adı"].apply(norm_name)
    valid_df["Norm_Teslim"] = valid_df["Teslim Eden Personel"].apply(norm_name)

    has_kanali = "Kargo Teslimat Kanalı" in valid_df.columns
    has_aciklama = "Açıklama" in valid_df.columns

    def evaluate_row(row):
        z = row["Norm_Zimmet"]
        t = row["Norm_Teslim"]
        # Teslim eden kişi, zimmetli kişiyle aynı değilse DEVİR
        if t == "" or t != z:
            return "DEVİR", ""
        
        kanali = str(row["Kargo Teslimat Kanalı"]).strip().upper() if has_kanali else ""
        aciklama = str(row["Açıklama"]).strip().upper() if has_aciklama else ""

        if "İMZA" in kanali or "IMZA" in kanali: return "TESLİM", "İMZA"
        if "SMS" in kanali: return "TESLİM", "SMS"
        if "KAPIYA" in kanali or "KS" in kanali: return "TESLİM", "KS"
        if "POS" in aciklama or "PE" in aciklama: return "TESLİM", "KS-PE"
        return "TESLİM", "DİĞER"

    results = valid_df.apply(evaluate_row, axis=1)
    valid_df["Durum"] = [r[0] for r in results]
    valid_df["Kanal"] = [r[1] for r in results]

    summary = []
    for norm_p, p_df in valid_df.groupby("Norm_Zimmet"):
        p_name = p_df["AT Zimmet Personel Adı"].iloc[0]
        zimmet_cnt = len(p_df)
        teslim_df = p_df[p_df["Durum"] == "TESLİM"]
        
        summary.append({
            "Personel": p_name,
            "Zimmet": zimmet_cnt,
            "Teslim Edilen": len(teslim_df),
            "Teslim Edilemeyen": len(p_df[p_df["Durum"] == "DEVİR"]),
            "Başarı Oranı": round((len(teslim_df) / zimmet_cnt) * 100, 1),
            "İMZA": len(teslim_df[teslim_df["Kanal"] == "İMZA"]),
            "SMS": len(teslim_df[teslim_df["Kanal"] == "SMS"]),
            "KS": len(teslim_df[teslim_df["Kanal"] == "KS"]),
            "KS-PE": len(teslim_df[teslim_df["Kanal"] == "KS-PE"])
        })

    return pd.DataFrame(summary), None

def smart_read_file(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    try: return pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    except: return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python')

# ==========================================
# SIDEBAR VE ARAYÜZ
# ==========================================
with st.sidebar:
    st.markdown("## Yurtiçi Kargo Görükle KOYS")
    uploaded_file = st.file_uploader("📂 AT Zimmet Raporu Yükle", type=['csv', 'xlsx', 'xls'])
    if st.button("📊 Ana Panel"): st.session_state.active_tab = "Ana Panel"
    if st.button("🏃‍♂️ Kurye Performans"): st.session_state.active_tab = "Kurye Performans"

if uploaded_file is not None:
    raw_df = smart_read_file(uploaded_file)
    perf_res, err = process_excel_data(raw_df)
    if err: st.error(f"Eksik Sütunlar: {err}")
    else: st.session_state.perf_df = perf_res

# ==========================================
# ANA SAYFA
# ==========================================
if st.session_state.active_tab == "Ana Panel":
    st.title("📊 Genel Performans Özeti")
    if st.session_state.perf_df is not None:
        perf_df = st.session_state.perf_df
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Zimmet", f"{perf_df['Zimmet'].sum():,}")
        c2.metric("Teslim Edilen", f"{perf_df['Teslim Edilen'].sum():,}")
        c3.metric("Teslim Edilemeyen", f"{perf_df['Teslim Edilemeyen'].sum():,}")
        st.dataframe(perf_df, use_container_width=True)

elif st.session_state.active_tab == "Kurye Performans":
    st.title("🏃‍♂️ Kurye Performans Paneli")
    if st.session_state.perf_df is not None:
        perf_df = st.session_state.perf_df
        for _, row in perf_df.iterrows():
            with st.container():
                st.write(f"### {row['Personel']}")
                st.write(f"Başarı Oranı: %{row['Başarı Oranı']} | Zimmet: {row['Zimmet']}")
                st.markdown("---")
