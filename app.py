import streamlit as st
from supabase import create_client
import uuid

SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("⚽ Gestione Lega Fantacalcio")

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Inserisci Punteggi"])

# --- 1. CLASSIFICA ---
if menu == "Classifica":
    st.header("Classifica Generale")
    risultati = supabase.table("risultati").select("*").execute().data
    squadre = supabase.table("squadre").select("*").execute().data
    
    for s in squadre:
        punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
        col1, col2 = st.columns([1, 4])
        if s.get('logo_url'):
            # Genera il link pubblico dell'immagine
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/leghe-fantacalcio/{s['logo_url']}"
            col1.image(public_url, width=50)
        col2.write(f"### {s['nome_squadra']}: {punti} punti")

# --- 2. ADMIN: GESTIONE SQUADRE ---
elif menu == "Admin: Gestione Squadre":
    st.header("Registra squadra")
    with st.form("form_squadra"):
        nome_squadra = st.text_input("Nome Squadra")
        presidente = st.text_input("Nome Presidente")
        vicepresidente = st.text_input("Nome Vicepresidente")
        logo = st.file_uploader("Carica Logo", type=['jpg', 'png'])
        
        if st.form_submit_button("Salva Squadra"):
            logo_name = None
            if logo:
                logo_name = f"{uuid.uuid4()}.png"
                supabase.storage.from_("leghe-fantacalcio").upload(logo_name, logo.getvalue())
            
            supabase.table("squadre").insert({
                "nome_squadra": nome_squadra,
                "presidente": presidente,
                "vicepresidente": vicepresidente,
                "logo_url": logo_name
            }).execute()
            st.success("Squadra creata!")
