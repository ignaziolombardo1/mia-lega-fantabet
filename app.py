import streamlit as st
from supabase import create_client

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS
st.markdown("""
    <style>
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3 { color: #FFFFFF !important; text-shadow: 3px 3px 6px rgba(0, 0, 0, 1); }
    .card { background-color: rgba(15, 15, 15, 0.85) !important; padding: 15px !important; border-radius: 12px !important; margin-bottom: 12px !important; border-left: 5px solid #4CAF50 !important; }
    .winner-card { background: rgba(20, 20, 20, 0.95); border: 2px solid #FFD700; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; box-shadow: 0px 0px 20px rgba(255, 215, 0, 0.4); }
    </style>
""", unsafe_allow_html=True)

# Gestione stato navigazione
if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"
if "admin" not in st.session_state: st.session_state.admin = False

# --- SIDEBAR (Area Admin) ---
with st.sidebar:
    st.subheader("⚙️ Area Amministratore")
    if not st.session_state.admin:
        pwd = st.text_input("Password", type="password")
        if st.button("Entra"):
            if pwd == "capeta63": st.session_state.admin = True; st.rerun()
            else: st.error("Password errata")
    else:
        st.success("Accesso Effettuato")
        if st.button("Logout"): st.session_state.admin = False; st.rerun()
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Squadra", "⚽ Punti", "🎫 Schedina", "🗑️ Elimina"])
        squadre_list = supabase.table("squadre").select("*").execute().data
        
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra"); logo = st.text_input("URL Logo")
                if st.form_submit_button("Salva"): 
                    supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo}).execute()
                    st.success("Squadra salvata!")
                    st.rerun()
                    
        with tab2:
            st.write("### Inserisci Punti Giornata")
            if squadre_list:
                with st.form("add_p_multi"):
                    g_pts = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], key="g_pts_multi")
                    num_g_pts = int(g_pts.split()[1])
                    
                    punti_inseriti = {}
                    for s in sorted(squadre_list, key=lambda x: x['nome_squadra']):
                        punti_inseriti[s['id']] = st.number_input(f"{s['nome_squadra']}", min_value=0, step=1, key=f"pts_{s['id']}")
                    
                    if st.form_submit_button("Salva Tutti i Punti"):
                        for s_id, p in punti_inseriti.items():
                            # Rimuoviamo eventuali punti precedenti per quella giornata e squadra per evitare duplicati
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0: # Salviamo anche lo zero se l'utente lo inserisce esplicitamente
                                supabase.table("risultati").insert({
                                    "squadra_id": s_id, 
                                    "punteggio": p, 
                                    "giornata": num_g_pts
                                }).execute()
                        st.success("Punti aggiornati con successo per tutte le squadre!")
                        st.rerun()
                
                st.markdown("---")
                st.write("### Azzera Punti Squadra")
                with st.form("reset_p_single"):
                    g_reset = st.selectbox("Giornata da azzerare", [f"Giornata {i}" for i in range(1, 39)], key="g_reset_pts")
                    num_g_reset = int(g_reset.split()[1])
                    sq_reset = st.selectbox("Squadra", [s['nome_squadra'] for s in sorted(squadre_list, key=lambda x: x['nome_squadra'])], key="sq_reset_pts")
                    
                    if st.form_submit_button("Azzera Punti Squadra"):
                        s_id_reset = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq_reset)
                        supabase.table("risultati").delete().eq("squadra_id", s_id_reset).eq("giornata", num_g_reset).execute()
                        st.success(f"Punti azzerati per {sq_reset} nella {g_reset}!")
                        st.rerun()
            else:
                st.info("Aggiungi prima almeno una squadra.")
                
        with tab3:
            st.write("### Carica Schedine Giornata")
            if squadre_list:
                with st.form("add_sch_multi"):
                    g = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], key="g_sch_multi")
                    num_g_sch = int(g.split()[1])
                    
                    schedine_inserite = {}
                    for s in sorted(squadre_list, key=lambda x: x['nome_squadra']):
                        schedine_inserite[s['id']] = st.text_input(f"URL Schedina - {s['nome_squadra']}", key=f"sch_{s['id']}")
                    
                    if st.form_submit_button("Carica Tutte le Schedine"):
                        for s_id, url in schedine_inserite.items():
                            if url and url.startswith("http"):
                                supabase.table("schedine").delete().eq("squadra_id", s_id).eq("giornata", num_g_sch).execute()
                                supabase.table("schedine").insert({
                                    "squadra_id": s_id, 
                                    "giornata": num_g_sch, 
                                    "schedina_url": url
                                }).execute()
                        st.success("Schedine caricate con successo!")
                        st.rerun()
            else:
                st.info("Aggiungi prima almeno una squadra.")
                        
        with tab4:
            st.write("### Elimina Schedina")
            g_del = st.selectbox("Giornata", [f"Giornata {i}" for i in range(1, 39)], key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            schedine_g = supabase.table("schedine").select("squadra_id").eq("giornata", num_g_del).execute().data
            squadre_con_schedina = [s for s in squadre_list if s['id'] in [sch['squadra_id'] for sch in schedine_g]] if squadre_list else []
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    st.success("Schedina eliminata!")
                    st.rerun()
            else:
                st.info("Nessuna schedina in questa giornata.")
                
            st.markdown("---")
            st.write("### Elimina Squadra")
            if squadre_list:
                sq_del = st.selectbox("Squadra", [s['nome_squadra'] for s in squadre_list], key="sq_del_tot")
                if st.button("Elimina Squadra e Dati"):
                    s_id = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq_del)
                    supabase.table("squadre").delete().eq("id", s_id).execute()
                    supabase.table("risultati").delete().eq("squadra_id", s_id).execute()
                    supabase.table("schedine").delete().eq("squadra_id", s_id).execute()
                    st.success("Squadra eliminata!")
                    st.rerun()
            else:
                st.info("Nessuna squadra presente.")

