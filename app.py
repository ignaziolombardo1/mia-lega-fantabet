import streamlit as st
from supabase import create_client

# Configurazione Supabase
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("⚽ Gestione Lega Fantacalcio")

# Menu laterale
menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Inserisci Punteggi", "Admin: Carica Schedine"])

# --- 1. CLASSIFICA ---
if menu == "Classifica":
    st.header("Classifica Generale")
    st.write("Qui a breve vedremo la classifica calcolata automaticamente.")

# --- 2. ADMIN: GESTIONE SQUADRE ---
elif menu == "Admin: Gestione Squadre":
    st.header("Registra una nuova squadra")
    
    with st.form("form_squadra"):
        nome_squadra = st.text_input("Nome Squadra")
        presidente = st.text_input("Nome Presidente")
        vicepresidente = st.text_input("Nome Vicepresidente")
        submit_squadra = st.form_submit_button("Salva Squadra")
        
        if submit_squadra:
            if nome_squadra and presidente:
                data = {
                    "nome_squadra": nome_squadra,
                    "presidente": presidente,
                    "vicepresidente": vicepresidente
                }
                supabase.table("squadre").insert(data).execute()
                st.success(f"Squadra '{nome_squadra}' registrata con successo!")
            else:
                st.error("Inserisci almeno il nome della squadra e del presidente.")

# --- 3. ADMIN: INSERISCI PUNTEGGI ---
elif menu == "Admin: Inserisci Punteggi":
    st.header("Inserimento Punteggi per Giornata")
    
    # Recuperiamo l'elenco delle squadre dal database
    squadre_res = supabase.table("squadre").select("id, nome_squadra").execute()
    squadre = squadre_res.data
    
    if not squadre:
        st.warning("Prima devi registrare almeno una squadra nella sezione 'Admin: Gestione Squadre'.")
    else:
        # Creiamo un dizionario per associare il nome all'ID
        squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre}
        
        with st.form("form_punti"):
            squadra_scelta = st.selectbox("Seleziona Squadra", list(squadra_dict.keys()))
            giornata = st.number_input("Numero Giornata", min_value=1, max_value=38, value=1, step=1)
            punteggio = st.number_input("Punteggio (es. 74.5)", format="%.2f")
            
            submit_punti = st.form_submit_button("Salva Punteggio")
            
            if submit_punti:
                squadra_id = squadra_dict[squadra_scelta]
                data = {
                    "squadra_id": squadra_id,
                    "giornata": giornata,
                    "punteggio": punteggio
                }
                supabase.table("risultati").insert(data).execute()
                st.success(f"Punteggio di {punteggio} salvato per {squadra_scelta} (Giornata {giornata})!")

# --- 4. ADMIN: CARICA SCHEDINE ---
elif menu == "Admin: Carica Schedine (Foto)": # nota: gestiamo il caricamento visivo
    st.header("Carica Foto Schedina")
    st.info("Funzionalità in arrivo: qui potrai associare la foto della schedina alla squadra e alla giornata.")
