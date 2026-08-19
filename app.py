import streamlit as st
from supabase import create_client
import requests

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Funzione Validazione Immagine
def get_valid_logo(url):
    if not url or not url.startswith("http"): return None
    try:
        response = requests.head(url, timeout=1.5)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            return url
    except: pass
    return None

# 4. CSS FORZATO (Nero e Bianco per tutto)
st.markdown("""
    <style>
    /* Sfondo generale e testo bianco */
    .stApp { background-color: #000000 !important; }
    h1, h2, h3, p, div, label { color: #FFFFFF !important; }
    
    /* Sidebar nera */
    [data-testid="stSidebar"] { background-color: #111111 !important; }
    
    /* Card Classifica con sfondo scuro e bordo */
    .card { 
        background-color: #1c1c1c !important; 
        padding: 15px !important; 
        border-radius: 10px !important; 
        margin-bottom: 10px !important; 
        border-left: 5px solid #4CAF50 !important; 
        color: #FFFFFF !important;
    }
    
    /* Input campi (per non farli sparire) */
    .stTextInput input, .stNumberInput input, .stSelectbox div { 
        background-color: #333333 !important; 
        color: #FFFFFF !important; 
    }
    </style>
""", unsafe_allow_html=True)

# 5. Logica Admin
def check_password():
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        st.sidebar.subheader("🔒 Area Admin")
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.rerun()
            else: st.sidebar.error("Password errata")
        return False
    return True

# 6. Interfaccia
menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Area Admin"])

if menu == "Classifica":
    st.title("🏆 Classifica Generale")
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    
    if squadre:
        classifica = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': get_valid_logo(s.get('logo_url'))})
        
        for pos, item in enumerate(sorted(classifica, key=lambda x: x['punti'], reverse=True), 1):
            logo = f"<img src='{item['logo']}' width='30' height='30' style='border-radius:50%;'>" if item['logo'] else "⚽"
            st.markdown(f"""
                <div class="card">
                    <div style="display:flex; align-items:center;">
                        <span style="width:40px;">{pos}°</span>
                        <div style="margin-right:15px;">{logo}</div>
                        <div style="flex-grow:1;">{item['nome']}</div>
                        <div style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Nessuna squadra presente.")

else:
    if check_password():
        st.title("⚙️ Area Amministrazione")
        tab1, tab2, tab3 = st.tabs(["➕ Nuova Squadra", "⚽ Assegna Punti", "🗑️ Elimina Squadre"])
        
        with tab1:
            with st.form("add_sq"):
                n = st.text_input("Nome Squadra")
                l = st.text_input("URL Logo")
                if st.form_submit_button("Salva"):
                    supabase.table("squadre").insert({"nome_squadra": n, "logo_url": l}).execute()
                    st.rerun()
        
        with tab2:
            sqs = supabase.table("squadre").select("*").execute().data
            if sqs:
                with st.form("add_pts"):
                    sel = st.selectbox("Squadra", [s['nome_squadra'] for s in sqs])
                    p = st.number_input("Punteggio", step=1)
                    if st.form_submit_button("Aggiungi"):
                        sid = next(s['id'] for s in sqs if s['nome_squadra'] == sel)
                        supabase.table("risultati").insert({"squadra_id": sid, "punteggio": p}).execute()
                        st.rerun()
        
        with tab3:
            for s in supabase.table("squadre").select("*").execute().data:
                if st.button(f"Elimina {s['nome_squadra']}", key=s['id']):
                    supabase.table("risultati").delete().eq("squadra_id", s['id']).execute()
                    supabase.table("squadre").delete().eq("id", s['id']).execute()
                    st.rerun()
