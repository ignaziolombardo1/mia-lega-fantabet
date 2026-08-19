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
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3 { color: #FFFFFF !important; text-shadow: 3px 3px 6px rgba(0, 0, 0, 1); }
    .card { background-color: rgba(15, 15, 15, 0.9) !important; padding: 15px !important; border-radius: 12px !important; margin-bottom: 12px !important; border-left: 5px solid #4CAF50 !important; }
    </style>
""", unsafe_allow_html=True)

# Inizializzazione variabili di stato
if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"
if "admin" not in st.session_state: st.session_state.admin = False

# --- MENU IN ALTO ---
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
with col2:
    if st.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"
with col3:
    if st.button("⚙️ Admin", use_container_width=True): st.session_state.current_page = "Admin"

st.markdown("---")

# --- PAGINA CLASSIFICA ---
if st.session_state.current_page == "Classifica":
    st.title("🏆 Classifica Generale")
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    if squadre:
        classifica = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
        for pos, item in enumerate(sorted(classifica, key=lambda x: (-x['punti'], x['nome'])), 1):
            logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽"
            st.markdown(f"""<div class="card"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                        <span style="flex-grow:1; font-weight:bold;">{item['nome']}</span>
                        <span style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)

# --- PAGINA SCHEDINE ---
elif st.session_state.current_page == "Schedine":
    st.title("📅 Schedine")
    giornata = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=0)
    num_g = int(giornata.split(" ")[1])
    squadre = supabase.table("squadre").select("*").execute().data
    schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data
    schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
    for s in sorted(squadre, key=lambda x: x['nome_squadra']):
        logo_html = f"<img src='{s.get('logo_url')}' style='width:40px; height:40px; border-radius:50%; object-fit:cover; margin-right:15px;' />" if s.get('logo_url') else "⚽"
        st.markdown(f"<div style='display:flex; align-items:center;'>{logo_html} <h3>{s['nome_squadra']}</h3></div>", unsafe_allow_html=True)
        url = schedine_dict.get(s['id'])
        if url: st.image(url, use_container_width=True)
        else: st.info("Nessuna schedina.")
        st.markdown("---")

# --- PAGINA ADMIN ---
elif st.session_state.current_page == "Admin":
    if not st.session_state.admin:
        st.subheader("🔒 Accesso Amministratore")
        pwd = st.text_input("Password", type="password")
        if st.button("Entra"):
            if pwd == "capeta63": st.session_state.admin = True; st.rerun()
            else: st.error("Password errata")
    else:
        st.title("⚙️ Area Admin")
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Squadra", "⚽ Punteggi", "🎫 Schedina", "🗑️ Elimina"])
        
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra"); logo = st.text_input("URL Logo")
                if st.form_submit_button("Salva"): supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo}).execute(); st.success("Salvato")
        
        with tab2:
            squadre_list = supabase.table("squadre").select("*").execute().data
            if squadre_list:
                with st.form("add_p"):
                    sq = st.selectbox("Squadra", [s['nome_squadra'] for s in squadre_list])
                    p = st.number_input("Punti", step=1)
                    if st.form_submit_button("Aggiorna"):
                        s_id = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq)
                        supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p}).execute(); st.success("Punteggio aggiornato")
        
        with tab3:
            if squadre_list:
                with st.form("add_sch"):
                    g = st.selectbox("Giornata", [f"Giornata {i}" for i in range(1, 39)])
                    sq_s = st.selectbox("Squadra", [s['nome_squadra'] for s in squadre_list])
                    u_sch = st.text_input("URL Immagine Schedina")
                    if st.form_submit_button("Carica"):
                        s_id = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq_s)
                        supabase.table("schedine").insert({"squadra_id": s_id, "giornata": int(g.split()[1]), "schedina_url": u_sch}).execute(); st.success("Schedina caricata")
        
        with tab4:
            if st.button("Log-out"): st.session_state.admin = False; st.rerun()
