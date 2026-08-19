import streamlit as st
from supabase import create_client
import requests

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. CSS POTENTE (Forza tutto)
st.markdown("""
    <style>
    /* Sfondo nero per tutta la pagina */
    .stApp { background-color: #000000 !important; }
    
    /* Forza il testo bianco ovunque */
    h1, h2, h3, div, p, span, label { color: #FFFFFF !important; }
    
    /* Sidebar scura */
    [data-testid="stSidebar"] { background-color: #1a1a1a !important; }
    
    /* Card Classifica */
    .custom-card { 
        background-color: #262626 !important; 
        padding: 15px !important; 
        border-radius: 10px !important; 
        margin-bottom: 10px !important; 
        border-left: 6px solid #4CAF50 !important; 
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
    }
    
    /* Logo circolare */
    .logo-img { 
        width: 40px !important; 
        height: 40px !important; 
        border-radius: 50% !important; 
        object-fit: cover !important; 
        margin-right: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4. Funzione Logo
def get_logo_html(url):
    if url and url.startswith("http"):
        return f'<img src="{url}" class="logo-img">'
    return '<span style="font-size:30px; margin-right:15px;">⚽</span>'

# 5. Logica Accesso
if "admin" not in st.session_state: st.session_state.admin = False

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Area Admin"])

if menu == "Classifica":
    st.markdown("# 🏆 Classifica Generale")
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    
    if squadre:
        # Calcolo punti
        classifica = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
        
        # Mostra in ordine
        for pos, item in enumerate(sorted(classifica, key=lambda x: x['punti'], reverse=True), 1):
            logo_html = get_logo_html(item['logo'])
            st.markdown(f"""
                <div class="custom-card">
                    <span style="font-weight:bold; margin-right:20px;">{pos}°</span>
                    {logo_html}
                    <span style="flex-grow:1; font-weight:bold; font-size:18px;">{item['nome']}</span>
                    <span style="color:#4CAF50; font-weight:bold; font-size:18px;">{item['punti']} pts</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Nessuna squadra registrata.")

else:
    # Area Admin
    if not st.session_state.admin:
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Entra"):
            if pwd == "capeta63": st.session_state.admin = True; st.rerun()
    else:
        st.title("⚙️ Amministrazione")
        # Tab semplici per evitare conflitti di layout
        tab1, tab2 = st.tabs(["➕ Nuova Squadra", "⚽ Inserisci Punti"])
        with tab1:
            with st.form("squadra"):
                n = st.text_input("Nome Squadra")
                l = st.text_input("URL Logo")
                if st.form_submit_button("Salva"):
                    supabase.table("squadre").insert({"nome_squadra": n, "logo_url": l}).execute()
                    st.rerun()
        with tab2:
            sqs = supabase.table("squadre").select("*").execute().data
            if sqs:
                with st.form("punti"):
                    s = st.selectbox("Squadra", [x['nome_squadra'] for x in sqs])
                    p = st.number_input("Punti", step=1)
                    if st.form_submit_button("Aggiungi"):
                        sid = next(x['id'] for x in sqs if x['nome_squadra'] == s)
                        supabase.table("risultati").insert({"squadra_id": sid, "punteggio": p}).execute()
                        st.rerun()
