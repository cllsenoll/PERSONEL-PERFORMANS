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
# CSS VE TRANSLATE KORUMA KODLARI
# ==========================================
custom_css = """
<style>
    .notranslate {
        translate: no !important;
    }
    .stApp {
        background-color: #070E1E;
        color: #FFFFFF;
    }
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #FFFFFF !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #0B172E !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        height: 48px !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #0A58CA 0%, #032057 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        margin-bottom: 6px !important;
        text-align: left !important;
        padding-left: 15px !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: linear-gradient(135deg, #0D6EFD 0%, #0A58CA 100%) !important;
        border-color: #F57C00 !important;
    }
    .person-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .profile-section {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .avatar-circle {
        width: 62px;
        height: 62px;
        border-radius: 50%;
        border: 2px solid #F57C00;
        object-fit: cover;
        background-color: #0B172E;
    }
    .person-name {
        font-size: 15px;
        font-weight: 700;
        color: #FFFFFF !important;
    }
    .metric-title {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .metric-value {
        font-size: 19px;
        font-weight: 700;
    }
    .channel-badge {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 12px;
        display: inline-block;
        margin-right: 8px;
        margin-top: 8px;
    }
    .badge-val {
        font-weight: 700;
        color: #F57C00 !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# TÜRKÇE TEMİZLEME FONKSİYONU
# ==========================================
def clean_string(text):
    if pd.isna(text) or not text:
        return ""
    text = str(text).upper().strip()
    replacements = {'İ': 'I', 'I': 'I', 'Ş': 'S', 'Ğ': 'G', 'Ü': 'U', 'Ö': 'O', 'Ç': 'C'}
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

def norm_name(val):
    if pd.isna(val) or not val:
        return ""
    return " ".join(str(val).upper().split())

# ==========================================
# OTOMATİK KURYE FOTOĞRAFI ALMA
# ==========================================
def get_courier_photo(courier_name):
    clean_courier = clean_string(courier_name)
    search_dirs = []
    if os.path.exists("kuryeler"):
        search_dirs.append("kuryeler")
    search_dirs.append(".") 

    for target_dir in search_dirs:
        try:
            files = os.listdir(target_dir)
            for file in files:
                file_path = os.path.join(target_dir, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower().replace('.', '')
                    if ext in ['png', 'jpg', 'jpeg', 'webp']:
                        file_name_clean = clean_string(os.path.splitext(file)[0])
                        if file_name_clean == clean_courier:
                            try:
                                with open(file_path, "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode()
                                    mime_type = "image/png" if ext == "png" else f"image/{ext}"
                                    return f"data:{mime_type};base64,{encoded_string}"
                            except Exception:
                                pass

            for file in files:
                file_path = os.path.join(target_dir, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower().replace('.', '')
                    if ext in ['png', 'jpg', 'jpeg', 'webp']:
                        file_name_clean = clean_string(os.path.splitext(file)[0])
                        if file_name_clean and clean_courier and (file_name_clean in clean_courier or clean_courier in file_name_clean):
                            try:
                                with open(file_path, "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode()
                                    mime_type = "image/png" if ext == "png" else f"image/{ext}"
                                    return f"data:{mime_type};base64,{encoded_string}"
                            except Exception:
                                pass
        except Exception:
            continue
                
    return f"https://ui-avatars.com/api/?name={courier_name.replace(' ', '+')}&background=0B172E&color=F57C00&bold=true&size=80"

# ==========================================
# AKILLI VE GELİŞMİŞ DOSYA OKUMA MOTORU
# ==========================================
def smart_read_file(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    encodings = ['cp1254', 'iso-8859-9', 'utf-8-sig', 'utf-8', 'latin1']
    separators = [';', ',', '\t', None]

    for enc in encodings:
        for sep in separators:
            try:
                engine_type = 'python' if sep is None else None
                df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding=enc, engine=engine_type, on_bad_lines='skip')
                if df is not None and len(df.columns) > 1 and len(df) > 0:
                    return df
            except Exception:
                continue

    try:
        return pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    except Exception:
        pass

    try:
        return pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
    except Exception:
        pass

    for enc in ['utf-8', 'cp1254', 'latin1']:
        try:
            dfs = pd.read_html(io.BytesIO(file_bytes), encoding=enc)
            if dfs and len(dfs) > 0:
                return dfs[0]
        except Exception:
            continue

    raise Exception("Dosya yapısı çözümlenemedi. Lütfen dosyanın bozuk olmadığını kontrol edin.")

# ==========================================
# AT ZİMMET İZLEME VERİ İŞLEME MOTORU (TAM KURALLARA GÖRE)
# ==========================================
def process_excel_data(df):
    df.columns = df.columns.astype(str).str.strip()
    req_cols = ["AT Zimmet Personel Adı", "Teslim Eden Personel"]
    missing_cols = [col for col in req_cols if col not in df.columns]
    
    if missing_cols:
        return None, missing_cols

    df["Norm_Zimmet"] = df["AT Zimmet Personel Adı"].apply(norm_name)
    df["Norm_Teslim"] = df["Teslim Eden Personel"].apply(norm_name)

    durum_col = None
    for c in ["Teslim Durumu", "Teslim Saati"]:
        if c in df.columns:
            durum_col = c
            break

    has_aciklama = "Açıklama" in df.columns
    has_kanali = "Kargo Teslimat Kanalı" in df.columns

    def check_devir(row):
        # 1. Teslim Durumu / Saati sütununda "Teslim Edilmedi / Bekletiliyor" geçiyorsa devirdir.
        if durum_col:
            d_val = str(row[durum_col]).strip().upper()
            if "BEKLETİLİYOR" in d_val or "EDİLMEDİ" in d_val or "BEKLETILIYOR" in d_val or "EDILMEDI" in d_val:
                return True
        
        z = row["Norm_Zimmet"]
        t = row["Norm_Teslim"]
        
        # 2. Teslim Eden Personel dolu ve AT Zimmet Personelinden farklıysa devirdir.
        if t != "" and t != z:
            return True
            
        # 3. Teslim Eden Personel boşsa veya aynı isimse teslim edilmiştir (devir değildir).
        return False

    df["Is_Devir"] = df.apply(check_devir, axis=1)

    def get_channel_type(row):
        if row["Is_Devir"] == True:
            return "DEVİR"

        kanali = str(row["Kargo Teslimat Kanalı"]).strip().upper() if has_kanali else ""
        aciklama = str(row["Açıklama"]).strip().upper() if has_aciklama else ""

        if "İMZA" in kanali or "IMZA" in kanali:
            return "İMZA"
        elif "SMS" in kanali:
            return "SMS"
        elif "KAPIYA" in kanali or "KAPIYA BIRAKILDI" in kanali:
            return "KS"
        elif (kanali == "" or kanali == "NAN") and "POS ENTEGRASYON" in aciklama:
            return "KS-PE"
        
        if "İMZA" in aciklama or "IMZA" in aciklama:
            return "İMZA"
        elif "SMS" in aciklama:
            return "SMS"
        elif "KAPIYA" in aciklama:
            return "KS"
            
        return "DİĞER"

    df["Custom_Channel"] = df.apply(get_channel_type, axis=1)

    # 1. Kural: Yalnızca AT Zimmet Personel Adı sütununda adı geçen geçerli personeller
    valid_df = df[
        df["Norm_Zimmet"].notna() & 
        (df["Norm_Zimmet"] != "") & 
        (df["Norm_Zimmet"] != "NAN") & 
        (df["Norm_Zimmet"] != "NONE")
    ].copy()
    
    personnel_groups = valid_df.groupby("Norm_Zimmet")
    
    summary = []
    for norm_p, p_df in personnel_groups:
        p_name = p_df["AT Zimmet Personel Adı"].mode()[0] if not p_df["AT Zimmet Personel Adı"].mode().empty else norm_p
        p_name = " ".join(str(p_name).split())
        
        # 2. Kural: Satır sayısı = Zimmetli kargo sayısı
        zimmet_cnt = len(p_df)
        
        # 4. Kural: Devir (Teslim Edilemeyen) sayısı
        devir_df = p_df[p_df["Is_Devir"] == True]
        teslim_edilemeyen_cnt = len(devir_df)
        
        # 3. Kural: Teslim Edilen sayısı
        teslim_cnt = zimmet_cnt - teslim_edilemeyen_cnt
        if teslim_cnt < 0:
            teslim_cnt = 0
        
        success_rate = round((teslim_cnt / zimmet_cnt) * 100, 1) if zimmet_cnt > 0 else 0.0
        
        # 5. Kural: Kanal Bazlı Dağılımlar
        teslim_edilen_df = p_df[p_df["Is_Devir"] == False]
        imza_cnt = len(teslim_edilen_df[teslim_edilen_df["Custom_Channel"] == "İMZA"])
        sms_cnt = len(teslim_edilen_df[teslim_edilen_df["Custom_Channel"] == "SMS"])
        ks_cnt = len(teslim_edilen_df[teslim_edilen_df["Custom_Channel"] == "KS"])
        ks_pe_cnt = len(teslim_edilen_df[teslim_edilen_df["Custom_Channel"] == "KS-PE"])

        summary.append({
            "Personel": p_name,
            "Zimmet": zimmet_cnt,
            "Teslim Edilen": teslim_cnt,
            "Teslim Edilemeyen": teslim_edilemeyen_cnt,
            "Başarı Oranı": success_rate,
            "İMZA": imza_cnt,
            "SMS": sms_cnt,
            "KS": ks_cnt,
            "KS-PE": ks_pe_cnt
        })

    res_df = pd.DataFrame(summary)
    if not res_df.empty:
        res_df.index = range(1, len(res_df) + 1)
        
    return res_df, None

# ==========================================
# SIDEBAR VE GEZİNTİ MENÜSÜ
# ==========================================
with st.sidebar:
    st.markdown("""
    <div class="notranslate" style="text-align: center; padding-bottom: 10px;">
        <h2 style="margin: 0; color: #FFFFFF;">Yurtiçi Kargo</h2>
        <h4 style="margin: 0; color: #F57C00;">Görükle Acente KOYS</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="notranslate" style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 15px;">
        <small style="color: #F57C00;">Aktif Kullanıcı:</small><br>
        <strong>{KULLANICI_ISIM}</strong> ({KULLANICI_GOREV})
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📂 AT Zimmet Raporu Yükle", type=['csv', 'xlsx', 'xls', 'html'])
    
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    if st.button("📊 Ana Panel"):
        st.session_state.active_tab = "Ana Panel"
    if st.button("🏃‍♂️ Kurye Performans"):
        st.session_state.active_tab = "Kurye Performans"

