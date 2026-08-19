import streamlit as st
from supabase import create_client

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS con contrasto elevato e ombra nera forte
st.markdown("""
    <style>
    /* Sfondo principale con immagine e overlay scuro */
    .stApp { 
        background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); 
        background-size: cover; 
        background-attachment: fixed; 
        background-position: center; 
    }
    
    /* Tutti i testi generali in bianco con forte ombra scura */
    html, body, [class*="css"], p, span, label { 
        color: #FFFFFF !important; 
        text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.95), 0 0 10px rgba(0, 0, 0, 0.8) !important;
    }
    
    h1, h2, h3, h4 { 
        color: #FFFFFF !important; 
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 1), 0 0 15px rgba(0,0,0,0.9) !important; 
    }
    
    /* Card della classifica e schedine */
    .card { 
        background-color: rgba(15, 15, 15, 0.9) !important; 
        padding: 15px !important; 
        border-radius: 12px !important; 
        margin-bottom: 12px !important; 
        border-left: 5px solid #4CAF50 !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.8) !important; 
    }
    
    /* Sidebar scura e leggibile */
    [data-testid="stSidebar"] { background-color: #111111 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.8) !important; }
    
    /* Campi di input con testo nero su sfondo bianco */
    .stTextInput input, .stNumberInput input { 
        color: #000000 !important; 
        background-color: #FFFFFF !important; 
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 4. Logica Accesso Admin
def check_password():
    if "admin" not in st.session_state: st.session_state.admin = False
    if not st.session_state.admin:
        st.sidebar.subheader("🔒 Accesso Amministratore")
        with st.sidebar.form("form_login"):
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Entra"):
                if pwd == "capeta63": 
                    st.session_state.admin = True
                    st.rerun()
                else: st.sidebar.error("Password errata")
        return False
    return True

# Gestione della navigazione (Sidebar o Home)
menu = st.sidebar.selectbox("Navigazione", ["Home / Seleziona", "Classifica", "📅 Schedine per Giornata", "Area Admin"])

# Se l'utente sceglie la home o all'avvio, mostriamo la doppia opzione principale
if menu == "Home / Seleziona":
    st.title("⚽ Benvenuto nel FantaBet Serie A")
    st.markdown("### Scegli quale sezione vuoi consultare:")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🏆 Vai alla Classifica Generale", use_container_width=True):
            st.session_state.nav_scelta = "Classifica"
            st.rerun()
    with col_b:
        if st.button("📅 Vai alle Schedine (Giornate 1-38)", use_container_width=True):
            st.session_state.nav_scelta = "📅 Schedine per Giornata"
            st.rerun()
            
    # Gestione dello stato dei pulsanti rapidi
    if "nav_scelta" in st.session_state:
        menu = st.session_state.nav_scelta
    else:
        st.stop()

if menu == "Classifica":
    st.title("🏆 Classifica Generale FantaBet")
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        risultati = supabase.table("risultati").select("*").execute().data
        if squadre:
            classifica = []
            for s in squadre:
                punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
                logo_url = s.get('logo_url')
                classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': logo_url, 'id': s['id']})
            
            # Ordinamento: Prima per punti decrescente, poi in ordine alfabetico (A-Z)
            classifica_ordinata = sorted(classifica, key=lambda x: (-x['punti'], x['nome']))
            
            for pos, item in enumerate(classifica_ordinata, 1):
                if item['logo'] and item['logo'].startswith('http'):
                    logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' onerror=\"this.onerror=null;this.src='https://images.emojiterra.com/google/android-11/512px/26bd.png';\" />"
                else:
                    logo_html = "<span style='margin-right:15px; font-size:25px;'>⚽</span>"
                
                st.markdown(f"""<div class="card"><div style="display:flex; align-items:center; width:100%;">
                            <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                            <span style="flex-grow:1; font-weight:bold; font-size:18px;">{item['nome']}</span>
                            <span style="color:#4CAF50; font-weight:bold; font-size:18px;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
        else:
            st.info("Nessuna squadra registrata.")
    except Exception as e: st.error(f"Errore caricamento classifica: {e}")

elif menu == "📅 Schedine per Giornata":
    st.title("📅 Schedine delle Squadre - Serie A")
    
    # Selezione della giornata da 1 a 38
    giornata_scelta = st.selectbox("Seleziona la Giornata di Campionato", [f"Giornata {i}" for i in range(1, 39)])
    num_giornata = int(giornata_scelta.split(" ")[1])
    
    try:
        squadre = supabase.table("squadre").select("*").execute().data
        schedine = supabase.table("schedine").select("*").eq("giornata", num_giornata).execute().data
        
        # Mappa le schedine per squadra_id
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        
        if squadre:
            for s in sorted(squadre, key=lambda x: x['nome_squadra']):
                # Mostra il logo della squadra anche qui se disponibile
                logo_s = s.get('logo_url')
                logo_tag = f"<img src='{logo_s}' style='width:30px; height:30px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:8px;' />" if logo_s and logo_s.startswith('http') else "🛡️ "
                
                st.markdown(f"### {logo_tag} {s['nome_squadra']}")
                url_schedina = schedine_dict.get(s['id'])
                
                if url_schedina and url_schedina.startswith('http'):
                    st.image(url_schedina, caption=f"Schedina {s['nome_squadra']} - {giornata_scelta}", use_container_width=True)
                else:
                    st.info(f"Nessuna schedina caricata per {s['nome_squadra']} in questa giornata.")
                st.markdown("---")
        else:
            st.info("Nessuna squadra registrata.")
    except Exception as e:
        st.error(f"Errore nel caricamento delle schedine: {e}")

elif menu == "Area Admin":
    if check_password():
        st.title("⚙️ Area Admin")
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Registra Squadra", "⚽ Gestisci Punteggi", "🎫 Carica Schedina", "🗑️ Elimina Squadre"])
        
        # TAB 1: Registra Squadra
        with tab1:
            with st.form("form_squadra"):
                st.subheader("Crea Nuova Squadra")
                n = st.text_input("Nome Squadra")
                pres = st.text_input("Nome Presidente")
                logo = st.text_input("URL Immagine Logo (Link diretto, es. Postimages)")
                submit_sq = st.form_submit_button("Salva Squadra")
                
                if submit_sq:
                    if n:
                        supabase.table("squadre").insert({"nome_squadra": n, "presidente": pres, "logo_url": logo}).execute()
                        st.success(f"✅ **Operazione completata!** La squadra **{n}** è stata registrata con successo.")
                    else:
                        st.error("⚠️ Inserisci obbligatoriamente il nome della squadra.")

        # TAB 2: Gestisci Punteggi
        with tab2:
            squadre_list = supabase.table("squadre").select("*").execute().data
            if squadre_list:
                squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_list}
                with st.form("form_punti"):
                    st.subheader("Modifica Punteggio Squadra")
                    sq = st.selectbox("Seleziona Squadra", list(squadra_dict.keys()))
                    p = st.number_input("Punti (positivo per aggiungere, negativo es. -3 per togliere)", step=1, value=0)
                    submit_pts = st.form_submit_button("Aggiorna Punteggio")
                    
                    if submit_pts:
                        supabase.table("risultati").insert({"squadra_id": squadra_dict[sq], "punteggio": p}).execute()
                        azione = "Aggiunti" if p >= 0 else "Tolti"
                        st.success(f"✅ **Aggiornamento riuscito!** {azione} **{abs(p)} punti** alla squadra **{sq}**.")
            else:
                st.warning("Registra prima almeno una squadra.")

        # TAB 3: Carica Schedina per Giornata
        with tab3:
            squadre_list = supabase.table("squadre").select("*").execute().data
            if squadre_list:
                squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_list}
                with st.form("form_schedina_admin"):
                    st.subheader("Carica Schedina Giornaliera")
                    giornata_admin = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], key="g_adm")
                    sq_schedina = st.selectbox("Seleziona Squadra", list(squadra_dict.keys()), key="s_adm")
                    url_sch = st.text_input("URL Immagine Schedina (Link diretto)")
                    submit_sch = st.form_submit_button("Salva Schedina")
                    
                    if submit_sch:
                        num_g = int(giornata_admin.split(" ")[1])
                        s_id = squadra_dict[sq_schedina]
                        
                        # Controlla se esiste già una schedina per questa squadra in questa giornata
                        esistente = supabase.table("schedine").select("*").eq("squadra_id", s_id).eq("giornata", num_g).execute().data
                        
                        if esistente:
                            supabase.table("schedine").update({"schedina_url": url_sch}).eq("squadra_id", s_id).eq("giornata", num_g).execute()
                        else:
                            supabase.table("schedine").insert({"squadra_id": s_id, "giornata": num_g, "schedina_url": url_sch}).execute()
                            
                        st.success(f"✅ Schedina di **{sq_schedina}** per la **{giornata_admin}** caricata con successo!")
            else:
                st.warning("Registra prima almeno una squadra.")

        # TAB 4: Elimina Squadre
        with tab4:
            st.subheader("Elimina Squadre dal Database")
            squadre_del = supabase.table("squadre").select("*").execute().data
            if squadre_del:
                for s in squadre_del:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{s['nome_squadra']}** (Presidente: {s.get('presidente', 'N/D')})")
                    with col2:
                        if st.button(f"Elimina", key=f"del_{s['id']}"):
                            supabase.table("risultati").delete().eq("squadra_id", s['id']).execute()
                            supabase.table("schedine").delete().eq("squadra_id", s['id']).execute()
                            supabase.table("squadre").delete().eq("id", s['id']).execute()
                            st.success(f"🗑️ Squadra **{s['nome_squadra']}** eliminata correttamente.")
                            st.rerun()
            else:
                st.info("Nessuna squadra presente da eliminare.")
