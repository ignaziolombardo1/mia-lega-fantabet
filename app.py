import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# 1. Configurazione Supabase
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina e Stile Grafico con Sfondo Personalizzato
st.set_page_config(page_title="FantaBet", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .card { 
        background-color: rgba(255, 255, 255, 0.9); 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 10px; 
        border-left: 5px solid #2e7d32; 
        color: #000000;
    }
    .stApp { 
        background-image: url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/4a866b472531ce29775b4ff679efa3b806c5ba47/background.jpg"); 
        background-size: cover; 
        background-attachment: fixed;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Protezione Area Admin con Password
def check_password():
    if "admin" not in st.session_state: 
        st.session_state.admin = False
    if not st.session_state.admin:
        pwd = st.sidebar.text_input("Password Admin", type="password")
        if st.sidebar.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.rerun()
            else:
                st.sidebar.error("Password errata")
        return False
    return True

# 4. Menu di Navigazione
menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Aggiungi/Togli Punti", "Admin: Gestione Punteggi"])

# --- CLASSIFICA (Grafica a Card) ---
if menu == "Classifica":
    st.title("🏆 Classifica Generale FantaBet")
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    
    if squadre:
        classifica = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica.append({'nome': s['nome_squadra'], 'punti': punti})
        
        # Ordinamento dal punteggio più alto al più basso
        classifica_ordinata = sorted(classifica, key=lambda x: x['punti'], reverse=True)
        
        for pos, item in enumerate(classifica_ordinata, 1):
            st.markdown(f"""
                <div class="card">
                    <h3>{pos}°. {item['nome']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>{item['punti']} punti</b></h3>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nessuna squadra ancora registrata nella FantaBet.")

# --- AREA ADMIN ---
else:
    if check_password():
        st.header("⚙️ Area Amministratore FantaBet")
        
        # GESTIONE SQUADRE (Registrazione e Eliminazione)
        if menu == "Admin: Gestione Squadre":
            st.subheader("Registra Nuova Squadra")
            with st.form("form_squadra"):
                nome_squadra = st.text_input("Nome Squadra")
                presidente = st.text_input("Nome Presidente")
                vicepresidente = st.text_input("Nome Vicepresidente")
                logo = st.file_uploader("Logo Squadra", type=['jpg', 'png'])
                
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
                    st.success(f"Squadra '{nome_squadra}' registrata con successo!")
                    st.rerun()

            st.markdown("---")
            st.subheader("Elimina Squadra")
            squadre = supabase.table("squadre").select("*").execute().data
            if squadre:
                for s in squadre:
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{s['nome_squadra']}** (Pres: {s.get('presidente', '-')})")
                    if col2.button("Elimina", key=f"del_sq_{s['id']}"):
                        supabase.table("risultati").delete().eq("squadra_id", s['id']).execute()
                        supabase.table("squadre").delete().eq("id", s['id']).execute()
                        st.success(f"Squadra eliminata!")
                        st.rerun()
            else:
                st.write("Nessuna squadra presente.")

        # AGGIUNGI O TOGLI PUNTI
        elif menu == "Admin: Aggiungi/Togli Punti":
            st.subheader("Modifica Punteggio (Aggiungi o Togli)")
            squadre_res = supabase.table("squadre").select("id, nome_squadra").execute().data
            
            if squadre_res:
                squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_res}
                with st.form("form_punti_mod"):
                    squadra_scelta = st.selectbox("Seleziona Squadra", list(squadra_dict.keys()))
                    operazione = st.radio("Azione", ["Aggiungi Punti (+)", "Togli Punti (-)"])
                    giornata = st.number_input("Numero Giornata", min_value=1, step=1)
                    valore = st.number_input("Quantità Punti", min_value=0, step=1, format="%d")
                    
                    if st.form_submit_button("Conferma"):
                        punteggio_finale = -valore if operazione == "Togli Punti (-)" else valore
                        
                        supabase.table("risultati").insert({
                            "squadra_id": squadra_dict[squadra_scelta],
                            "giornata": giornata,
                            "punteggio": punteggio_finale
                        }).execute()
                        st.success(f"Operazione completata! Registrati {punteggio_finale} punti per {squadra_scelta}.")
            else:
                st.warning("Registra prima almeno una squadra.")

        # GESTIONE / ELIMINA PUNTEGGI
        elif menu == "Admin: Gestione Punteggi":
            st.subheader("Elenco Punteggi e Modifica/Eliminazione")
            risultati = supabase.table("risultati").select("*, squadre(nome_squadra)").execute().data
            
            if risultati:
                for r in risultati:
                    nome_sq = r['squadre']['nome_squadra'] if r['squadre'] else "Squadra rimossa"
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"⚽ **{nome_sq}** — Giornata {r['giornata']}: **{r['punteggio']} punti**")
                    if col2.button("Elimina", key=f"del_p_{r['id']}"):
                        supabase.table("risultati").delete().eq("id", r['id']).execute()
                        st.success("Punteggio eliminato!")
                        st.rerun()
            else:
                st.info("Nessun punteggio inserito finora.")
