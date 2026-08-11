import streamlit as st
import pandas as pd
import io
import re

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(
    page_title="Görükle Acente - Kurye Performans",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. OTURUM DURUMU
if 'active_tab' not in st.session_state: st.session_state.active_tab = "Ana Panel"
if 'perf_df' not in st.session_state: st.session_state.perf_df = None

# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================
def norm_name(val):
    if pd.isna(val) or not val: return ""
    return " ".join(str(val).upper().split())

def process_excel_data(df):
    df.columns = df.columns.astype(str).str.strip()
    
    # 1. Sadece "AT Zimmet Personel Adı" dolu olanları al
    df = df[df["AT Zimmet Personel Adı"].notna() & (df["AT Zimmet Personel Adı"].astype(str).str.strip() != "")].copy()
    
    df["Norm_Zimmet"] = df["AT Zimmet Personel Adı"].apply(norm_name)
    df["Norm_Teslim"] = df["Teslim Eden Personel"].apply(norm_name) if "Teslim Eden Personel" in df.columns else ""
    
    # İşleme Mantığı
    def evaluate_row(row):
        z = row["Norm_Zimmet"]
        t = row["Norm_Teslim"]
        aciklama = str(row.get("Açıklama", "")).strip().upper()
        kanali = str(row.get("Kargo Teslimat Kanalı", "")).strip().upper()

        # İsim eşleşiyorsa TESLİM
        if z == t and z != "":
            status = "TESLİM"
            if "İMZA" in kanali: return status, "İMZA"
            if "SMS" in kanali: return status, "SMS"
            if "KAPIYA" in kanali or "KS" in kanali: return status, "KS"
            return status, "DİĞER"
        
        # İsim eşleşmiyorsa POS Entegrasyon kontrolü
        else:
            if "POS ENTEGRASYON" in aciklama:
                return "TESLİM", "KS-PE"
            return "DEVİR", None

    results = df.apply(evaluate_row, axis=1)
    df["Durum"] = [r[0] for r in results]
    df["Kanal"] = [r[1] for r in results]

    # Özetleme
    summary = []
    for norm_p, p_df in df.groupby("Norm_Zimmet"):
        zimmet_cnt = len(p_df)
        teslim_df = p_df[p_df["Durum"] == "TESLİM"]
        
        summary.append({
            "Personel": p_df["AT Zimmet Personel Adı"].iloc[0],
            "Zimmet": zimmet_cnt,
            "Teslim Edilen": len(teslim_df),
            "Teslim Edilemeyen": len(p_df[p_df["Durum"] == "DEVİR"]),
            "Başarı Oranı": round((len(teslim_df) / zimmet_cnt) * 100, 1) if zimmet_cnt > 0 else 0,
            "İMZA": len(teslim_df[teslim_df["Kanal"] == "İMZA"]),
            "SMS": len(teslim_df[teslim_df["Kanal"] == "SMS"]),
            "KS": len(teslim_df[teslim_df["Kanal"] == "KS"]),
            "KS-PE": len(teslim_df[teslim_df["Kanal"] == "KS-PE"])
        })
    return pd.DataFrame(summary), None

# ==========================================
# ARAYÜZ
# ==========================================
with st.sidebar:
    st.markdown("## Görükle Acente KOYS")
    uploaded_file = st.file_uploader("📂 AT Zimmet Raporu Yükle", type=['csv', 'xlsx'])
    if st.button("📊 Ana Panel"): st.session_state.active_tab = "Ana Panel"
    if st.button("🏃‍♂️ Kurye Performans"): st.session_state.active_tab = "Kurye Performans"

if uploaded_file:
    raw_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
    perf_res, _ = process_excel_data(raw_df)
    st.session_state.perf_df = perf_res

if st.session_state.perf_df is not None:
    if st.session_state.active_tab == "Ana Panel":
        st.title("📊 Genel Performans")
        st.dataframe(st.session_state.perf_df, use_container_width=True)
    else:
        st.title("🏃‍♂️ Kurye Performans")
        for _, row in st.session_state.perf_df.iterrows():
            st.markdown(f"**{row['Personel']}** - Başarı: %{row['Başarı Oranı']} | Zimmet: {row['Zimmet']} | Teslim: {row['Teslim Edilen']} | Devir: {row['Teslim Edilemeyen']}")
            st.markdown(f"Detay: İMZA: {row['İMZA']} | SMS: {row['SMS']} | KS: {row['KS']} | KS-PE: {row['KS-PE']}")
            st.divider()