# ==========================================
# AKILLI VERİ DAĞITIM VE İŞLEME MİMARİSİ
# ==========================================
if uploaded_file is not None:
    try:
        raw_df = smart_read_file(uploaded_file)
        st.session_state.raw_df = raw_df
        
        perf_res, err = process_excel_data(raw_df)
        if err:
            st.error(f"❌ Eksik Sütunlar: {err}")
        else:
            st.session_state.perf_df = perf_res
    except Exception as e:
        st.error(f"❌ Dosya Okuma/İşleme Hatası: {e}")

# ==========================================
# TAB 1: ANA PANEL
# ==========================================
if st.session_state.active_tab == "Ana Panel":
    st.title("📊 Görükle Acente - Genel Performans Özeti")
    
    perf_df = st.session_state.perf_df
    if perf_df is not None and not perf_df.empty:
        total_zimmet = perf_df["Zimmet"].sum()
        total_teslim = perf_df["Teslim Edilen"].sum()
        total_devir = perf_df["Teslim Edilemeyen"].sum()
        avg_rate = round((total_teslim / total_zimmet) * 100, 1) if total_zimmet > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 Toplam Zimmet", f"{total_zimmet:,}")
        c2.metric("✅ Teslim Edilen", f"{total_teslim:,}")
        c3.metric("🚨 Devir / Teslim Edilemeyen", f"{total_devir:,}")
        c4.metric("🎯 Genel Başarı Oranı", f"%{avg_rate}")
        
        st.markdown("---")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Kurye Başarı Oranları (%)")
            chart_df = perf_df.set_index("Personel")[["Başarı Oranı"]]
            st.bar_chart(chart_df)
            
        with col_right:
            st.subheader("📲 Teslimat Kanalları Dağılımı")
            channel_df = pd.DataFrame({
                "Kanal": ["İMZA", "SMS", "KS", "KS-PE"],
                "Adet": [perf_df["İMZA"].sum(), perf_df["SMS"].sum(), perf_df["KS"].sum(), perf_df["KS-PE"].sum()]
            }).set_index("Kanal")
            st.bar_chart(channel_df)
            
        st.subheader("📋 Genel Performans Tablosu")
        st.dataframe(perf_df, use_container_width=True)
        
    else:
        st.info("💡 Sol menüden **AT ZİMMET İZLEME** dosyanızı yükleyerek ana paneli görüntüleyebilirsiniz.")

