import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(
    page_title="FantaBet Serie A", 
    page_icon="⚽", 
    layout="wide"
)

# 3. Stile CSS per leggibilità massima
st.markdown("""
    <link rel="manifest" href="manifest.json">
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/logo.png">
    <style>
    /* Testo bianco ovunque */
    html, body, [class*="css"] {
        color: #FFFFFF !important;
    }
    /* Titoli con ombra per contrasto */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 1) !important;
    }
    /* Card con sfondo quasi nero opaco */
    .card { 
        background-color: rgba(0, 0, 0, 0.85) !important; 
        padding: 15px !important; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        border-left: 5px solid #4CAF50; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
    }
    /* Sfondo oscurato al 80% */
    .stApp { 
        background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); 
        background-size: cover; 
        background-attachment: fixed;
        background-position: center;
    }
    /* Input campi bianchi traslucidi */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        color: white !important;
        background-color: rgba(255,255,255,0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4. Logica App
def check_password():
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        st.sidebar.subheader("🔒 Accesso Amministratore")
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.rerun()
            else: st.sidebar.error("Password errata")
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
                classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
            for pos, item in enumerate(sorted(classifica, key=lambda x: x['punti'], reverse=True), 1):
                logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽"
                st.markdown(f"""<div class="card"><div style="display:flex; align-items:center; width:100%;">
                            <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                            <span style="flex-grow:1; font-weight:bold;">{item['nome']}</span>
                            <span style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
    except Exception as e: st.error(f"Errore: {e}")

else:
    if check_password():
        st.title("⚙️ Area Admin")
        tab1, tab2, tab3 = st.tabs(["➕ Squadre", "⚽ Punteggi", "🗑️ Elimina"])
        with tab1:
            with st.form("f1"):
                n = st.text_input("Nome Squadra")
                if st.form_submit_button("Salva"):
                    supabase.table("squadre").insert({"nome_squadra": n}).execute()
                    st.rerun()
        with tab2:
            squadre_list = supabase.table("squadre").select("id, nome_squadra").execute().data
            if squadre_list:
                with st.form("f2"):
                    sq = st.selectbox("Squadra", {s["nome_squadra"]: s["id"] for s in squadre_list})
                    p = st.number_input("Punti", step=1)
                    if st.form_submit_button("Aggiungi"):
                        supabase.table("risultati").insert({"squadra_id": {s["nome_squadra"]: s["id"] for s in squadre_list}[sq], "punteggio": p}).execute()
                        st.rerun()
        with tab3:
            ris = supabase.table("risultati").select("*").execute().data
            for r in ris:
                if st.button(f"Elimina punteggio {r['punteggio']}", key=r['id']):
                    supabase.table("risultati").delete().eq("id", r['id']).execute()
                    st.rerun()
