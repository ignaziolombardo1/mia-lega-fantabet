import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "fantabet"

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS
st.markdown("""
    <style>
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, h5 { color: #FFFFFF !important; text-shadow: 2px 2px 4px #000; }
    .card { background: rgba(30,30,30,0.8); padding: 15px; border-radius: 12px; margin-bottom: 10px; border-left: 5px solid #4CAF50; }
    .gold { border-left: 5px solid #FFD700 !important; background: rgba(255, 215, 0, 0.1) !important; }
    .silver { border-left: 5px solid #C0C0C0 !important; background: rgba(192, 192, 192, 0.1) !important; }
    .bronze { border-left: 5px solid #CD7F32 !important; background: rgba(205, 127, 50, 0.1) !important; }
    </style>
""", unsafe_allow_html=True)

# Helper
def get_giornata_corrente():
    oggi = datetime.now().date()
    inizio = datetime(2026, 8, 23).date()
    return max(1, min(38, ((oggi - inizio).days // 7) + 1)) if oggi >= inizio else 1

giornata_idx = get_giornata_corrente() - 1

if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"
if "admin" not in st.session_state: st.session_state.admin = False

# --- AREA ADMIN ---
with st.sidebar:
    st.subheader("⚙️ Area Amministratore")
    if not st.session_state.admin:
        pwd = st.text_input("Password", type="password")
        if st.button("Entra"):
            if pwd == "capeta63": st.session_state.admin = True; st.rerun()
            else: st.error("Password errata")
    else:
        if st.button("Logout"): st.session_state.admin = False; st.rerun()
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Squadra", "⚽ Punti", "🎫 Schedina", "🗑️ Elimina"])
        squadre_list = supabase.table("squadre").select("*").execute().data or []
        
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra")
                logo_file = st.file_uploader("Carica Logo", type=["png", "jpg", "jpeg"])
                if st.form_submit_button("Salva"): 
                    logo_url = ""
                    if logo_file:
                        path = f"loghi/{datetime.now().timestamp()}_{logo_file.name}"
                        supabase.storage.from_(BUCKET_NAME).upload(path, logo_file.getvalue(), {"content-type": logo_file.type})
                        logo_url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)
                    supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo_url}).execute()
                    st.success("Salvato!"); time.sleep(2); st.rerun()
        
        with tab2:
            with st.form("add_p"):
                num_g = st.number_input("Giornata", 1, 38, get_giornata_corrente())
                pts = {s['id']: st.number_input(s['nome_squadra'], 0, key=f"p_{s['id']}") for s in squadre_list}
                if st.form_submit_button("Salva Punti"):
                    for s_id, p in pts.items():
                        supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g).execute()
                        supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g}).execute()
                    st.success("Aggiornato!"); time.sleep(2); st.rerun()

        with tab3:
            with st.form("add_sch"):
                num_g = st.number_input("Giornata Schedina", 1, 38, get_giornata_corrente())
                files = {s['id']: st.file_uploader(f"Schedina {s['nome_squadra']}", type=["jpg", "png"], key=f"sch_{s['id']}") for s in squadre_list}
                if st.form_submit_button("Carica"):
                    for s_id, f in files.items():
                        if f:
                            path = f"schedine/g{num_g}_{datetime.now().timestamp()}_{f.name}"
                            supabase.storage.from_(BUCKET_NAME).upload(path, f.getvalue(), {"content-type": f.type})
                            url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)
                            supabase.table("schedine").delete().eq("squadra_id", s_id).eq("giornata", num_g).execute()
                            supabase.table("schedine").insert({"squadra_id": s_id, "giornata": num_g, "schedina_url": url}).execute()
                    st.success("Caricato!"); time.sleep(2); st.rerun()

# --- AREA PUBBLICA ---
st.title("⚽ FantaBet Serie A")
col1, col2 = st.columns(2)
if col1.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
if col2.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"

st.markdown("---")

squadre = supabase.table("squadre").select("*").execute().data or []
risultati = supabase.table("risultati").select("*").execute().data or []

if st.session_state.current_page == "Classifica":
    classifica = []
    for s in squadre:
        p = sum(int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id'])
        classifica.append({'nome': s['nome_squadra'], 'punti': p, 'logo': s.get('logo_url')})
    
    for pos, item in enumerate(sorted(classifica, key=lambda x: -x['punti']), 1):
        logo_html = f"<img src='{item['logo']}' style='width:40px; height:40px; border-radius:50%; margin-right:10px;' />" if item['logo'] else "⚽ "
        st.markdown(f"""<div class="card"><div style="display:flex; align-items:center;">
                    {logo_html} <h5>{pos}° {item['nome']} - {item['punti']} pts</h5>
                    </div></div>""", unsafe_allow_html=True)

elif st.session_state.current_page == "Schedine":
    num_g = st.selectbox("Seleziona Giornata", range(1, 39), index=giornata_idx)
    schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []
    sch_dict = {s['squadra_id']: s['schedina_url'] for s in schedine}
    for s in squadre:
        st.markdown(f"<h5>{s['nome_squadra']}</h5>", unsafe_allow_html=True)
        url = sch_dict.get(s['id'])
        if url:
            st.image(url, width=300)
            st.markdown(f"[🔗 Apri a schermo intero]({url})")
        else: st.caption("Nessuna schedina.")
        st.markdown("---")
