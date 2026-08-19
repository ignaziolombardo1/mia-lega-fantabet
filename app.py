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

# Gestione stato
if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"
if "admin" not in st.session_state: st.session_state.admin = False

# --- SIDEBAR (Area Admin) ---
with st.sidebar:
    st.subheader("⚙️ Area Amministratore")
    if not st.session_state.admin:
        pwd = st.text_input("Password", type="password")
        if st.button("Entra"):
            if pwd == "capeta63": st.session_state.admin = True; st.rerun()
            else: st.error("Password errata")
    else:
        st.success("Accesso Effettuato")
        if st.button("Logout"): st.session_state.admin = False; st.rerun()
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Squadra", "⚽ Punti", "🎫 Schedina", "🗑️ Elimina"])
        squadre_list = supabase.table("squadre").select("*").execute().data
        
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra"); logo = st.text_input("URL Logo")
                if st.form_submit_button("Salva"): supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo}).execute(); st.rerun()
        with tab2:
            with st.form("add_p"):
                sq = st.selectbox("Squadra", [s['nome_squadra'] for s in squadre_list])
                p = st.number_input("Punti", step=1)
                if st.form_submit_button("Aggiorna"):
                    s_id = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq)
                    supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p}).execute(); st.rerun()
        with tab3:
            with st.form("add_sch"):
                g = st.selectbox("Giornata", [f"Giornata {i}" for i in range(1, 39)])
                sq_s = st.selectbox("Squadra", [s['nome_squadra'] for s in squadre_list])
                u_sch = st.text_input("URL Schedina")
                if st.form_submit_button("Carica"):
                    s_id = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq_s)
                    supabase.table("schedine").insert({"squadra_id": s_id, "giornata": int(g.split()[1]), "schedina_url": u_sch}).execute(); st.rerun()
        with tab4:
            st.write("### Elimina Schedina")
            g_del = st.selectbox("Giornata Schedina", [f"Giornata {i}" for i in range(1, 39)], key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            
            # Prendi le schedine caricate per questa giornata
            schedine_g = supabase.table("schedine").select("squadra_id").eq("giornata", num_g_del).execute().data
            squadre_con_schedina = [s for s in squadre_list if s['id'] in [sch['squadra_id'] for sch in schedine_g]]
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina Selezionata"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    st.success("Schedina eliminata!")
                    st.rerun()
            else:
                st.info("Nessuna schedina in questa giornata.")
                
            st.markdown("---")
            st.write("### Elimina Squadra")
            if squadre_list:
                sq_del = st.selectbox("Squadra da eliminare", [s['nome_squadra'] for s in squadre_list], key="sq_del_tot")
                if st.button("Elimina Squadra e Tutti i Dati"):
                    s_id = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq_del)
                    supabase.table("squadre").delete().eq("id", s_id).execute()
                    supabase.table("risultati").delete().eq("squadra_id", s_id).execute()
                    supabase.table("schedine").delete().eq("squadra_id", s_id).execute()
                    st.success("Squadra eliminata!")
                    st.rerun()
            else:
                st.info("Nessuna squadra presente.")

# --- MENU CENTRALE ---
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    if st.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
with c2:
    if st.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"

st.markdown("---")

# --- CONTENUTO PAGINE ---
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

elif st.session_state.current_page == "Schedine":
    st.title("📅 Schedine")
    giornata = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)])
    num_g = int(giornata.split(" ")[1])
    squadre = supabase.table("squadre").select("*").execute().data
    schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data
    schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
    
    for s in sorted(squadre, key=lambda x: x['nome_squadra']):
        logo_html = f"<img src='{s.get('logo_url')}' style='width:40px; height:40px; border-radius:50%; object-fit:cover; margin-right:15px;' />" if s.get('logo_url') else "⚽"
        st.markdown(f"<div style='display:flex; align-items:center;'>{logo_html} <h3>{s['nome_squadra']}</h3></div>", unsafe_allow_html=True)
        url = schedine_dict.get(s['id'])
        if url: st.image(url, use_container_width=True)
        else: st.info("Nessuna schedina caricata.")
        st.markdown("---")
