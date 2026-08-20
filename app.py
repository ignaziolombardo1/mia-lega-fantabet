import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Nome del bucket di Supabase Storage
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
    .winner-card { background: rgba(20, 20, 20, 0.95); border: 2px solid #FFD700; padding: 20px; border-radius: 15px; text-align: center; margin: 20px 0; }
    .alert-box { background: rgba(40, 40, 40, 0.9); border-left: 5px solid #2196F3; padding: 12px; border-radius: 8px; margin-bottom: 20px; color: #fff; }
    </style>
""", unsafe_allow_html=True)

# Helper: Giornata corrente
def get_giornata_corrente():
    oggi = datetime.now().date()
    inizio = datetime(2026, 8, 23).date()
    return max(1, min(38, ((oggi - inizio).days // 7) + 1)) if oggi >= inizio else 1

giornata_idx = get_giornata_corrente() - 1

# Stato sessione
if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"
if "admin" not in st.session_state: st.session_state.admin = False

# Caricamento dati per l'admin
try:
    risultati_globali = supabase.table("risultati").select("giornata").execute().data
    giornate_completate = set(r['giornata'] for r in risultati_globali if r.get('giornata'))
except:
    giornate_completate = set()

lista_giornate_etichette = [f"Giornata {i} {'✅' if i in giornate_completate else ''}" for i in range(1, 39)]

# --- AREA ADMIN ---
with st.sidebar:
    st.subheader("⚙️ Area Amministratore")
    if not st.session_state.admin:
        pwd = st.text_input("Password", type="password")
        if st.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.rerun()
            else: st.error("Password errata")
    else:
        if st.button("Logout"): 
            st.session_state.admin = False
            st.rerun()
        
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
                    st.success("Squadra salvata!")
                    time.sleep(2)
                    st.rerun()
        
        with tab2:
            with st.form("add_p_multi"):
                g = st.selectbox("Giornata", lista_giornate_etichette, index=giornata_idx)
                num_g = int(g.split()[1])
                pts = {s['id']: st.number_input(s['nome_squadra'], 0, step=1) for s in squadre_list}
                if st.form_submit_button("Salva"):
                    for s_id, p in pts.items():
                        supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g).execute()
                        supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g}).execute()
                    st.success("Punti aggiornati!")
                    time.sleep(2)
                    st.rerun()

        with tab3:
            with st.form("add_sch_multi"):
                g = st.selectbox("Giornata", lista_giornate_etichette, index=giornata_idx)
                num_g = int(g.split()[1])
                files = {s['id']: st.file_uploader(f"Schedina {s['nome_squadra']}", type=["jpg", "png"]) for s in squadre_list}
                if st.form_submit_button("Carica Schedine"):
                    for s_id, f in files.items():
                        if f:
                            path = f"schedine/g{num_g}_{datetime.now().timestamp()}_{f.name}"
                            supabase.storage.from_(BUCKET_NAME).upload(path, f.getvalue(), {"content-type": f.type})
                            url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)
                            supabase.table("schedine").delete().eq("squadra_id", s_id).eq("giornata", num_g).execute()
                            supabase.table("schedine").insert({"squadra_id": s_id, "giornata": num_g, "schedina_url": url}).execute()
                    st.success("Schedine caricate!")
                    time.sleep(2)
                    st.rerun()

        with tab4:
            if st.button("Elimina Squadra"):
                # Logica semplificata per brevità
                st.warning("Seleziona dal menu per eliminare")

# --- AREA PUBBLICA ---
st.title("⚽ FantaBet Serie A")
c1, c2 = st.columns(2)
if c1.button("🏆 Classifica"): st.session_state.current_page = "Classifica"
if c2.button("📅 Schedine"): st.session_state.current_page = "Schedine"

st.markdown("---")

# Logica Visualizzazione
squadre = supabase.table("squadre").select("*").execute().data or []
risultati = supabase.table("risultati").select("*").execute().data or []

if st.session_state.current_page == "Classifica":
    classifica = []
    for s in squadre:
        p = sum(int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id'])
        classifica.append({'nome': s['nome_squadra'], 'punti': p, 'logo': s.get('logo_url')})
    for item in sorted(classifica, key=lambda x: -x['punti']):
        st.markdown(f"""<div class="card"><h5>{item['nome']} - {item['punti']} pts</h5></div>""", unsafe_allow_html=True)

elif st.session_state.current_page == "Schedine":
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split(" ")[1])
    schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []
    sch_dict = {s['squadra_id']: s['schedina_url'] for s in schedine}
    
    for s in squadre:
        st.markdown(f"<h5>{s['nome_squadra']}</h5>", unsafe_allow_html=True)
        url = sch_dict.get(s['id'])
        if url:
            st.image(url, width=300)
            st.markdown(f"[🔗 Apri a schermo intero]({url})")
        else:
            st.caption("Nessuna schedina.")
        st.markdown("---")
