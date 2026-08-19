import streamlit as st
from supabase import create_client

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS
st.markdown("""
    <style>
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; background-position: center; }
    html, body, [class*="css"], p, span, label { color: #FFFFFF !important; text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.95); }
    h1, h2, h3, h4 { color: #FFFFFF !important; text-shadow: 3px 3px 6px rgba(0, 0, 0, 1); }
    .card { background-color: rgba(15, 15, 15, 0.9) !important; padding: 15px !important; border-radius: 12px !important; margin-bottom: 12px !important; border-left: 5px solid #4CAF50 !important; }
    [data-testid="stSidebar"] { background-color: #111111 !important; }
    .stTextInput input, .stNumberInput input { color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 4. Logica Accesso Admin
def check_password():
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        st.sidebar.subheader("🔒 Accesso Amministratore")
        with st.sidebar.form("form_login"):
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Entra"):
                if pwd == "capeta63": st.session_state.admin = True; st.rerun()
                else: st.sidebar.error("Password errata")
        return False
    return True

# Gestione stato navigazione (Default: Classifica)
if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"

# Barra di Navigazione in alto
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("🏆 Classifica"): st.session_state.current_page = "Classifica"
with col2:
    if st.button("📅 Schedine"): st.session_state.current_page = "Schedine"
with col3:
    if st.sidebar.button("⚙️ Area Admin"): st.session_state.current_page = "Admin"

# --- PAGINA CLASSIFICA ---
if st.session_state.current_page == "Classifica":
    st.title("🏆 Classifica Generale")
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        risultati = supabase.table("risultati").select("*").execute().data
        if squadre:
            classifica = []
            for s in squadre:
                punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
                classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url'), 'id': s['id']})
            for pos, item in enumerate(sorted(classifica, key=lambda x: (-x['punti'], x['nome'])), 1):
                logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' onerror=\"this.onerror=null;this.src='https://images.emojiterra.com/google/android-11/512px/26bd.png';\" />" if item['logo'] and item['logo'].startswith('http') else "<span style='margin-right:15px; font-size:25px;'>⚽</span>"
                st.markdown(f"""<div class="card"><div style="display:flex; align-items:center;">
                            <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                            <span style="flex-grow:1; font-weight:bold; font-size:18px;">{item['nome']}</span>
                            <span style="color:#4CAF50; font-weight:bold; font-size:18px;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
    except Exception as e: st.error(f"Errore: {e}")

# --- PAGINA SCHEDINE ---
elif st.session_state.current_page == "Schedine":
    st.title("📅 Schedine")
    giornata = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=0)
    num_g = int(giornata.split(" ")[1])
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        for s in sorted(squadre, key=lambda x: x['nome_squadra']):
            st.markdown(f"### {s['nome_squadra']}")
            url = schedine_dict.get(s['id'])
            if url and url.startswith('http'): st.image(url, use_container_width=True)
            else: st.info("Nessuna schedina caricata.")
            st.markdown("---")
    except Exception as e: st.error(f"Errore: {e}")

# --- AREA ADMIN ---
elif st.session_state.current_page == "Admin":
    if check_password():
        st.title("⚙️ Area Admin")
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Squadra", "⚽ Punteggi", "🎫 Schedine", "🗑️ Elimina"])
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra"); pres = st.text_input("Presidente"); logo = st.text_input("URL Logo")
                if st.form_submit_button("Salva"): supabase.table("squadre").insert({"nome_squadra": n, "presidente": pres, "logo_url": logo}).execute()
        with tab2:
            with st.form("add_p"):
                sq = st.selectbox("Squadra", [s['nome_squadra'] for s in supabase.table("squadre").select("*").execute().data])
                p = st.number_input("Punti", step=1); 
                if st.form_submit_button("Aggiorna"): 
                    s_id = next(s['id'] for s in supabase.table("squadre").select("*").execute().data if s['nome_squadra'] == sq)
                    supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p}).execute()
        with tab3:
            with st.form("add_sch"):
                g = st.selectbox("Giornata", [f"Giornata {i}" for i in range(1, 39)])
                sq_s = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in supabase.table("squadre").select("*").execute().data])
                u_sch = st.text_input("URL Schedina")
                if st.form_submit_button("Carica"): 
                    s_id = next(s['id'] for s in supabase.table("squadre").select("*").execute().data if s['nome_squadra'] == sq_s)
                    supabase.table("schedine").insert({"squadra_id": s_id, "giornata": int(g.split()[1]), "schedina_url": u_sch}).execute()
        with tab4:
            if st.button("Elimina Tutto/Gestisci"): st.rerun()
