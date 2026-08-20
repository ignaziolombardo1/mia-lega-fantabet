import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Nome del bucket di Supabase Storage per le immagini
BUCKET_NAME = "fantabet"

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS Perfezionato
st.markdown("""
    <style>
    .stApp { background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3 { color: #FFFFFF !important; text-shadow: 2px 2px 4px #000; }
    .card { background: rgba(30,30,30,0.8); padding: 15px; border-radius: 12px; margin-bottom: 10px; border-left: 5px solid #4CAF50; }
    .gold { border-left: 5px solid #FFD700 !important; background: rgba(255, 215, 0, 0.1) !important; }
    .silver { border-left: 5px solid #C0C0C0 !important; background: rgba(192, 192, 192, 0.1) !important; }
    .bronze { border-left: 5px solid #CD7F32 !important; background: rgba(205, 127, 50, 0.1) !important; }
    .winner-card { background: rgba(20, 20, 20, 0.95); border: 2px solid #FFD700; padding: 20px; border-radius: 15px; text-align: center; margin: 20px 0; box-shadow: 0 0 15px rgba(255, 215, 0, 0.3); }
    .alert-box { background: rgba(40, 40, 40, 0.9); border-left: 5px solid #2196F3; padding: 12px; border-radius: 8px; margin-bottom: 20px; color: #fff; }
    </style>
""", unsafe_allow_html=True)

