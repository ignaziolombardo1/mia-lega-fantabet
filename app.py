import streamlit as st
from supabase import create_client
import uuid
import pandas as pd

# 1. Configurazione Supabase (Aggiornata con i tuoi nuovi dati)
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina e Stile Grafico (Mobile-Friendly, Icona Home & Sfondo)
st.set_page_config(
    page_title="FantaBet Serie A", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <link rel="manifest" href="manifest.json">
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/logo.png">
    <style>
    html, body, [class*="css"] {
        color: #FFFFFF !important;
    }
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
    }
    .card { 
        background-color: rgba(0, 0, 0, 0.7); 
        padding: 12px 15px; 
        border-radius: 12px; 
        margin-bottom: 10px; 
        border-left: 5px solid #4CAF50; 
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
    }
    .stApp { 
        background-image: url("https://github.com/ignaziolombardo1/mia-lega-fantabet/blob/de0d9af981fb75ed84e96f7e7b6275b21c144002/background.jpg"); 
        background-size: cover; 
        background-attachment: fixed;
    }
    @media (max-width: 768px) {
        .stApp { background-attachment: scroll; }
        .block-container { padding: 1rem; }
    }
    </style>
""", unsafe_allow_html=True)

# 3. Gestione Accesso Admin Unico (Password: capeta63)
def check_password():
    if "admin" not in st.session_state: 
        st.session_state.admin = False
    
    if not st.session_state.admin:
        st.sidebar.subheader("🔒 Accesso Amministratore")
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.rerun()
            else:
                st.sidebar.error("Password errata")
        return False
    return True

# 4. Navigazione Principale
menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Area Admin (Gestione Totale)"])

# --- CLASSIFICA ---
if menu == "Classifica":
    st.title("🏆 Classifica Generale FantaBet")
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        risultati = supabase.table("risultati").select("*").execute().data
        
        if squadre:
            classifica = []
            for s in squadre:
                punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
                classifica.append({
                    'nome': s['nome_squadra'],
                    'punti': punti,
                    'logo': s.get('logo_url')
                })
            
            classifica_ordinata = sorted(classifica, key=lambda x: x['punti'], reverse=True)
            
            for pos, item in enumerate(classifica_ordinata, 1):
                logo_html = ""
                if item['logo']:
                    logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px; vertical-align:middle;' />"
                else:
                    logo_html = "<span style='font-size:24px; margin-right:12px; vertical-align:middle;'>⚽</span>"

                st.markdown(f"""
                    <div class="card">
                        <div style="display: flex; align-items: center; width: 100%;">
                            <span style="font-weight: bold; font-size: 1.1rem; width: 35px;">{pos}°</span>
                            {logo_html}
                            <span style="font-size: 1.1rem; font-weight: bold; flex-grow: 1;">{item['nome']}</span>
                            <span style="font-size: 1.2rem; font-weight: bold; color: #4CAF50; background: rgba(0,255,0,0.1); padding: 4px 12px; border-radius: 8px;">{item['punti']} pts</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuna squadra ancora registrata nella FantaBet.")
    except Exception as e:
        st.error(f"Errore nel caricamento della classifica: {e}")

# --- AREA ADMIN UNICA ---
else:
    if check_password():
        st.title("⚙️ Area Admin FantaBet")
        if st.sidebar.button("Esci dall'Admin"):
            st.session_state.admin = False
            st.rerun()
            
        tab1, tab2, tab3 = st.tabs(["➕ Registra Squadra", "⚽ Gestisci Punteggi (+ / -)", "🗑️ Elimina Dati"])
        
        # TAB 1: Registra Squadra
        with tab1:
            st.subheader("Registra Nuova Squadra")
            with st.form("form_squadra"):
                nome_squadra = st.text_input("Nome Squadra")
                presidente = st.text_input("Nome Presidente")
                vicepresidente = st.text_input("Nome Vicepresidente")
                logo_url = st.text_input("URL Immagine Logo Squadra (Opzionale)")
                
                if st.form_submit_button("Salva Squadra"):
                    if not nome_squadra:
                        st.error("Il nome della squadra è obbligatorio!")
                    else:
                        try:
                            supabase.table("squadre").insert({
                                "nome_squadra": nome_squadra,
                                "presidente": presidente if presidente else "",
                                "vicepresidente": vicepresidente if vicepresidente else "",
                                "logo_url": logo_url if logo_url else None
                            }).execute()
                            st.success(f"Squadra '{nome_squadra}' registrata con successo!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore durante il salvataggio: {e}")

        # TAB 2: Aggiungi o Togli Punti
        with tab2:
            st.subheader("Aggiungi o Togli Punti a una Squadra")
            try:
                squadre_res = supabase.table("squadre").select("id, nome_squadra").execute().data
                if squadre_res:
                    squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_res}
                    with st.form("form_punti_mod"):
                        squadra_scelta = st.selectbox("Seleziona Squadra", list(squadra_dict.keys()))
                        operazione = st.radio("Azione", ["Aggiungi Punti (+)", "Togli Punti (-)"])
                        giornata = st.number_input("Numero Giornata", min_value=1, step=1)
                        valore = st.number_input("Quantità Punti", min_value=0, step=1, format="%d")
                        
                        if st.form_submit_button("Conferma Punteggio"):
                            punteggio_finale = -valore if operazione == "Togli Punti (-)" else valore
                            supabase.table("risultati").insert({
                                "squadra_id": squadra_dict[squadra_scelta],
                                "giornata": giornata,
                                "punteggio": punteggio_finale
                            }).execute()
                            st.success(f"Operazione completata! Registrati {punteggio_finale} punti per {squadra_scelta}.")
                else:
                    st.warning("Registra prima almeno una squadra nella scheda precedente.")
            except Exception as e:
                st.error("Errore nel caricamento delle squadre.")

        # TAB 3: Elimina Squadre o Punteggi errati
        with tab3:
            st.subheader("Gestione ed Eliminazione")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("### Elimina Squadre")
                squadre = supabase.table("squadre").select("*").execute().data
                if squadre:
                    for s in squadre:
                        if st.button(f"Elimina {s['nome_squadra']}", key=f"del_sq_{s['id']}"):
                            supabase.table("risultati").delete().eq("squadra_id", s['id']).execute()
                            supabase.table("squadre").delete().eq("id", s['id']).execute()
                            st.success(f"Squadra eliminata!")
                            st.rerun()
                else:
                    st.write("Nessuna squadra.")
                    
            with col_b:
                st.markdown("### Elimina Punteggi")
                risultati = supabase.table("risultati").select("*, squadre(nome_squadra)").execute().data
                if risultati:
                    for r in risultati:
                        nome_sq = r['squadre']['nome_squadra'] if r['squadre'] else "Squadra rimossa"
                        if st.button(f"Del {nome_sq} (Giornata {r['giornata']}: {r['punteggio']} pts)", key=f"del_p_{r['id']}"):
                            supabase.table("risultati").delete().eq("id", r['id']).execute()
                            st.success("Punteggio eliminato!")
                            st.rerun()
                else:
                    st.write("Nessun punteggio.")