# --- MENU CENTRALE ---
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    if st.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
with c2:
    if st.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"
with c3:
    if st.button("❄️ Coppa Inverno", use_container_width=True): st.session_state.current_page = "Coppa Inverno"
with c4:
    if st.button("🌸 Coppa Primavera", use_container_width=True): st.session_state.current_page = "Coppa Primavera"

st.markdown("---")

# --- PAGINA CLASSIFICA GENERALE ---
if st.session_state.current_page == "Classifica":
    st.title("🏆 Classifica Generale")
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    if squadre:
        classifica = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
        for pos, item in enumerate(sorted(classifica, key=lambda x: (-x['punti'], x['nome'])), 1):
            logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽"
            st.markdown(f"""<div class="card"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                        <span style="flex-grow:1; font-weight:bold;">{item['nome']}</span>
                        <span style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)

# --- PAGINA SCHEDINE ---
elif st.session_state.current_page == "Schedine":
    st.title("📅 Schedine")
    giornata = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], key="g_view_sch")
    num_g = int(giornata.split(" ")[1])
    squadre = supabase.table("squadre").select("*").execute().data
    schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data
    schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
    
    if squadre:
        for s in sorted(squadre, key=lambda x: x['nome_squadra']):
            logo_html = f"<img src='{s.get('logo_url')}' style='width:40px; height:40px; border-radius:50%; object-fit:cover; margin-right:15px;' />" if s.get('logo_url') else "⚽"
            st.markdown(f"<div style='display:flex; align-items:center;'>{logo_html} <h3>{s['nome_squadra']}</h3></div>", unsafe_allow_html=True)
            url = schedine_dict.get(s['id'])
            if url: st.image(url, use_container_width=True)
            else: st.info("Nessuna schedina caricata.")
            st.markdown("---")

# --- PAGINA COPPA INVERNO (Giornate 12 - 17) ---
elif st.session_state.current_page == "Coppa Inverno":
    st.title("❄️ Coppa Inverno")
    st.markdown("### Conteggio punti valido dalla 12ª alla 17ª giornata")
    
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    
    if squadre:
        classifica_coppa = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati 
                         if r['squadra_id'] == s['id'] and r.get('giornata') is not None and 12 <= int(r['giornata']) <= 17])
            classifica_coppa.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
        
        classifica_ordinata = sorted(classifica_coppa, key=lambda x: (-x['punti'], x['nome']))
        
        giornate_inserite = [int(r['giornata']) for r in risultati if r.get('giornata') is not None]
        torneo_concluso = any(g >= 18 for g in giornate_inserite)
        
        if torneo_concluso and classifica_ordinata and classifica_ordinata[0]['punti'] > 0:
            vincitore = classifica_ordinata[0]
            logo_vincitore = f"<img src='{vincitore['logo']}' style='width:90px; height:90px; border-radius:50%; object-fit:cover; border: 3px solid #FFD700; margin-bottom: 10px;' />" if vincitore['logo'] else "🏆"
            st.markdown(f"""
                <div class="winner-card">
                    <h2 style="color: #FFD700 !important; margin-bottom: 15px;">🏆 Vincitore Coppa Inverno 🏆</h2>
                    {logo_vincitore}
                    <h1 style="color: #FFFFFF !important; margin: 5px 0;">{vincitore['nome']}</h1>
                    <p style="color: #4CAF50; font-size: 18px; font-weight: bold; margin: 0;">Con {vincitore['punti']} punti</p>
                </div>
            """, unsafe_allow_html=True)
            st.balloons()
        
        st.markdown("---")
        st.markdown("### Classifica Parziale Coppa Inverno")
        for pos, item in enumerate(classifica_ordinata, 1):
            logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽"
            st.markdown(f"""<div class="card"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                        <span style="flex-grow:1; font-weight:bold;">{item['nome']}</span>
                        <span style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)

