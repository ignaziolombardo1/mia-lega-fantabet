import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# 1. Configurazione
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina e Stile (Sfondo)
st.set_page_config(page_title="FantaBet", page_icon="⚽")
# IMPORTANTE: Cambia 'tuo-utente' e 'tuo-repo' con i tuoi dati GitHub reali!
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://raw.githubusercontent.com/tuo-utente/tuo-repo/main/background.jpg");
        background-size: cover;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("⚽ Lega FantaBet")

# 3. Gestione Password Admin
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        pwd = st.sidebar.text_input("Password Admin", type="password")
        if st.sidebar.button("Accedi"):
            if pwd == "Fantabet26": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.sidebar.error("Password errata")
        return False
    return True

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Inserisci Punteggi"])

# --- PAGINA CLASSIFICA ---
if menu == "Classifica":
    st.header("🏆 Classifica Generale")
    risultati = supabase.table("risultati").select("*").execute().data
    squadre = supabase.table("squadre").select("*").execute().data
    
    if squadre:
        data = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            data.append({'Squadra': s['nome_squadra'], 'Punti': punti})
        
        df = pd.DataFrame(data).sort_values(by='Punti', ascending=False)
        st.table(df)
    else:
        st.info("Nessuna squadra registrata.")

# --- PAGINA ADMIN ---
else:
    if check_password():
        if menu == "Admin: Gestione Squadre":
            st.header("Gestione Squadre")
            with st.form("form_squadra"):
                nome_squadra = st.text_input("Nome Squadra")
                presidente = st.text_input("Presidente")
                logo = st.file_uploader("Logo", type=['jpg', 'png'])
                if st.form_submit_button("Salva"):
                    # Logica upload
                    logo_name = f"{uuid.uuid4()}.png" if logo else None
                    if logo: supabase.storage.from_("leghe-fantabet").upload(logo_name, logo.getvalue())
                    supabase.table("squadre").insert({"nome_squadra": nome_squadra, "presidente": presidente, "logo_url": logo_name}).execute()
                    st.success("Squadra creata!")

        elif menu == "Admin: Inserisci Punteggi":
            st.header("Inserisci Punteggi")
            squadre_res = supabase.table("squadre").select("id, nome_squadra").execute().data
            if squadre_res:
                squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_res}
                with st.form("form_punti"):
                    squadra = st.selectbox("Squadra", list(squadra_dict.keys()))
                    giornata = st.number_input("Giornata", 1, 38)
                    punteggio = st.number_input("Punti", 0, 100)
                    if st.form_submit_button("Salva"):
                        supabase.table("risultati").insert({"squadra_id": squadra_dict[squadra], "giornata": giornata, "punteggio": punteggio}).execute()
                        st.success("Punteggio salvato!")
