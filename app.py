import streamlit as st
from supabase import create_client
from datetime import datetime

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS Perfezionato
st.markdown("""
    <style>
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3 { color: #FFFFFF !important; text-shadow: 2px 2px 4px #000; }
    .card { background: rgba(30,30,30,0.8); padding: 15px; border-radius: 12px; margin-bottom: 10px; border-left: 5px solid #4CAF50; }
    .gold { border-left: 5px solid #FFD700 !important; background: rgba(255, 215, 0, 0.1) !important; }
    .silver { border-left: 5px solid #C0C0C0 !important; background: rgba(192, 192, 192, 0.1) !important; }
    .bronze { border-left: 5px solid #CD7F32 !important; background: rgba(205, 127, 50, 0.1) !important; }
    .winner-card { background: rgba(20, 20, 20, 0.95); border: 2px solid #FFD700; padding: 20px; border-radius: 15px; text-align: center; margin: 20px 0; box-shadow: 0 0 15px rgba(255, 215, 0, 0.3); }
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

# --- AREA ADMIN ---
with st.sidebar:
    st.subheader("⚙️ Area Admin")
    if not st.session_state.admin:
        pwd = st.text_input("Password", type="password")
        if st.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.success("Accesso riuscito!")
                st.rerun()
            else: 
                st.error("Password errata")
    else:
        if st.button("Logout"): 
            st.session_state.admin = False
            st.rerun()

# --- MENU E LOGICA PAGINE ---
st.title("⚽ FantaBet Serie A")
c1, c2, c3, c4 = st.columns(4)
if c1.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
if c2.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"
if c3.button("❄️ Coppa Inverno", use_container_width=True): st.session_state.current_page = "Coppa Inverno"
if c4.button("🌸 Coppa Primavera", use_container_width=True): st.session_state.current_page = "Coppa Primavera"

st.markdown("---")

# --- CARICAMENTO DATI SICURO ---
try:
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
except Exception as e:
    squadre, risultati = [], []
    st.error(f"Errore di connessione al database: {e}")

# --- CLASSIFICA GENERALE ---
if st.session_state.current_page == "Classifica":
    if squadre:
        classifica = sorted([{
            'nome': s['nome_squadra'], 
            'punti': sum(int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']), 
            'logo': s.get('logo_url')
        } for s in squadre], key=lambda x: -x['punti'])
        
        # Podio Finale (controlliamo se ci sono dati per la 38esima o se la classifica è piena)
        giornate_registrate = {r.get('giornata') for r in risultati}
        if 38 in giornate_registrate and len(classifica) >= 3:
            st.markdown("<div class='winner-card'><h2>🏆 PODIO FINALE 🏆</h2></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            podio = [col2, col1, col3] # 1°, 2°, 3°
            for i in range(3):
                with podio[i]:
                    logo_p = f"<img src='{classifica[i]['logo']}' style='width:50px; height:50px; border-radius:50%; object-fit:cover; margin-bottom:5px;' /><br>" if classifica[i]['logo'] else ""
                    st.markdown(f"### {'🥇' if i==0 else '🥈' if i==1 else '🥉'} {classifica[i]['nome']}")
                    if classifica[i]['logo']:
                        st.markdown(logo_p, unsafe_allow_html=True)
                    st.write(f"**{classifica[i]['punti']} Punti**")
        
        # Lista Classifica
        for pos, item in enumerate(classifica, 1):
            c_class = "gold" if pos == 1 else "silver" if pos == 2 else "bronze" if pos == 3 else ""
            logo_html = f"<img src='{item['logo']}' style='width:30px; height:30px; border-radius:50%; object-fit:cover; margin-right:10px;' />" if item['logo'] else "⚽ "
            st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:35px;">{pos}°</span>
                        {logo_html}
                        <span style="flex-grow:1; margin-left:5px;">{item['nome']}</span>
                        <span style="font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
    else:
        st.info("Nessuna squadra inserita nel database.")

# --- COPPE (Inverno / Primavera) ---
elif "Coppa" in st.session_state.current_page:
    is_inverno = st.session_state.current_page == "Coppa Inverno"
    target = (12, 17) if is_inverno else (27, 32)
    
    if squadre:
        classifica = sorted([{
            'nome': s['nome_squadra'], 
            'punti': sum(int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id'] and target[0] <= int(r['giornata']) <= target[1]), 
            'logo': s.get('logo_url')
        } for s in squadre], key=lambda x: -x['punti'])
        
        giornate_registrate = {r.get('giornata') for r in risultati}
        torneo_concluso = target[1] in giornate_registrate
        
        if torneo_concluso and classifica and classifica[0]['punti'] > 0:
            vincitore = classifica[0]
            logo_v = f"<img src='{vincitore['logo']}' style='width:80px; height:80px; border-radius:50%; object-fit:cover; border:3px solid #FFD700; margin-bottom:10px;' />" if vincitore['logo'] else "🏆"
            st.markdown(f"""<div class="winner-card">
                        <h2>🏆 Vincitore {st.session_state.current_page} 🏆</h2>
                        {logo_v}
                        <h1>🥇 {vincitore['nome']}</h1>
                        <p style="color:#4CAF50; font-weight:bold;">Con {vincitore['punti']} punti</p>
                        </div>""", unsafe_allow_html=True)
            st.balloons()
        
        for pos, item in enumerate(classifica, 1):
            c_class = "gold" if pos == 1 else ""
            logo_html = f"<img src='{item['logo']}' style='width:30px; height:30px; border-radius:50%; object-fit:cover; margin-right:10px;' />" if item['logo'] else "⚽ "
            st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:35px;">{pos}°</span>
                        {logo_html}
                        <span style="flex-grow:1; margin-left:5px;">{item['nome']}</span>
                        <span>{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
    else:
        st.info("Nessuna squadra inserita nel database.")

# --- PAGINA SCHEDINE ---
elif st.session_state.current_page == "Schedine":
    st.title("📅 Schedine Giornaliere")
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split(" ")[1])
    
    try:
        schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        
        if squadre:
            for s in sorted(squadre, key=lambda x: x['nome_squadra']):
                logo_html = f"<img src='{s.get('logo_url')}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:10px;' />" if s.get('logo_url') else "⚽ "
                st.markdown(f"<div style='display:flex; align-items:center; margin-top:15px;'>{logo_html} <h3>{s['nome_squadra']}</h3></div>", unsafe_allow_html=True)
                url = schedine_dict.get(s['id'])
                if url: 
                    st.image(url, use_container_width=True)
                else: 
                    st.info("Nessuna schedina caricata per questa squadra.")
                st.markdown("---")
    except Exception as e:
        st.error(f"Errore nel caricamento delle schedine: {e}")
