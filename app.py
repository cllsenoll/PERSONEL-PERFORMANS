import streamlit as st
import pandas as pd
import io
import re

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(
    page_title="Görükle Acente - Hesap & F4 Paneli",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. OTURUM DURUMU (Session State)
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "HESAP"
if 'account_df' not in st.session_state:
    st.session_state.account_df = None
if 'hesap_df' not in st.session_state:
    st.session_state.hesap_df = None
if 'kasa_miktari' not in st.session_state:
    st.session_state.kasa_miktari = 0.0
if 'raw_df' not in st.session_state:
    st.session_state.raw_df = None
if 'f4_df' not in st.session_state:
    st.session_state.f4_df = None

KULLANICI_ISIM = "Celal ŞENOL"
KULLANICI_GOREV = "Şube Şefi"

# ==========================================
# MÜŞTERİ - PERSONEL EŞLEŞTİRME SÖZLÜĞÜ
# ==========================================
MUSTERI_PERSONEL_MAP = {
    "KÜBRA AYDEMİR": "AHMET BERKAN ÖKSÜZ",
    "SERKAN KUYUMCU": "AHMET BERKAN ÖKSÜZ",
    "AKSUN AĞAÇ AMBALAJ KERESTE SAN. TİC.LTD.ŞTİ": "ALATTİN CEBECİ",
    "ARTEA DIŞ TİCARET MAKİNA SANAYİ LİMİTED ŞİRKETİ": "ALATTİN CEBECİ",
    "BAYAGRO TARIM İLAÇLARI SANAYİ VE TİCARETLTD. ŞTİ.": "ALATTİN CEBECİ",
    "BEREKET İLAÇ KOZMETİK SANAYİ VE TİCARET ANONİM ŞİRKETİ": "ALATTİN CEBECİ",
    "BURMOD TEKSTİL SAN.TİC.A.Ş.-BURSA ŞB.": "ALATTİN CEBECİ",
    "DEMİRCİOĞLU ŞASE ENDÜSTRİYEL YAĞ OTOMOTİV TEKSTİL GIDA İNŞAAT SANAYİ VE TİCARET A.Ş.": "ALATTİN CEBECİ",
    "EDDA MAKİNE AMBALAJ NAKLİYE İNŞAAT KİMYA SANAYİ TİCARET LİMİTED ŞİRKETİ": "ALATTİN CEBECİ",
    "FLY MOBİLYA SANAYİ VE TİCARET ANONİM ŞİRKETİ": "ALATTİN CEBECİ",
    "KOLİSAN AMBALAJ SANAYİ VE TİCARET A.Ş.": "ALATTİN CEBECİ",
    "M-BEND METAL ÇELİK MAKİNA İNŞAAT SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "ALATTİN CEBECİ",
    "MAVİFORM METAL KALIPFİKSTÜR VE APARAT SAN.VE TİC.LTD": "ALATTİN CEBECİ",
    "MERZE MOBİLYA TASARIM İNŞAAT SANAYİ TİCARET ANONİM ŞİRKETİ": "ALATTİN CEBECİ",
    "MNC BİTKİSEL VE SAĞLIK ÜRÜNLERİ REKLAM VE ORGANİZASYON BİLİŞİM TEKNOLOJİLERİ İNŞAAT SAN.TİC.LTD.ŞTİ.": "ALATTİN CEBECİ",
    "SOMBURSA BAĞLANTI ELEMANLARI TİCARET VESAN.VE A.Ş.": "ALATTİN CEBECİ",
    "ÖZBEYAZ DIŞ TİCARET TAŞIMACILIK ANONİM ŞİRKETİ": "ALATTİN CEBECİ",
    "ALPER ŞEN": "BURCU DÜREN",
    "ALSTOM RAYLI SİSTEM SANAYİ ANONİM ŞİRKETİ": "BURCU DÜREN",
    "AMPHENOL TURKEY BAĞLANTI ÇÖZÜMLERİ LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "BAŞATLAR ORMAN ÜRÜNLERİ VE AMBALAJ SAN.TİC.LTD.ŞTİ.": "BURCU DÜREN",
    "D.K.C TEKNİK KAPLAMA APRE TEKSTİL KONFEKSİYON SERVİS TAŞIMACILIĞI SAN.VE TİC.LTD.ŞTİ.": "BURCU DÜREN",
    "DEBSA TASARIM KONFEKSİYON TEKSTİL SANAYİ TİCARET ANONİM ŞİRKETİ": "BURCU DÜREN",
    "DEVSAN ENDÜSTRİYEL OTOMASYON MAKİNA SANAYİ VE TİCARET A.Ş.": "BURCU DÜREN",
    "DOĞANYİĞİTLER ORGANİK GIDA SANAYİ TİCARET LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "DİLAN YILDIRIM - OLİNA BUTİK": "BURCU DÜREN",
    "ESAUTOMOTION MEKATRONİK SANAYİ VE TİCARET ANONİM ŞİRKETİ": "BURCU DÜREN",
    "GENÇ GÖZDE TARIM MAKİNALARI SANAYİ VE TİC.LTD.ŞTİ.": "BURCU DÜREN",
    "GÜMÜŞ ARSLAN GENEL MAKİNE İMALATI ENERJİ VE ISI SİSTEMLERİ SANAYİ TİCARET LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "HMT MAKİNA SANAYİ VE TİCARET ANONİM ŞİRKETİ": "BURCU DÜREN",
    "JACQUARD FASHİON KONFEKSİYON TEKSTİL SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "KCL LOJİSTİK OTOMOTİV SANAYİ TİCARET LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "MATAY OTOMOTİV YAN SANAYİ VE TİCARET A .Ş.": "BURCU DÜREN",
    "MİNTEKS TEKSTİL SAN VE TİC. LTD.ŞTİ. İŞLETME ADI:MİNTEKS": "BURCU DÜREN",
    "MS MOTION OTOMOTİV ANONİM ŞİRKETİ": "BURCU DÜREN",
    "NOBEL TEKNİK OTO YANSANAYİ VE TİCARET A.Ş.": "BURCU DÜREN",
    "ORCA HOME TEKSTİL İTHALAT İHRACATSANAYİ VE TİCARET LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "OTEKSO MÜHENDİSLİK TASARIM MAKİNE SANAYİ VE TİCARET ANONİM ŞİRKETİ": "BURCU DÜREN",
    "PROLİFT ASANSÖR SANAYİ VE TİCARET ANONİM ŞİRKETİ": "BURCU DÜREN",
    "S.S.MARMARA ZEYTİN TARIM SAT.KOOP.BİR.MARMARABİRLİK": "BURCU DÜREN",
    "T-BİYOTEKNOLOJİ LABORATUVAR ESTETİK MEDİKAL KOZMETİK SANAYİVE TİCARET LTD.ŞTİ.": "BURCU DÜREN",
    "UĞURLU FİNİSAJ SİSTEMLERİ SANAYİ VE TİCARET ANONİM ŞİRKETİ": "BURCU DÜREN",
    "VARNA DERİ SANAYİ VE TİCARET A.Ş.": "BURCU DÜREN",
    "VETABİL GIDA TARIM HAYVANCILIK LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "ÖZGÜR ULUS - MARANGOZ": "BURCU DÜREN",
    "İLK-SEZ ENDÜSTRİYEL OTOMASYON SİSTEMLERİ ELEKTRİK ELEKTRONİK MAKİNA SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "BURCU DÜREN",
    "ALTINSOY MADENCİLİKVE TİCARET A.Ş.": "CELAL ŞENOL",
    "ENDER DURSAK": "CELAL ŞENOL",
    "KAPLANLAR SOĞUTMA SAN.VE TİC.AŞ.": "CELAL ŞENOL",
    "NARVİN TEKSTİL EMLAK KOZMETİK SOSYAL MEDYA İHRACAT İTHALAT SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "CELAL ŞENOL",
    "SELFİE TARIMSAL TEDARİK SERACILIK DEPOCULUK DANIŞMANLIK SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "CELAL ŞENOL",
    "SERGEN GÖRÜROĞLU": "CELAL ŞENOL",
    "ARMENDUS OPERATÖR KOL VE PANO SİSTEMLERİ SANAYİ VE TİCARET ANONİM ŞİRKETİ": "HASAN SAĞLAM",
    "BAROMAK MAKİNE SANAYİ TİCARET LİMİTED ŞİRKETİ": "HASAN SAĞLAM",
    "BİLEKLER İNŞAAT MAKİNALARI SANAYİ VETİCARET LTD.ŞTİ.": "HASAN SAĞLAM",
    "BURKON MOBİLYA SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "HASAN SAĞLAM",
    "DICHERSEAL ELASTOMER TEKNOLOJİLERİ SANAYİ TİCARET LİMİTED ŞİRKETİ": "HASAN SAĞLAM",
    "DİGİTORİUM ELEKTRONİK TEKNOLOJİLERİ ANONİM ŞİRKETİ": "HASAN SAĞLAM",
    "ELECTRA KABLOSİSTEMLERİ SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "HASAN SAĞLAM",
    "ELECTRA GRUP MÜHENDİSLİK ELEKTRİK TAAHHÜT MEKANİK PANO İMALAT İTHALAT İHRACAT SANAYİ VE TİCARET ANONİM ŞİRKETİ": "HASAN SAĞLAM",
    "ELECTRA PROJE ELEKTRİK MÜHENDİSLİK TAAHHÜT İNŞAAT ARAÇ KİRALAMA İTHALAT İHRACAT VE TİCARET ANONİM ŞİRKETİ": "HASAN SAĞLAM",
    "F.S.K.MAKİNE İMALATTAAH.VE GIDA TEKN.SAN.T.LTD.ŞTİ.": "HASAN SAĞLAM",
    "IPM GALVANO YÜZEY KAPLAMA SANAYİ VE TİCARET ANONİM ŞİRKETİ": "HASAN SAĞLAM",
    "LİGNUM AĞAÇ MAKİNELERİ SANAYİ TİCARET LİMİTED ŞİRKETİ": "HASAN SAĞLAM",
    "TEMPOLİFT ASANSÖR ELEKTRİK ELEKTRONİK SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "HASAN SAĞLAM",
    "TURKAUTO MOTORLU ARAÇLAR SANAYİ VE TİCARET LİMİTED ŞİRKETİ.": "HASAN SAĞLAM",
    "VİYA OTOMOTİV CAM TURİZM DENİZCİLİK SANAYİ VE TİCARET LTD. ŞTİ.": "HASAN SAĞLAM",
    "YSL OTOMOTİV YAN SANAYİ VE TİCARET ANONİM ŞİRKETİ": "HASAN SAĞLAM",
    "ÖZGÖZDE OTOMOTİV İNŞAAT İŞ MAKİNALARI PETROL NAKLİYE VE TURİZM HİZMETLERİ SANAYİ TİCARET A.Ş.": "HASAN SAĞLAM",
    "ACH DIŞ TİCARET SANAYİ VE TİCARET ANONİM ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "AKEL DERİ TEKS.SAN.VE DIŞ TİC.LTD.ŞTİ.": "SERGEN GÖRÜROĞLU",
    "AYDEMİR DERİ SANAYİ VE TİCARET ANONİM ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "BURSA DERİ İHTİSAS VE KARMA ORGANİZE SANAYİ BÖLGESİ": "SERGEN GÖRÜROĞLU",
    "BURSA JELATİN GIDA SANAYİ VE TİCARET ANONİM ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "CİVAN GERİ DÖNÜŞÜM İZOLASYON PLASTİK METAL,İNŞAAT TAAH.SAN.VE TİC.LTD.ŞTİ.": "SERGEN GÖRÜROĞLU",
    "EMRE DERELİ - DERELİ MARİNE": "SERGEN GÖRÜROĞLU",
    "ERBA FİNİSAJ DERİ SANAYİ VE TİCARET LTD.ŞTİ.": "SERGEN GÖRÜROĞLU",
    "GESU ARITMA SİSTEMLERİ SANAYİ VE TİCARET LTD.ŞTİ.": "SERGEN GÖRÜROĞLU",
    "LAS-SAN LASTİK PLASTİK SANAYİ VE TİCARET ANONİM ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "MECANICA CNC MAKİNE VE SERVİS LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "MET-RİN DERİ MAKİNELERİ VE METAL SANAYİ TİCARET LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "MORKİM KİMYA İNŞAAT İTHALAT İHRACAT SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "MURSAN FİBERGLASS VE DENİZ ARAÇLARI TURİZM SANAYİ TİCARET PAZARLAMA LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "NOVMA KİMYA SANAYİ TİCARET LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "VAKETA DERİCİLİK SANAYİ VE TİCARET ANONİM ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "YILDIZ GRUBU DERİ KİMYA İNŞAAT TARIM SANAYİ VE DIŞ TİCARET LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "İDEA ENDÜSTRİYEL KİMYA SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "İNVENTA GIDA SANAYİ VE TİCARET LİMİTED ŞİRKETİ": "SERGEN GÖRÜROĞLU",
    "ERKAN DEMİRCAN": "SUAT ARI",
    "NUR ALUÇLUOĞLU - NUR TERZİ": "SUAT ARI",
    "YERLİYURT MARİN DENİZ ARAÇ KAB.TUR.SVE P.LTD.ŞTİ.": "SUAT ARI",
    "ÖZBAYRAK KIZAK KORUMA SİSTEMLERİ ENDÜSTRİ MAKİNE SANAYİ VE TİCARET ANONİM ŞİRKETİ": "SUAT ARI"
}

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
    .kasa-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px;
        margin-top: 20px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# TÜRKÇE TEMİZLEME VE PARS FONKSİYONLARI
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

def parse_turkish_float(val):
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.upper() in ['NAN', 'NONE', '-', '0', '0.0', '0,0']:
        return 0.0
    s = s.replace(' ', '').replace('₺', '').replace('TL', '')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

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
# PERSONEL HESAP ALIMI EKRANI PARSER
# ==========================================
def process_personnel_account_data(df):
    header_idx = 0
    for idx, row in df.iterrows():
        row_str = " ".join([str(val).upper() for val in row.values])
        if "PERSONEL" in row_str or "NAKİT" in row_str or "FT" in row_str or "ÖDEME" in row_str:
            header_idx = idx
            break
            
    if header_idx > 0:
        df.columns = df.iloc[header_idx].astype(str).str.strip()
        df = df.iloc[header_idx + 1:].reset_index(drop=True)
    else:
        df.columns = df.columns.astype(str).str.strip()

    cols_to_drop = [c for c in df.columns if "AÇIKLAMA" in str(c).upper() or "ACIKLAMA" in str(c).upper()]
    df = df.drop(columns=cols_to_drop, errors='ignore')

    p_col, ft_col, odeme_col, banka_col = None, None, None, None

    for col in df.columns:
        c_upper = str(col).upper()
        if ("PERSONEL" in c_upper or "AD" in c_upper or "KURYE" in c_upper) and not p_col:
            p_col = col
        elif (("FT" in c_upper or "FATURA" in c_upper) and not ("AD" in c_upper or "ADET" in c_upper)) and not ft_col:
            ft_col = col
        elif ("ÖDEME" in c_upper or "ODEME" in c_upper) and not odeme_col:
            odeme_col = col
        elif ("BANKA" in c_upper or "ATM" in c_upper or "POS" in c_upper) and not banka_col:
            banka_col = col

    cols_list = list(df.columns)
    if not p_col and len(cols_list) > 0: p_col = cols_list[0]
    if not ft_col and len(cols_list) > 1: ft_col = cols_list[1]
    if not odeme_col and len(cols_list) > 2: odeme_col = cols_list[2]
    if not banka_col and len(cols_list) > 3: banka_col = cols_list[3]

    parsed_rows = []
    for _, row in df.iterrows():
        raw_p_name = str(row[p_col]).strip() if p_col else ""
        c_p_name = clean_string(raw_p_name)
        
        if not c_p_name or c_p_name in ["NAN", "NONE", "TOTAL", "TOPLAM", "GENELTOPLAM"]:
            continue
            
        ft_val = parse_turkish_float(row[ft_col]) if ft_col else 0.0
        odeme_val = parse_turkish_float(row[odeme_col]) if odeme_col else 0.0
        banka_val = parse_turkish_float(row[banka_col]) if banka_col else 0.0

        parsed_rows.append({
            "Raw_Name": raw_p_name,
            "Clean_Name": c_p_name,
            "Nakit Ft Tutarı Topl": ft_val,
            "Nakit Ödeme Tutarı Topl": odeme_val,
            "Banka/ATM": banka_val
        })

    temp_df = pd.DataFrame(parsed_rows)

    priority_list = [
        "HATİCE KÜBRA IŞIK",
        "ALATTİN CEBECİ",
        "BURCU DÜREN",
        "AHMET BERKAN ÖKSÜZ",
        "HASAN SAĞLAM",
        "MEHMET KAYMAZ",
        "SUAT ARI",
        "SERGEN GÖRÜROĞLU"
    ]

    final_rows = []
    processed_clean_names = set()

    for fixed_name in priority_list:
        clean_fixed = clean_string(fixed_name)
        matched_row = None
        
        if not temp_df.empty:
            exact_match = temp_df[temp_df["Clean_Name"] == clean_fixed]
            if not exact_match.empty:
                matched_row = exact_match.iloc[0]
            else:
                contains_match = temp_df[temp_df["Clean_Name"].apply(lambda x: clean_fixed in x or x in clean_fixed)]
                if not contains_match.empty:
                    matched_row = contains_match.iloc[0]

        if matched_row is not None:
            final_rows.append({
                "Personel Adı": fixed_name,
                "Nakit Ft Tutarı Topl": float(matched_row["Nakit Ft Tutarı Topl"]),
                "Nakit Ödeme Tutarı Topl": float(matched_row["Nakit Ödeme Tutarı Topl"]),
                "Banka/ATM": float(matched_row["Banka/ATM"]),
            })
            processed_clean_names.add(matched_row["Clean_Name"])
        else:
            final_rows.append({
                "Personel Adı": fixed_name,
                "Nakit Ft Tutarı Topl": 0.0,
                "Nakit Ödeme Tutarı Topl": 0.0,
                "Banka/ATM": 0.0,
            })

    if not temp_df.empty:
        for _, row in temp_df.iterrows():
            c_name = row["Clean_Name"]
            if c_name not in processed_clean_names:
                final_rows.append({
                    "Personel Adı": row["Raw_Name"],
                    "Nakit Ft Tutarı Topl": float(row["Nakit Ft Tutarı Topl"]),
                    "Nakit Ödeme Tutarı Topl": float(row["Nakit Ödeme Tutarı Topl"]),
                    "Banka/ATM": float(row["Banka/ATM"]),
                })
                processed_clean_names.add(c_name)

    result_df = pd.DataFrame(final_rows)
    result_df["Hesap"] = result_df["Nakit Ft Tutarı Topl"] + result_df["Nakit Ödeme Tutarı Topl"] - result_df["Banka/ATM"]
    result_df["İşlem"] = False

    result_df.reset_index(drop=True, inplace=True)
    result_df.index = range(1, len(result_df) + 1)

    return result_df[["Personel Adı", "Nakit Ft Tutarı Topl", "Nakit Ödeme Tutarı Topl", "Banka/ATM", "Hesap", "İşlem"]]

# ==========================================
# F4 ÖDEME LİSTESİ İŞLEME MOTORU
# ==========================================
def process_f4_payment_data(df):
    df.columns = df.columns.astype(str).str.strip()
    
    musteri_col, borc_col, aciklama_col = None, None, None
    for col in df.columns:
        c_upper = str(col).upper()
        if ("MÜŞTERİ" in c_upper or "MUSTERI" in c_upper or "FIRMA" in c_upper or "UNVAN" in c_upper) and not musteri_col:
            musteri_col = col
        elif ("BORÇ" in c_upper or "BORC" in c_upper or "BAKİYE" in c_upper or "BAKIYE" in c_upper or "TUTAR" in c_upper) and not borc_col:
            borc_col = col
        elif "AÇIKLAMA" in c_upper or "ACIKLAMA" in c_upper:
            aciklama_col = col

    cols_list = list(df.columns)
    if not musteri_col and len(cols_list) > 0: musteri_col = cols_list[0]
    if not borc_col and len(cols_list) > 1: borc_col = cols_list[1]
    if not aciklama_col and len(cols_list) > 2: aciklama_col = cols_list[2]

    processed_rows = []
    for _, row in df.iterrows():
        m_adi = str(row[aciklama_col]).strip() if aciklama_col and not pd.isna(row[aciklama_col]) else ""
        if not m_adi or m_adi.upper() in ["NAN", "NONE", "TOPLAM", "TOTAL"]:
            m_adi = str(row[musteri_col]).strip() if musteri_col else ""
            
        if not m_adi or m_adi.upper() in ["NAN", "NONE", "TOPLAM", "TOTAL"]:
            continue
            
        borc_val = parse_turkish_float(row[borc_col]) if borc_col else 0.0
        
        if borc_val == 0.0:
            continue

        assigned_personel = "ATANMAMIŞ"
        m_upper = m_adi.upper()
        m_clean = clean_string(m_adi)

        if m_upper in MUSTERI_PERSONEL_MAP:
            assigned_personel = MUSTERI_PERSONEL_MAP[m_upper]
        else:
            found = False
            for k, v in MUSTERI_PERSONEL_MAP.items():
                if clean_string(k) == m_clean:
                    assigned_personel = v
                    found = True
                    break
            
            if not found:
                for k, v in MUSTERI_PERSONEL_MAP.items():
                    k_clean = clean_string(k)
                    if k_clean and (k_clean in m_clean or m_clean in k_clean):
                        assigned_personel = v
                        break

        processed_rows.append({
            "Müşteri Adı": m_adi,
            "Fatura Borcu": borc_val,
            "Açıklama": "",
            "Personel": assigned_personel
        })

    res_df = pd.DataFrame(processed_rows)
    if not res_df.empty:
        res_df.reset_index(drop=True, inplace=True)
        res_df.index = range(1, len(res_df) + 1)
    return res_df

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

    uploaded_file = st.file_uploader("📂 Rapor / Liste Yükle", type=['csv', 'xlsx', 'xls', 'html'])
    
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    if st.button("💰 HESAP"):
        st.session_state.active_tab = "HESAP"
    if st.button("📋 F4 ÖDEME LİSTESİ"):
        st.session_state.active_tab = "F4 ÖDEME LİSTESİ"

# ==========================================
# AKILLI VERİ DAĞITIM VE İŞLEME MİMARİSİ
# ==========================================
if uploaded_file is not None:
    try:
        raw_df = smart_read_file(uploaded_file)
        st.session_state.raw_df = raw_df
        
        cols_str = " ".join([str(c).upper() for c in raw_df.columns])
        if "NAKIT" in cols_str or "FT" in cols_str or "ODEME" in cols_str or "BANKA" in cols_str or "PERSONEL" in cols_str:
            processed_acc = process_personnel_account_data(raw_df)
            st.session_state.account_df = processed_acc
            st.session_state.hesap_df = processed_acc.copy()
            
        if "MÜŞTERİ" in cols_str or "MUSTERI" in cols_str or "BORÇ" in cols_str or "BORC" in cols_str or "FATURA BORCU" in cols_str or "F4" in uploaded_file.name.upper():
            f4_res = process_f4_payment_data(raw_df)
            st.session_state.f4_df = f4_res
            
    except Exception as e:
        st.error(f"❌ Dosya Okuma/İşleme Hatası: {e}")

# ==========================================
# TAB 1: HESAP
# ==========================================
if st.session_state.active_tab == "HESAP":
    st.title("📋 Günlük Personel Hesap Takip Tablosu")
    st.caption("✍️ Değerleri değiştirdiğinizde **Hesap** alanı canlı olarak güncellenir.")

    account_df = st.session_state.account_df

    if account_df is not None:
        if st.sidebar.button("🔄 Tabloyu Sıfırla"):
            st.session_state.hesap_df = account_df.copy()
            
        current_df = st.session_state.hesap_df.copy()

        def highlight_rows(row):
            if row.get('İşlem', False):
                return ['background-color: rgba(46, 125, 50, 0.4); color: #ffffff; font-weight: bold;'] * len(row)
            return [''] * len(row)

        edited_output = st.data_editor(
            current_df.style.apply(highlight_rows, axis=1),
            column_config={
                "Personel Adı": st.column_config.TextColumn("Personel Adı", required=True),
                "Nakit Ft Tutarı Topl": st.column_config.NumberColumn("Nakit Ft Tutarı Topl", format="%.2f ₺"),
                "Nakit Ödeme Tutarı Topl": st.column_config.NumberColumn("Nakit Ödeme Tutarı Topl", format="%.2f ₺"),
                "Banka/ATM": st.column_config.NumberColumn("Banka/ATM", format="%.2f ₺"),
                "Hesap": st.column_config.NumberColumn("Hesap", format="%.2f ₺", disabled=True),
                "İşlem": st.column_config.CheckboxColumn("İşlem (Tamamlandı)", default=False)
            },
            disabled=["Hesap"],
            hide_index=False,
            use_container_width=True,
            num_rows="fixed"
        )

        edited_df = pd.DataFrame(edited_output)
        ft_vals = pd.to_numeric(edited_df["Nakit Ft Tutarı Topl"], errors='coerce').fillna(0.0)
        odeme_vals = pd.to_numeric(edited_df["Nakit Ödeme Tutarı Topl"], errors='coerce').fillna(0.0)
        banka_vals = pd.to_numeric(edited_df["Banka/ATM"], errors='coerce').fillna(0.0)
        edited_df["Hesap"] = ft_vals + odeme_vals - banka_vals
        st.session_state.hesap_df = edited_df

        st.markdown("<div class='kasa-box'>", unsafe_allow_html=True)
        st.subheader("💵 Genel Kasa ve Hesap Dengesi")
        toplam_hesap = float(edited_df["Hesap"].sum())

        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Toplam Hesap", f"{toplam_hesap:,.2f} ₺")

        kasa_val = col2.number_input("🏦 KASA (Manuel Giriniz)", value=float(st.session_state.kasa_miktari), step=100.0, format="%.2f")
        st.session_state.kasa_miktari = kasa_val

        kasa_fark = toplam_hesap - kasa_val
        if kasa_val > toplam_hesap:
            col3.metric("⚖️ Kasa Farkı Durumu", f"{kasa_fark:,.2f} ₺", delta="Durum: AÇIK", delta_color="inverse")
        else:
            col3.metric("⚖️ Kasa Farkı Durumu", f"{kasa_fark:,.2f} ₺", delta="Durum: TAM", delta_color="normal")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("💡 Lütfen sol taraftan **Personel Hesap Alımı Ekranı** dosyanızı yükleyin.")

# ==========================================
# TAB 2: F4 ÖDEME LİSTESİ
# ==========================================
elif st.session_state.active_tab == "F4 ÖDEME LİSTESİ":
    st.title("📋 F4 Ödeme ve Personel Tahsilat Listesi")
    st.caption("✍️ Tablo üzerinden 'Sorumlu Personel' sütununa tıklayarak eksik veya atanmamış firmaların personel isimlerini **manuel olarak yazabilir** veya değiştirebilirsiniz.")

    f4_df = st.session_state.f4_df
    if f4_df is not None and not f4_df.empty:
        
        edited_f4_df = st.data_editor(
            f4_df,
            column_config={
                "Müşteri Adı": st.column_config.TextColumn("Müşteri Adı", disabled=True),
                "Fatura Borcu": st.column_config.NumberColumn("Fatura Borcu", format="%.2f ₺", disabled=True),
                "Açıklama": st.column_config.TextColumn("Açıklama", disabled=True),
                "Personel": st.column_config.TextColumn("Sorumlu Personel (Düzenlenebilir)")
            },
            hide_index=False,
            use_container_width=True,
            num_rows="fixed",
            key="f4_editable_table"
        )
        
        st.session_state.f4_df = pd.DataFrame(edited_f4_df)
        
        st.markdown("---")
        
        available_personnel = ["Tümü"] + sorted(st.session_state.f4_df["Personel"].dropna().unique().tolist())
        selected_f4_personel = st.selectbox("🔍 Sorumlu Personele Göre Süzgeçle:", available_personnel, key="f4_personel_filter")
        
        if selected_f4_personel != "Tümü":
            display_f4_df = st.session_state.f4_df[st.session_state.f4_df["Personel"] == selected_f4_personel]
        else:
            display_f4_df = st.session_state.f4_df
            
        st.subheader(f"📌 Seçilen Görünüm: {selected_f4_personel} (Toplam {len(display_f4_df)} Kayıt)")
        st.dataframe(display_f4_df, use_container_width=True)
        
        if not display_f4_df.empty:
            toplam_secilen_borc = display_f4_df["Fatura Borcu"].sum()
            st.metric(label=f"{selected_f4_personel} - Toplam Fatura Borcu / Tahsilat Hedefi", value=f"{toplam_secilen_borc:,.2f} ₺")
            
            html_table = display_f4_df.to_html(classes='table table-striped', index=False)
            print_html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <title>F4 Tahsilat Listesi - {selected_f4_personel}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    h2 {{ color: #0A58CA; }}
                    table {{ width: 100% !important; border-collapse: collapse; margin-top: 15px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 12px; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body onload="window.print();">
                <h2>Görükle Acente - F4 Tahsilat ve Borç Listesi</h2>
                <p><b>Sorumlu Personel:</b> {selected_f4_personel}</p>
                <p><b>Toplam Fatura Borcu:</b> {toplam_secilen_borc:,.2f} ₺</p>
                {html_table}
            </body>
            </html>
            """
            
            st.download_button(
                label=f"📄 Görüntülenen Listeyi Yazdır / PDF Olarak Kaydet",
                data=print_html,
                file_name=f"F4_Tahsilat_Listesi_{selected_f4_personel}.html",
                mime="text/html",
                help="Bu butona tıkladığınızda açılacak sayfadan hedefi 'PDF olarak kaydet' seçerek çıktısını alabilirsiniz."
            )

    else:
        raw_df = st.session_state.raw_df
        if raw_df is not None:
            f4_res = process_f4_payment_data(raw_df)
            st.session_state.f4_df = f4_res
            if f4_res is not None and not f4_res.empty:
                st.success(f"✅ F4 Ödeme Listesi başarıyla analiz edildi.")
                st.rerun()
            else:
                st.warning("⚠️ Yüklenen dosya içerisinde F4 ödeme kriterlerine uygun (borcu sıfırdan büyük) veri bulunamadı.")
        else:
            st.info("💡 F4 Ödeme Listesi verilerini görüntülemek için sol menüden ilgili F4 ÖDEME LİSTESİ dosyanızı yükleyin.")
