import streamlit as st
from supabase import create_client

# Configurazione (Sostituisci con i tuoi dati trovati in Impostazioni -> API)
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co/rest/v1/"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"

st.title("⚽ Gestione Lega Fantacalcio")

# Menu laterale
menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Inserisci Risultati (Admin)"])

if menu == "Classifica":
    st.header("Classifica Generale")
    # Qui aggiungeremo la logica per leggere i dati e mostrarli
    st.write("Area dedicata alla classifica.")

elif menu == "Inserisci Risultati (Admin)":
    st.header("Area Amministratore")
    st.warning("Accesso riservato.")
    
    # Form per inserimento
    squadra = st.text_input("Nome Squadra")
    punteggio = st.number_input("Punteggio", format="%.2f")
    file = st.file_uploader("Carica foto schedina", type=['jpg', 'png'])
    
    if st.button("Salva Risultato"):
        st.success("Dati caricati correttamente!")