import streamlit as st
from supabase import create_client
import uuid
import pandas as pd
import requests

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Funzione per validare il link immagine
def get_valid_logo(url):
    """Controlla se l'URL è un'immagine valida, altrimenti ritorna None."""
    if not url: return None
    try:
        # Controlliamo solo le intestazioni per velocità
        response = requests.head(url, timeout=2)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            return url
    except:
        pass
    return None

# 4. Stile CSS
st.markdown("""
    <style>
    html, body, [class*="css"] { color: #FFFFFF !important; }
    h1, h2, h3, h4 { color: #FFFFFF !important; text-shadow: 3px 3px 6px rgba(0, 0, 0, 1) !important; }
    .card { background-color: rgba(0, 0, 0, 0.85) !important; padding: 15px !important; border-radius: 12px; margin-bottom: 12px; border-left: 5px solid #4CAF50; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; background-position: center; }
    [data-testid="stSidebar"] { background-color: #111111 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .stTextInput input, .stNumberInput input { color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold; }
    label { color: #FFFFFF !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 5. Logica Accesso
def check_password():
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        st.sidebar.subheader("🔒 Accesso Amministratore")
        with st.sidebar.form("form_login"):
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Entra"):
                if pwd == "capeta63": 
                    st.session_state.admin = True
                    st.rerun()
                else: st.error("Password errata")
        return False
    return True

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Area Admin"])

if menu == "Classifica":
    st.title("🏆 Classifica Generale FantaBet")
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        risultati = supabase.table("risultati").select("*").execute().data
        if squadre:
            classifica = []
            for s in squadre:
                punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
                # Usiamo la validazione automatica
                valid_logo = get_valid_logo(s.get('logo_url'))
                classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': valid_logo})
            
            for pos, item in enumerate(sorted(classifica, key=lambda x: x['punti'], reverse=True), 1):
                logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "<span style='margin-right:15px; font-size:25px;'>⚽</span>"
                st.markdown(f"""<div class="card"><div style="display:flex; align-items:center; width:100%;">
                            <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                            <span style="flex-grow:1; font-weight:bold;">{item['nome']}</span>
                            <span style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
    except Exception as e: st.error(f"Errore caricamento: {e}")

else:
    if check_password():
        # ... (Il resto delle TAB admin rimane identico) ...
        # (Ometti il resto qui per brevità, incolla sopra e mantieni le tue tab)
