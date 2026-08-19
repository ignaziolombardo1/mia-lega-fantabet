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
    [data-testid="stSidebar"] { background-color: #111111 !important; }
    </style>
""", unsafe_allow_html=True)

# Gestione stato navigazione
if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"

# --- MENU IN ALTO (AFFIANCATO) ---
col_menu1, col_menu2, col_menu3 = st.columns([1, 1, 4])
with col_menu1:
    if st.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
with col_menu2:
    if st.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"

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
        # Intestazione con logo e nome affiancati
        logo_url = s.get('logo_url')
        logo_html = f"<img src='{logo_url}' style='width:40px; height:40px; border-radius:50%; object-fit:cover; margin-right:15px;' />" if logo_url else "⚽"
        
        st.markdown(f"""<div style="display:flex; align-items:center; margin-bottom:10px;">
                    {logo_html} <h3 style="margin:0;">{s['nome_squadra']}</h3></div>""", unsafe_allow_html=True)
        
        url = schedine_dict.get(s['id'])
        if url and url.startswith('http'): 
            st.image(url, use_container_width=True)
        else: 
            st.info(f"Nessuna schedina caricata per {s['nome_squadra']}.")
        st.markdown("---")

# Sidebar per Admin
with st.sidebar:
    if st.button("⚙️ Area Admin"): st.session_state.current_page = "Admin"
