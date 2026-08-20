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
    .winner-card { background: rgba(20, 20, 20, 0.95); border: 2px solid #FFD700; padding: 20px; border-radius: 15px; text-align: center; margin: 20px 0; }
    </style>
""", unsafe_allow_html=True)

def get_giornata_corrente():
    oggi = datetime.now().date()
    inizio = datetime(2026, 8, 23).date()
    return max(1, min(38, ((oggi - inizio).days // 7) + 1)) if oggi >= inizio else 1

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
        squadre_list = sorted(supabase.table("squadre").select("*").execute().data or [], key=lambda x: x['nome_squadra'])
        
        tab1, tab2, tab3 = st.tabs(["➕ Squadra", "⚽ Punti", "🎫 Schedina"])
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra")
                logo = st.file_uploader("Logo", type=["png", "jpg"])
                if st.form_submit_button("Salva"):
                    url = ""
                    if logo:
                        path = f"loghi/{datetime.now().timestamp()}_{logo.name}"
                        supabase.storage.from_(BUCKET_NAME).upload(path, logo.getvalue(), {"content-type": logo.type})
                        url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)
                    supabase.table("squadre").insert({"nome_squadra": n, "logo_url": url}).execute()
                    st.success("Salvataggio..."); time.sleep(2); st.rerun()
        with tab2:
            with st.form("add_p"):
                num_g = st.number_input("Giornata", 1, 38, get_giornata_corrente())
                pts = {s['id']: st.number_input(s['nome_squadra'], 0) for s in squadre_list}
                if st.form_submit_button("Salva"):
                    for s_id, p in pts.items():
                        supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g).execute()
                        supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g}).execute()
                    st.success("Salvataggio..."); time.sleep(2); st.rerun()
        with tab3:
            with st.form("add_sch"):
                num_g = st.number_input("Giornata", 1, 38, get_giornata_corrente())
                files = {s['id']: st.file_uploader(f"Schedina {s['nome_squadra']}", type=["jpg", "png"]) for s in squadre_list}
                if st.form_submit_button("Carica"):
                    for s_id, f in files.items():
                        if f:
                            path = f"schedine/g{num_g}_{datetime.now().timestamp()}_{f.name}"
                            supabase.storage.from_(BUCKET_NAME).upload(path, f.getvalue(), {"content-type": f.type})
                            url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)
                            supabase.table("schedine").delete().eq("squadra_id", s_id).eq("giornata", num_g).execute()
                            supabase.table("schedine").insert({"squadra_id": s_id, "giornata": num_g, "schedina_url": url}).execute()
                    st.success("Caricamento..."); time.sleep(2); st.rerun()

# --- AREA PUBBLICA ---
st.title("⚽ FantaBet Serie A")
menu = st.columns(4)
if menu[0].button("🏆 Classifica"): st.session_state.current_page = "Classifica"
if menu[1].button("📅 Schedine"): st.session_state.current_page = "Schedine"
if menu[2].button("❄️ Inverno"): st.session_state.current_page = "Coppa Inverno"
if menu[3].button("🌸 Primavera"): st.session_state.current_page = "Coppa Primavera"

st.markdown("---")

squadre = sorted(supabase.table("squadre").select("*").execute().data or [], key=lambda x: x['nome_squadra'])
risultati = supabase.table("risultati").select("*").execute().data or []

def get_punti(s_id, target_g=None):
    res = [r for r in risultati if r['squadra_id'] == s_id]
    if target_g: res = [r for r in res if target_g[0] <= r['giornata'] <= target_g[1]]
    return sum(r['punteggio'] for r in res)

if st.session_state.current_page in ["Classifica", "Coppa Inverno", "Coppa Primavera"]:
    target = None
    if "Inverno" in st.session_state.current_page: target = (12, 17)
    if "Primavera" in st.session_state.current_page: target = (27, 32)
    
    classifica = sorted([{'nome': s['nome_squadra'], 'punti': get_punti(s['id'], target), 'logo': s.get('logo_url')} 
                         for s in squadre], key=lambda x: (-x['punti'], x['nome']))
    
    for pos, item in enumerate(classifica, 1):
        c = "gold" if pos==1 else "silver" if pos==2 else "bronze" if pos==3 else ""
        logo = f"<img src='{item['logo']}' style='width:40px;height:40px;border-radius:50%;margin-right:10px;' />" if item['logo'] else "⚽ "
        st.markdown(f"""<div class="card {c}"><div style="display:flex; align-items:center;">
                    {logo} <h5>{pos}° {item['nome']} - {item['punti']} pts</h5></div></div>""", unsafe_allow_html=True)

elif st.session_state.current_page == "Schedine":
    num_g = st.selectbox("Seleziona Giornata", range(1, 39), index=get_giornata_corrente()-1)
    sch_dict = {s['squadra_id']: s['schedina_url'] for s in supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []}
    for s in squadre:
        st.markdown(f"<h5>{s['nome_squadra']}</h5>", unsafe_allow_html=True)
        url = sch_dict.get(s['id'])
        if url:
            st.image(url, width=300)
            st.markdown(f"[🔗 Apri a schermo intero]({url})")
        else: st.caption("Nessuna schedina.")
        st.markdown("---")