# --- PAGINA COPPA PRIMAVERA (Giornate 27 - 32) ---
elif st.session_state.current_page == "Coppa Primavera":
    st.title("🌸 Coppa Primavera")
    st.markdown("### Conteggio punti valido dalla 27ª alla 32ª giornata")
    
    squadre = supabase.table("squadre").select("*").execute().data
    risultati = supabase.table("risultati").select("*").execute().data
    
    if squadre:
        classifica_coppa = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati 
                         if r['squadra_id'] == s['id'] and r.get('giornata') is not None and 27 <= int(r['giornata']) <= 32])
            classifica_coppa.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
        
        classifica_ordinata = sorted(classifica_coppa, key=lambda x: (-x['punti'], x['nome']))
        
        giornate_inserite = [int(r['giornata']) for r in risultati if r.get('giornata') is not None]
        torneo_concluso = any(g >= 33 for g in giornate_inserite)
        
        if torneo_concluso and classifica_ordinata and classifica_ordinata[0]['punti'] > 0:
            vincitore = classifica_ordinata[0]
            logo_vincitore = f"<img src='{vincitore['logo']}' style='width:90px; height:90px; border-radius:50%; object-fit:cover; border: 3px solid #FFD700; margin-bottom: 10px;' />" if vincitore['logo'] else "🏆"
            st.markdown(f"""
                <div class="winner-card">
                    <h2 style="color: #FFD700 !important; margin-bottom: 15px;">🏆 Vincitore Coppa Primavera 🏆</h2>
                    {logo_vincitore}
                    <h1 style="color: #FFFFFF !important; margin: 5px 0;">{vincitore['nome']}</h1>
                    <p style="color: #4CAF50; font-size: 18px; font-weight: bold; margin: 0;">Con {vincitore['punti']} punti</p>
                </div>
            """, unsafe_allow_html=True)
            st.balloons()
        
        st.markdown("---")
        st.markdown("### Classifica Parziale Coppa Primavera")
        for pos, item in enumerate(classifica_ordinata, 1):
            logo_html = f"<img src='{item['logo']}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽"
            st.markdown(f"""<div class="card"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:35px;">{pos}°</span>{logo_html}
                        <span style="flex-grow:1; font-weight:bold;">{item['nome']}</span>
                        <span style="color:#4CAF50; font-weight:bold;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