# Helper: Giornata corrente
def get_giornata_corrente():
    oggi = datetime.now().date()
    inizio = datetime(2026, 8, 23).date()
    return max(1, min(38, ((oggi - inizio).days // 7) + 1)) if oggi >= inizio else 1

giornata_idx = get_giornata_corrente() - 1

# Stato sessione
if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"
if "admin" not in st.session_state: st.session_state.admin = False

# Caricamento dati globali utili per l'admin
try:
    risultati_globali = supabase.table("risultati").select("giornata").execute().data
    giornate_completate = set(r['giornata'] for r in risultati_globali if r.get('giornata'))
except:
    giornate_completate = set()

lista_giornate_etichette = [f"Giornata {i} {'✅' if i in giornate_completate else ''}" for i in range(1, 39)]

# --- AREA ADMIN ---
with st.sidebar:
    st.subheader("⚙️ Area Amministratore")
    if not st.session_state.admin:
        pwd = st.text_input("Password", type="password")
        if st.button("Entra"):
            if pwd == "capeta63": 
                st.session_state.admin = True
                st.success("Accesso riuscito!")
                time.sleep(1)
                st.rerun()
            else: 
                st.error("Password errata")
    else:
        st.success("Accesso Effettuato")
        if st.button("Logout"): 
            st.session_state.admin = False
            st.rerun()
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Squadra", "⚽ Punti", "🎫 Schedina", "🗑️ Elimina"])
        
        try:
            # Squadre ordinate alfabeticamente anche nell'area admin
            squadre_list = sorted(supabase.table("squadre").select("*").execute().data or [], key=lambda x: x['nome_squadra'])
        except:
            squadre_list = []
        
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra")
                logo_file = st.file_uploader("Carica Logo Squadra", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("Salva"): 
                    if n:
                        logo_url = ""
                        if logo_file is not None:
                            try:
                                file_path = f"loghi/{datetime.now().timestamp()}_{logo_file.name}"
                                supabase.storage.from_(BUCKET_NAME).upload(
                                    path=file_path,
                                    file=logo_file.getvalue(),
                                    file_options={"content-type": logo_file.type, "upsert": "true"}
                                )
                                logo_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                            except Exception as e:
                                st.error(f"Errore caricamento logo: {e}")
                        
                        supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo_url}).execute()
                        st.success("Squadra salvata con successo!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.warning("Inserisci il nome della squadra.")
                    
        with tab2:
            st.write("### Inserisci Punti Giornata")
            if squadre_list:
                with st.form("add_p_multi"):
                    g_pts = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_pts_multi")
                    num_g_pts = int(g_pts.split()[1])
                    
                    punti_inseriti = {}
                    for s in squadre_list:
                        punti_inseriti[s['id']] = st.number_input(f"{s['nome_squadra']}", min_value=0, step=1, key=f"pts_{s['id']}")
                    
                    if st.form_submit_button("Salva Tutti i Punti"):
                        for s_id, p in punti_inseriti.items():
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0:
                                supabase.table("risultati").insert({
                                    "squadra_id": s_id, 
                                    "punteggio": p, 
                                    "giornata": num_g_pts
                                }).execute()
                        st.success("Punti aggiornati con successo!")
                        time.sleep(2)
                        st.rerun()
                
                st.markdown("---")
                st.write("### Azzera Punti Squadra")
                with st.form("reset_p_single"):
                    g_reset = st.selectbox("Giornata da azzerare", lista_giornate_etichette, index=giornata_idx, key="g_reset_pts")
                    num_g_reset = int(g_reset.split()[1])
                    sq_reset = st.selectbox("Squadra", [s['nome_squadra'] for s in squadre_list], key="sq_reset_pts")
                    
                    if st.form_submit_button("Azzera Punti Squadra"):
                        s_id_reset = next(s['id'] for s in squadre_list if s['nome_squadra'] == sq_reset)
                        supabase.table("risultati").delete().eq("squadra_id", s_id_reset).eq("giornata", num_g_reset).execute()
                        st.success(f"Punti azzerati per {sq_reset} nella Giornata {num_g_reset}!")
                        time.sleep(2)
                        st.rerun()
            else:
                st.info("Aggiungi prima almeno una squadra.")
                
        with tab3:
            st.write("### Carica Schedine")
            if squadre_list:
                with st.form("add_sch_multi"):
                    g = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_sch_multi")
                    num_g_sch = int(g.split()[1])
                    
                    schedine_file_inserite = {}
                    for s in squadre_list:
                        schedine_file_inserite[s['id']] = st.file_uploader(f"Schedina - {s['nome_squadra']}", type=["png", "jpg", "jpeg"], key=f"sch_file_{s['id']}")
                    
                    if st.form_submit_button("Carica Schedine"):
                        caricamenti_effettuati = 0
                        for s_id, file_obj in schedine_file_inserite.items():
                            if file_obj is not None:
                                try:
                                    file_path = f"schedine/g{num_g_sch}_{datetime.now().timestamp()}_{file_obj.name}"
                                    supabase.storage.from_(BUCKET_NAME).upload(
                                        path=file_path,
                                        file=file_obj.getvalue(),
                                        file_options={"content-type": file_obj.type, "upsert": "true"}
                                    )
                                    url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                                    
                                    supabase.table("schedine").delete().eq("squadra_id", s_id).eq("giornata", num_g_sch).execute()
                                    supabase.table("schedine").insert({
                                        "squadra_id": s_id, 
                                        "giornata": num_g_sch, 
                                        "schedina_url": url
                                    }).execute()
                                    caricamenti_effettuati += 1
                                except Exception as e:
                                    st.error(f"Errore caricamento schedina squadra ID {s_id}: {e}")
                        
                        if caricamenti_effettuati > 0:
                            st.success(f"Caricate {caricamenti_effettuati} schedine con successo!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.warning("Seleziona almeno un file prima di cliccare su Carica Schedine.")
            else:
                st.info("Aggiungi prima almeno una squadra.")
                    
        with tab4:
            st.write("### Elimina Schedina")
            g_del = st.selectbox("Giornata Schedina", lista_giornate_etichette, index=giornata_idx, key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            try:
                schedine_g = supabase.table("schedine").select("squadra_id").eq("giornata", num_g_del).execute().data
                squadre_con_schedina = [s for s in squadre_list if s['id'] in [sch['squadra_id'] for sch in schedine_g]] if squadre_list else []
            except:
                squadre_con_schedina = []
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    st.success("Schedina eliminata!")
                    time.sleep(2)
                    st.rerun()
            else:
                st.info("Nessuna schedina trovata in questa giornata.")
                
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
                    time.sleep(2)
                    st.rerun()
            else:
                st.info("Nessuna squadra presente.")

# --- MENU E LOGICA PAGINE ---
st.title("⚽ FantaBet Serie A")

g_corrente = get_giornata_corrente()
st.markdown(f"""
    <div class="alert-box">
        💡 <b>Promemoria:</b> Siamo attualmente vicini o nella <b>Giornata {g_corrente}</b>. Assicurati di caricare la tua schedina in tempo!
    </div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
if c1.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
if c2.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"
if c3.button("❄️ Coppa Inverno", use_container_width=True): st.session_state.current_page = "Coppa Inverno"
if c4.button("🌸 Coppa Primavera", use_container_width=True): st.session_state.current_page = "Coppa Primavera"

st.markdown("---")

try:
    # Carichiamo le squadre ordinate rigorosamente in ordine alfabetico
    squadre = sorted(supabase.table("squadre").select("*").execute().data or [], key=lambda x: x['nome_squadra'])
    risultati = supabase.table("risultati").select("*").execute().data or []
except Exception as e:
    squadre, risultati = [], []
    st.error(f"Errore di connessione al database: {e}")

def calcola_classifica(giornate_target=None):
    if not squadre: return []
    
    classifica_temp = []
    for s in squadre:
        res_squadra = [r for r in risultati if r['squadra_id'] == s['id']]
        if giornate_target:
            res_squadra = [r for r in res_squadra if r.get('giornata') is not None and giornate_target[0] <= int(r['giornata']) <= giornate_target[1]]
        
        punti_totali = sum(int(r['punteggio']) for r in res_squadra)
        dettaglio_giornate = {int(r['giornata']): int(r['punteggio']) for r in res_squadra if r.get('giornata') is not None}
        
        classifica_temp.append({
            'id': s['id'],
            'nome': s['nome_squadra'], 
            'punti': punti_totali, 
            'logo': s.get('logo_url'),
            'dettaglio': dettaglio_giornate
        })
    
    # Ordinamento per punti (decrescente) e in caso di parità per nome (alfabetico)
    return sorted(classifica_temp, key=lambda x: (-x['punti'], x['nome']))

if st.session_state.current_page in ["Classifica", "Coppa Inverno", "Coppa Primavera"]:
    is_coppa = st.session_state.current_page != "Classifica"
    target = None
    if st.session_state.current_page == "Coppa Inverno": target = (12, 17)
    elif st.session_state.current_page == "Coppa Primavera": target = (27, 32)
    
    if squadre:
        classifica = calcola_classifica(target)
        
        if st.session_state.admin and not is_coppa and classifica:
            df_export = pd.DataFrame([{'Squadra': item['nome'], 'Punti Totali': item['punti']} for item in classifica])
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Scarica Classifica in CSV",
                data=csv_data,
                file_name="classifica_fantabet.csv",
                mime="text/csv",
            )
        
        giornate_registrate_set = {r.get('giornata') for r in risultati}
        
        # Podio Finale Generale
        if not is_coppa and 38 in giornate_registrate_set and len(classifica) >= 3:
            st.markdown("<div class='winner-card'><h2>🏆 PODIO FINALE 🏆</h2></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            podio = [col2, col1, col3]
            for i in range(3):
                with podio[i]:
                    logo_p = f"<img src='{classifica[i]['logo']}' style='width:50px; height:50px; border-radius:50%; object-fit:cover; margin-bottom:5px;' /><br>" if classifica[i]['logo'] else ""
                    st.markdown(f"### {'🥇' if i==0 else '🥈' if i==1 else '🥉'} {classifica[i]['nome']}")
                    if classifica[i]['logo']:
                        st.markdown(logo_p, unsafe_allow_html=True)
                    st.write(f"**{classifica[i]['punti']} Punti**")
        
        # Podio Coppe
        if is_coppa:
            torneo_concluso = target[1] in giornate_registrate_set
            if torneo_concluso and classifica and classifica[0]['punti'] > 0:
                vincitore = classifica[0]
                logo_v = f"<img src='{vincitore['logo']}' style='width:80px; height:80px; border-radius:50%; object-fit:cover; border:3px solid #FFD700; margin-bottom:10px;' />" if vincitore['logo'] else "🏆"
                st.markdown(f"""<div class="winner-card">
                        <h2>🏆 Vincitore {st.session_state.current_page} 🏆</h2>
                        {logo_v}
                        <h1>🥇 {vincitore['nome']}</h1>
                        <p style="color:#4CAF50; font-weight:bold;">Con {vincitore['punti']} punti</p>
                        </div>""", unsafe_allow_html=True)
                st.balloons()

        for pos, item in enumerate(classifica, 1):
            c_class = "gold" if pos == 1 else "silver" if pos == 2 else "bronze" if pos == 3 else ""
            logo_html = f"<img src='{item['logo']}' style='width:30px; height:30px; border-radius:50%; object-fit:cover; margin-right:10px;' />" if item['logo'] else "⚽ "
            
            with st.container():
                st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                            <span style="font-weight:bold; width:35px;">{pos}°</span>
                            {logo_html}
                            <span style="flex-grow:1; margin-left:5px; font-weight:bold;">{item['nome']}</span>
                            <span style="font-weight:bold; color:#4CAF50;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
                
                # Espansore solo per la classifica generale
                if not is_coppa:
                    with st.expander(f"📊 Dettaglio Giornate - {item['nome']}"):
                        if item['dettaglio']:
                            df_dettaglio = pd.DataFrame(list(item['dettaglio'].items()), columns=['Giornata', 'Punti']).sort_values('Giornata')
                            st.dataframe(df_dettaglio.set_index('Giornata'), use_container_width=True)
                        else:
                            st.info("Nessun punteggio registrato per questa squadra.")
    else:
        st.info("Nessuna squadra inserita nel database.")

elif st.session_state.current_page == "Schedine":
    st.title("📅 Schedine Giornaliere")
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split(" ")[1])
    
    try:
        schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        
        if squadre:
            for s in squadre:
                logo_html = f"<img src='{s.get('logo_url')}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:10px;' />" if s.get('logo_url') else "⚽ "
                st.markdown(f"<div style='display:flex; align-items:center; margin-top:15px;'>{logo_html} <h3>{s['nome_squadra']}</h3></div>", unsafe_allow_html=True)
                url = schedine_dict.get(s['id'])
                if url: 
                    # Schedina ridotta a 300px + link per aprirla a schermo intero
                    st.image(url, width=300)
                    st.markdown(f"[🔗 Apri a schermo intero]({url})")
                else: 
                    st.caption("Nessuna schedina caricata per questa squadra.")
                st.markdown("---")
    except Exception as e:
        st.error(f"Errore nel caricamento delle schedine: {e}")
