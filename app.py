import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# Configurazione
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="FantaBet", page_icon="⚽", layout="wide")

# CSS per abbellire le Card della classifica
st.markdown("""
    <style>
    .card { background-color: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #2e7d32; }
    .stApp { background-image: url("https://raw.githubusercontent.com/tuo-utente/tuo-repo/main/background.jpg"); background-size: cover; }
    </style>
""", unsafe_allow_html=True)

# Protezione Admin
def check_password():
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        pwd = st.sidebar.text_input("Password Admin", type="password")
        if st.sidebar.button("Entra"):
            if pwd == "Fantabet26": st.session_state.admin = True; st.rerun()
        return False
    return True

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Gestione Punteggi"])

# --- CLASSIFICA (Grafica Migliorata) ---
if menu == "Classifica":
    st.title("🏆 Classifica FantaBet")
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    
    if squadre:
        classifica = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica.append({'nome': s['nome_squadra'], 'punti': punti})
        
        for pos, item in enumerate(sorted(classifica, key=lambda x: x['punti'], reverse=True), 1):
            with st.container():
                st.markdown(f"""<div class="card">
                    <h3>{pos}°. {item['nome']} - <b>{item['punti']} punti</b></h3>
                </div>""", unsafe_allow_html=True)

# --- ADMIN (Gestione Dati) ---
else:
    if check_password():
        st.header("⚙️ Area Amministratore")
        
        # ELIMINA SQUADRE
        if menu == "Admin: Gestione Squadre":
            squadre = supabase.table("squadre").select("*").execute().data
            st.subheader("Elimina Squadra")
            for s in squadre:
                col1, col2 = st.columns([3, 1])
                col1.write(s['nome_squadra'])
                if col2.button("Elimina", key=f"del_{s['id']}"):
                    supabase.table("squadre").delete().eq("id", s['id']).execute()
                    st.rerun()

        # ELIMINA/CORREGGI PUNTEGGI
        elif menu == "Admin: Gestione Punteggi":
            st.subheader("Gestione Punteggi")
            risultati = supabase.table("risultati").select("*, squadre(nome_squadra)").execute().data
            for r in risultati:
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"{r['squadre']['nome_squadra']} - Giornata {r['giornata']}: {r['punteggio']} pts")
                if col3.button("Elimina", key=f"del_p_{r['id']}"):
                    supabase.table("risultati").delete().eq("id", r['id']).execute()
                    st.rerun()
