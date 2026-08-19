import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS (Sidebar scura ma leggibile)
st.markdown("""
    <style>
    /* Testo generale bianco */
    html, body, [class*="css"] { color: #FFFFFF !important; }
    h1, h2, h3, h4 { color: #FFFFFF !important; text-shadow: 3px 3px 6px rgba(0, 0, 0, 1) !important; }
    
    /* CARD CLASSIFICA */
    .card { background-color: rgba(0, 0, 0, 0.85) !important; padding: 15px !important; border-radius: 12px; margin-bottom: 12px; border-left: 5px solid #4CAF50; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    
    /* SFONDO PRINCIPALE */
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; background-position: center; }
    
    /* SIDEBAR NERA */
    [data-testid="stSidebar"] {
        background-color: #111111 !important;
    }
    /* Solo i titoli/testi nella sidebar sono bianchi, i selettori mantengono il loro stile standard */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* CAMPI DI INPUT (Form registrazione e admin): Testo NERO su fondo bianco */
    .stTextInput input, .stNumberInput input { 
        color: #000000 !important; 
        background-color: #FFFFFF !important; 
        font-weight: bold;
    }
    /* Etichette dei campi bianche */
    label { color: #FFFFFF !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 4. Logica Accesso
def check_password():
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        st.sidebar.subheader("🔒 Accesso Amministratore")
        pwd = st.sidebar.text_input("Password", type="password") 
        if st.sidebar.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.rerun()
            else: st.sidebar.error("Password errata")
        return False
    return True

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Area Admin"])

if menu == "Classifica":
    st.title("🏆 Classifica Generale FantaBet")
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        risultati = supabase.table("risultati").select("*").execute().data
        if squadre:
            classifica = []
            for s in squadre:
                punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
                classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
            for pos, item in enumerate(sorted(classifica, key=lambda x: x['punti'], reverse=True), 1):
                logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽"
                st.markdown(f"""<div class="card"><div style="display:flex; align-items:center; width:100%;">
                            <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                            <span style="flex-grow:1; font-weight:bold;">{item['nome']}</span>
                            <span style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
        else:
            st.info("Nessuna squadra registrata.")
    except Exception as e: st.error(f"Errore caricamento classifica: {e}")

else:
    if check_password():
        st.title("⚙️ Area Admin")
        tab1, tab2, tab3 = st.tabs(["➕ Registra Squadra", "⚽ Gestisci Punteggi", "🗑️ Elimina"])
        
        with tab1:
            with st.form("form_squadra"):
                n = st.text_input("Nome Squadra")
                pres = st.text_input("Nome Presidente")
                vice = st.text_input("Nome Vicepresidente")
                logo = st.text_input("URL Immagine Logo")
                if st.form_submit_button("Salva Squadra"):
                    if not n:
                        st.error("Il nome della squadra è obbligatorio!")
                    else:
                        try:
                            supabase.table("squadre").insert({
                                "nome_squadra": n, 
                                "presidente": pres if pres else "", 
                                "vicepresidente": vice if vice else "", 
                                "logo_url": logo if logo else None
                            }).execute()
                            st.success(f"Squadra '{n}' creata con successo!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore database durante il salvataggio squadra: {e}")

        with tab2:
            try:
                squadre_list = supabase.table("squadre").select("*").execute().data
                if squadre_list:
                    squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_list}
                    with st.form("form_punti"):
                        sq = st.selectbox("Squadra", list(squadra_dict.keys()))
                        p = st.number_input("Punti", step=1, format="%d")
                        g = st.number_input("Giornata", min_value=1, step=1)
                        if st.form_submit_button("Conferma Punteggio"):
                            try:
                                supabase.table("risultati").insert({
                                    "squadra_id": squadra_dict[sq], 
                                    "punteggio": p, 
                                    "giornata": g
                                }).execute()
                                st.success("Punteggio registrato!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Errore database durante l'inserimento punti: {e}")
                else:
                    st.warning("Registra prima almeno una squadra.")
            except Exception as e:
                st.error(f"Errore caricamento squadre: {e}")

        with tab3:
            try:
                ris = supabase.table("risultati").select("*").execute().data
                if ris:
                    for r in ris:
                        if st.button(f"Elimina punteggio ID: {r['id'][:4]}", key=r['id']):
                            supabase.table("risultati").delete().eq("id", r['id']).execute()
                            st.success("Eliminato!")
                            st.rerun()
                else:
                    st.write("Nessun punteggio da eliminare.")
            except Exception as e:
                st.error(f"Errore caricamento risultati: {e}")
