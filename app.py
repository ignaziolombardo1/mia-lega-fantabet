import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# Configurazione Supabase
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurazione Pagina e Stile
st.set_page_config(page_title="FantaBet", page_icon="⚽")
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://raw.githubusercontent.com/tuo-nome-utente/nome-del-tuo-repo/main/background.jpg");
        background-size: cover;
        background-attachment: fixed;
    }
    .stTable { background-color: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("⚽ Lega FantaBet")

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Inserisci Punteggi"])

# --- 1. CLASSIFICA ---
if menu == "Classifica":
    st.header("🏆 Classifica Generale FantaBet")
    risultati = supabase.table("risultati").select("*").execute().data
    squadre = supabase.table("squadre").select("*").execute().data
    
    if squadre:
        classifica_data = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica_data.append({'Squadra': s['nome_squadra'], 'Punti': punti})
        
        df = pd.DataFrame(classifica_data).sort_values(by='Punti', ascending=False)
        st.table(df) # Tabella elegante
    else:
        st.info("Nessuna squadra registrata.")

# --- 2. ADMIN: GESTIONE SQUADRE ---
elif menu == "Admin: Gestione Squadre":
    st.header("Registra Squadra FantaBet")
    with st.form("form_squadra"):
        nome_squadra = st.text_input("Nome Squadra")
        presidente = st.text_input("Nome Presidente")
        vicepresidente = st.text_input("Nome Vicepresidente")
        logo = st.file_uploader("Carica Logo", type=['jpg', 'png'])
        
        if st.form_submit_button("Salva Squadra"):
            logo_name = None
            if logo:
                logo_name = f"{uuid.uuid4()}.png"
                supabase.storage.from_("leghe-fantabet").upload(logo_name, logo.getvalue())
            
            supabase.table("squadre").insert({
                "nome_squadra": nome_squadra,
                "presidente": presidente,
                "vicepresidente": vicepresidente,
                "logo_url": logo_name
            }).execute()
            st.success("Squadra creata!")

# --- 3. ADMIN: INSERISCI PUNTEGGI ---
elif menu == "Admin: Inserisci Punteggi":
    st.header("Inserisci Punteggi")
    squadre_res = supabase.table("squadre").select("id, nome_squadra").execute().data
    
    if squadre_res:
        squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_res}
        with st.form("form_punti"):
            squadra_scelta = st.selectbox("Seleziona Squadra", list(squadra_dict.keys()))
            giornata = st.number_input("Giornata", min_value=1, step=1)
            punteggio = st.number_input("Punteggio", min_value=0, step=1, format="%d")
            
            if st.form_submit_button("Salva"):
                supabase.table("risultati").insert({
                    "squadra_id": squadra_dict[squadra_scelta],
                    "giornata": giornata,
                    "punteggio": punteggio
                }).execute()
                st.success("Punteggio salvato!")
