import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# Configurazione Supabase
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Password controllo
def check_password():
    """Restituisce True se la password inserita è corretta."""
    def password_entered():
        if st.session_state["password"] == st.secrets["ADMIN_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Inserisci Password Admin", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password errata. Riprova:", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

# --- Interfaccia ---
st.title("⚽ Lega FantaBet")
menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Inserisci Punteggi"])

if menu == "Classifica":
    st.header("🏆 Classifica Generale")
    # (Inserisci qui il codice della classifica di prima)

else:
    # Qui entra in gioco la protezione
    if check_password():
        if menu == "Admin: Gestione Squadre":
            st.header("Area Protetta: Gestione Squadre")
            # (Inserisci qui il codice dell'admin di prima)
            
        elif menu == "Admin: Inserisci Punteggi":
            st.header("Area Protetta: Inserisci Punteggi")
            # (Inserisci qui il codice inserimento punteggi di prima)
    else:
        st.warning("Accesso riservato all'amministratore.")
