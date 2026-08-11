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

# 2. OTURUM DURUMU
if 'active_tab' not in st.session_state: st.session_state.active_tab = "Ana Panel"
if 'perf_df' not in st.session_state: st.session_state.perf_df = None

KULLANICI_ISIM = "Celal ŞENOL"
KULLANICI_GOREV = "Şube Şefi"

# ==========================================
# CSS VE TASARIM
# ==========================================
custom_css = """
<style>
    .stApp { background-color: #0B192C !important; color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #1E3E62 !important; }
    .person-card { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px; margin-bottom: 14px; }
    .metric-value { font-size: 19px; font-weight: 700; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================
def norm_name(val):
    if pd.isna(val) or not val: return ""
    return " ".join(str(val).upper().split())

def process_excel_data(df):
    df.columns = df.columns.astype(str).str.strip()
    
    # Sadece "AT Zimmet Personel Adı" olan satırları al
    valid_df = df[df["AT Zimmet Personel Adı"].notna() & (df["AT Zimmet Personel Adı"].astype(str).str.strip() != "")].copy()
    
    valid_df["Norm_Zimmet"] = valid_df["AT Zimmet Personel Adı"].apply(norm_name)
    if "Teslim Eden Personel" in valid_df.columns:
        valid_df["Norm_Teslim"] = valid_df["Teslim Eden Personel"].apply(norm_name)
    else:
        valid_df["Norm_Teslim"] = ""

    # Mantık İşleme
    def evaluate_row(row):
        z = row["Norm_Zimmet"]
        t = row["Norm_Teslim"]
        
        # 3 ve 4. Madde: Eşleşme kontrolü
        if z == t and z != "":
            status = "TESLİM"
        else:
            return "DEVİR", None

        # 5. Madde: Kanal/Açıklama Mantığı
        kanali = str(row.get("Kargo Teslimat Kanalı", "")).strip().upper()
        aciklama = str(row.get("Açıklama", "")).strip().upper()

        if "İMZA" in kanali or "IMZA" in kanali: return status, "İMZA"
        if "SMS" in kanali: return status, "SMS"
        if "KAPIYA" in kanali or "KS" in kanali: return status, "KS"
        if (kanali == "" or kanali == "NAN" or kanali == "NONE") and "POS ENTEGRASYON" in aciklama: return status, "KS-PE"
        
        return status, "DİĞER"

    results = valid_df.apply(evaluate_row, axis=1)
    valid_df["Durum"] = [r[0] for r in results]
    valid_df["Kanal"] = [r[1] for r in results]

    # Özet Tablo Oluşturma
    summary = []
    for norm_p, p_df in valid_df.groupby("Norm_Zimmet"):
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
    uploaded_file = st.file_uploader("📂 AT Zimmet Raporu", type=['csv', 'xlsx'])
    if st.button("📊 Ana Panel"): st.session_state.active_tab = "Ana Panel"
    if st.button("🏃‍♂️ Kurye Performans"): st.session_state.active_tab = "Kurye Performans"

if uploaded_file:
    raw_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
    perf_res, err = process_excel_data(raw_df)
    if not err: st.session_state.perf_df = perf_res

if st.session_state.active_tab == "Ana Panel" and st.session_state.perf_df is not None:
    st.title("📊 Genel Performans")
    st.dataframe(st.session_state.perf_df, use_container_width=True)

elif st.session_state.active_tab == "Kurye Performans" and st.session_state.perf_df is not None:
    st.title("🏃‍♂️ Kurye Performans")
    for _, row in st.session_state.perf_df.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="person-card">
                <h3>{row['Personel']}</h3>
                <p>Zimmet: {row['Zimmet']} | Başarı: %{row['Başarı Oranı']}</p>
                <div>✍️ İMZA: {row['İMZA']} | 📲 SMS: {row['SMS']} | 🚪 KS: {row['KS']} | 💳 KS-PE: {row['KS-PE']}</div>
            </div>
            """, unsafe_allow_html=True)
