# Definizione del contenuto completo e corretto dell'app Streamlit.
# L'obiettivo è forzare lo sfondo, lo stile dei loghi e la leggibilità.

app_code = """
import streamlit as st
from supabase import create_client

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. CSS DEFINITIVO: Forza lo sfondo su tutto l'app e gestisce i loghi
st.markdown('''
    <style>
    /* Forza lo sfondo nero su tutto il container principale */
    .stApp {
        background-color: #000000 !important;
    }
    
    /* Forza il colore bianco su tutti i testi */
    h1, h2, h3, div, p, span, label, input {
        color: #FFFFFF !important;
    }

    /* Sidebar Nera */
    [data-testid="stSidebar"] {
        background-color: #0f0f0f !important;
    }

    /* Card Squadra - Layout pulito */
    .custom-card {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    }

    /* Stile Logo - Cerchio perfetto */
    .logo-container {
        width: 50px !important;
        height: 50px !important;
        border-radius: 50% !important;
        overflow: hidden !important;
        margin-right: 20px !important;
        background-color: #333 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .logo-img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
    }
    </style>
''', unsafe_allow_html=True)

# 4. Logica Accesso
if "admin" not in st.session_state: st.session_state.admin = False
menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Area Admin"])

# 5. Funzione renderizzazione Squadra
def render_squadra_card(pos, nome, punti, logo_url):
    logo_content = f'<img src="{logo_url}" class="logo-img">' if logo_url and logo_url.startswith('http') else '<span style="font-size:24px;">⚽</span>'
    st.markdown(f'''
        <div class="custom-card">
            <span style="font-weight:bold; font-size:18px; margin-right:20px;">{pos}°</span>
            <div class="logo-container">{logo_content}</div>
            <span style="flex-grow:1; font-weight:bold; font-size:20px;">{nome}</span>
            <span style="color:#4CAF50; font-weight:bold; font-size:20px;">{punti} pts</span>
        </div>
    ''', unsafe_allow_html=True)

if menu == "Classifica":
    st.title("🏆 Classifica Generale")
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        risultati = supabase.table("risultati").select("*").execute().data
        
        if squadre:
            classifica = []
            for s in squadre:
                punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
                classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
            
            for pos, item in enumerate(sorted(classifica, key=lambda x: x['punti'], reverse=True), 1):
                render_squadra_card(pos, item['nome'], item['punti'], item['logo'])
        else:
            st.write("Nessuna squadra presente.")
    except Exception as e:
        st.error(f"Errore: {e}")

else:
    # Area Admin (Semplicizzata per stabilità)
    if not st.session_state.admin:
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Entra"):
            if pwd == "capeta63": st.session_state.admin = True; st.rerun()
    else:
        st.title("⚙️ Amministrazione")
        tab1, tab2 = st.tabs(["➕ Nuova Squadra", "⚽ Punteggi"])
        with tab1:
            with st.form("new_sq"):
                n = st.text_input("Nome Squadra")
                l = st.text_input("URL Logo")
                if st.form_submit_button("Salva"):
                    supabase.table("squadre").insert({"nome_squadra": n, "logo_url": l}).execute()
                    st.rerun()
        with tab2:
            sqs = supabase.table("squadre").select("*").execute().data
            if sqs:
                with st.form("new_pts"):
                    sel = st.selectbox("Squadra", [x['nome_squadra'] for x in sqs])
                    p = st.number_input("Punti", step=1)
                    if st.form_submit_button("Salva"):
                        sid = next(x['id'] for x in sqs if x['nome_squadra'] == sel)
                        supabase.table("risultati").insert({"squadra_id": sid, "punteggio": p}).execute()
                        st.rerun()
"""

# Scrittura su file app.py
with open("app.py", "w") as f:
    f.write(app_code)