# ==========================================
# TAB 2: KURYE PERFORMANS PANELİ
# ==========================================
elif st.session_state.active_tab == "Kurye Performans":
    st.title("🏃‍♂️ Kurye Performans Paneli")
    
    perf_df = st.session_state.perf_df
    if perf_df is not None and not perf_df.empty:
        st.success(f"✅ AT ZİMMET İZLEME raporu aktif. Toplam **{len(perf_df)}** kurye bulundu.")
        
        all_personnel = ["Tümü"] + sorted(perf_df["Personel"].dropna().unique().tolist())
        selected_personnel = st.selectbox("🔍 Personel Seçerek Süzgeçle:", all_personnel)
        
        if selected_personnel != "Tümü":
            filtered_perf_df = perf_df[perf_df["Personel"] == selected_personnel]
        else:
            filtered_perf_df = perf_df
            
        for idx, row in filtered_perf_df.iterrows():
            p_name = row["Personel"]
            zimmet = row["Zimmet"]
            teslim = row["Teslim Edilen"]
            devir = row["Teslim Edilemeyen"]
            rate = row["Başarı Oranı"]
            imza = row["İMZA"]
            sms = row["SMS"]
            ks = row["KS"]
            ks_pe = row["KS-PE"]

            avatar_url = get_courier_photo(p_name)

            card_html = f"""
            <div class="person-card notranslate">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                    <div class="profile-section" style="min-width: 220px;">
                        <img src="{avatar_url}" class="avatar-circle">
                        <div>
                            <div class="person-name">{p_name}</div>
                            <small style="color: #F57C00;">Saha Kuryesi</small>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div class="metric-title">Zimmet Sayısı</div>
                        <div class="metric-value" style="color: #FFFFFF;">{zimmet}</div>
                    </div>
                    <div style="text-align: center;">
                        <div class="metric-title">Teslim Edilen</div>
                        <div class="metric-value" style="color: #4CAF50;">{teslim}</div>
                    </div>
                    <div style="text-align: center;">
                        <div class="metric-title">Teslim Edilemeyen</div>
                        <div class="metric-value" style="color: #F44336;">{devir}</div>
                    </div>
                    <div style="text-align: center; min-width: 80px;">
                        <div class="metric-title">Başarı Oranı</div>
                        <div class="metric-value" style="color: #F57C00;">%{rate}</div>
                    </div>
                </div>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.06);">
                    <div class="channel-badge">✍️ İMZA: <span class="badge-val">{imza}</span></div>
                    <div class="channel-badge">📲 SMS: <span class="badge-val">{sms}</span></div>
                    <div class="channel-badge">🚪 KS: <span class="badge-val">{ks}</span></div>
                    <div class="channel-badge">💳 KS-PE: <span class="badge-val">{ks_pe}</span></div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Kurye performans kartlarını görmek için sol menüden **AT ZİMMET İZLEME** dosyasını yükleyin.")
