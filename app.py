import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time
from generatore import crea_immagine_schedina

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "fantabet"

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A", page_icon="⚽", layout="wide")

# 3. Stile CSS Ottimizzato (Dark Mode Forzata)
st.markdown("""
    <style>
    :root {
        --background-color: #0E1117;
        --secondary-background-color: #262730;
        --text-color: #FAFAFA;
    }
    .stApp { 
        background-color: #0E1117 !important;
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); 
        background-size: cover; 
        background-attachment: fixed; 
    }
    h1, h2, h3, h5, p, span { color: #FAFAFA !important; text-shadow: 2px 2px 4px #000; }
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

# Funzioni di caricamento dati
@st.cache_data(ttl=60)
def carica_dati_db():
    try:
        sq = sorted(supabase.table("squadre").select("*").execute().data or [], key=lambda x: x['nome_squadra'])
        res = supabase.table("risultati").select("*").execute().data or []
        return sq, res
    except Exception as e:
        return [], []

squadre, risultati = carica_dati_db()

try:
    risultati_globali = supabase.table("risultati").select("giornata").execute().data or []
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
            if pwd == st.secrets["ADMIN_PASSWORD"]: 
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
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Squadra", "📅 Partite", "⚽ Punti", "🎫 Schedine", "🗑️ Elimina"])
        
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
                                    path=file_path, file=logo_file.getvalue(),
                                    file_options={"content-type": logo_file.type, "upsert": "true"}
                                )
                                logo_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                            except Exception as e:
                                st.error(f"Errore caricamento logo: {e}")
                        
                        supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo_url}).execute()
                        st.success("Squadra salvata!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.warning("Inserisci il nome della squadra.")

        with tab2:
            st.write("### Imposta Partite Giornata")
            with st.form("form_partite"):
                g_part = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_part_sel")
                num_g_part = int(g_part.split()[1])
                
                p1 = st.text_input("Partita 1 (es. Inter - Milan)")
                p2 = st.text_input("Partita 2 (es. Juventus - Napoli)")
                p3 = st.text_input("Partita 3 (es. Roma - Lazio)")
                
                if st.form_submit_button("Salva Partite"):
                    supabase.table("partite_giornata").delete().eq("giornata", num_g_part).execute()
                    partite_inserite = [p1, p2, p3]
                    for p in partite_inserite:
                        if p.strip():
                            supabase.table("partite_giornata").insert({"giornata": num_g_part, "partita": p.strip()}).execute()
                    st.success("Partite salvate con successo!")
                    time.sleep(1.5)
                    st.rerun()

        with tab3:
            st.write("### Inserisci Punti Giornata")
            if squadre:
                with st.form("add_p_multi"):
                    g_pts = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_pts_multi")
                    num_g_pts = int(g_pts.split()[1])
                    
                    punti_inseriti = {s['id']: st.number_input(f"{s['nome_squadra']}", min_value=0, step=1, key=f"pts_{s['id']}") for s in squadre}
                    
                    if st.form_submit_button("Salva Tutti i Punti"):
                        for s_id, p in punti_inseriti.items():
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0:
                                supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_pts}).execute()
                        st.success("Punti aggiornati!")
                        time.sleep(1.5)
                        st.rerun()
            else:
                st.info("Aggiungi prima almeno una squadra.")
                
        with tab4:
            st.write("### Genera Schedina Automatica")
            if squadre:
                g_sch_auto = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_sch_auto")
                num_g_sch = int(g_sch_auto.split()[1])
                
                res_partite = supabase.table("partite_giornata").select("partita").eq("giornata", num_g_sch).execute().data
                partite_giornata = [item['partita'] for item in res_partite] if res_partite else []
                
                if partite_giornata:
                    sq_scelta_sch = st.selectbox("Seleziona Squadra", [s['nome_squadra'] for s in squadre], key="sq_sch_auto")
                    s_id_scelta = next(s['id'] for s in squadre if s['nome_squadra'] == sq_scelta_sch)
                    
                    with st.form("form_genera_schedina"):
                        pronostici_correnti = {}
                        for p in partite_giornata:
                            pronostici_correnti[p] = st.selectbox(f"Pronostico per: {p}", ["1", "X", "2"], key=f"pron_{p}")
                        
                        if st.form_submit_button("Crea e Carica Schedina"):
                            img_bytes = crea_immagine_schedina(sq_scelta_sch, num_g_sch, pronostici_correnti)
                            
                            file_path = f"schedine/g{num_g_sch}_{s_id_scelta}_{datetime.now().timestamp()}.png"
                            supabase.storage.from_(BUCKET_NAME).upload(
                                path=file_path, file=img_bytes,
                                file_options={"content-type": "image/png", "upsert": "true"}
                            )
                            url_img = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                            
                            supabase.table("schedine").delete().eq("squadra_id", s_id_scelta).eq("giornata", num_g_sch).execute()
                            supabase.table("schedine").insert({
                                "squadra_id": s_id_scelta,
                                "giornata": num_g_sch,
                                "schedina_url": url_img,
                                "pronostici_json": pronostici_correnti
                            }).execute()
                            
                            st.success("Schedina generata e salvata con successo!")
                            time.sleep(1.5)
                            st.rerun()
                else:
                    st.warning("Prima inserisci le partite per questa giornata nella tab 'Partite'!")
            else:
                st.info("Aggiungi prima almeno una squadra.")
                    
        with tab5:
            st.write("### Elimina Schedina o Squadra")
            g_del = st.selectbox("Giornata Schedina", lista_giornate_etichette, index=giornata_idx, key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            try:
                schedine_g = supabase.table("schedine").select("squadra_id").eq("giornata", num_g_del).execute().data or []
                squadre_con_schedina = [s for s in squadre if s['id'] in [sch['squadra_id'] for sch in schedine_g]]
            except:
                squadre_con_schedina = []
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina Selezionata"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    st.success("Schedina eliminata!")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.info("Nessuna schedina trovata in questa giornata.")
                
            st.markdown("---")
            st.write("### Elimina Squadra (Totale)")
            if squadre:
                sq_del = st.selectbox("Squadra da rimuovere", [s['nome_squadra'] for s in squadre], key="sq_del_tot")
                if st.button("Elimina Squadra e Dati"):
                    s_id = next(s['id'] for s in squadre if s['nome_squadra'] == sq_del)
                    supabase.table("squadre").delete().eq("id", s_id).execute()
                    supabase.table("risultati").delete().eq("squadra_id", s_id).execute()
                    supabase.table("schedine").delete().eq("squadra_id", s_id).execute()
                    st.success("Squadra eliminata con successo!")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.info("Nessuna squadra presente.")

# --- MENU E LOGICA PAGINE ---
st.title("⚽ FantaBet Serie A")

g_corrente = get_giornata_corrente()
st.markdown(f"""
    <div class="alert-box">
        💡 <b>Promemoria:</b> Siamo attualmente alla <b>Giornata {g_corrente}</b>. Carica la tua schedina in tempo!
    </div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
if c1.button("🏆 Classifica", use_container_width=True): st.session_state.current_page = "Classifica"
if c2.button("📅 Schedine", use_container_width=True): st.session_state.current_page = "Schedine"
if c3.button("❄️ Coppa Inverno", use_container_width=True): st.session_state.current_page = "Coppa Inverno"
if c4.button("🌸 Coppa Primavera", use_container_width=True): st.session_state.current_page = "Coppa Primavera"

st.markdown("---")

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
            'id': s['id'], 'nome': s['nome_squadra'], 'punti': punti_totali, 
            'logo': s.get('logo_url'), 'dettaglio': dettaglio_giornate
        })
    return sorted(classifica_temp, key=lambda x: (-x['punti'], x['nome']))

if st.session_state.current_page in ["Classifica", "Coppa Inverno", "Coppa Primavera"]:
    is_coppa = st.session_state.current_page != "Classifica"
    target = (12, 17) if st.session_state.current_page == "Coppa Inverno" else (27, 32) if st.session_state.current_page == "Coppa Primavera" else None
    
    if squadre:
        classifica = calcola_classifica(target)
        
        if st.session_state.admin and not is_coppa and classifica:
            df_export = pd.DataFrame([{'Squadra': item['nome'], 'Punti Totali': item['punti']} for item in classifica])
            st.download_button("📥 Scarica Classifica in CSV", df_export.to_csv(index=False).encode('utf-8'), "classifica_fantabet.csv", "text/csv")
        
        giornate_registrate_set = {r.get('giornata') for r in risultati}
        
        if not is_coppa and 38 in giornate_registrate_set and len(classifica) >= 3:
            st.markdown("<div class='winner-card'><h2>🏆 PODIO FINALE 🏆</h2></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            for i, col in enumerate([col2, col1, col3]):
                with col:
                    logo_p = f"<img src='{classifica[i]['logo']}' style='width:50px; height:50px; border-radius:50%; object-fit:cover; margin-bottom:5px;' /><br>" if classifica[i]['logo'] else ""
                    st.markdown(f"### {'🥇' if i==0 else '🥈' if i==1 else '🥉'} {classifica[i]['nome']}")
                    if classifica[i]['logo']: st.markdown(logo_p, unsafe_allow_html=True)
                    st.write(f"**{classifica[i]['punti']} Punti**")
        
        if is_coppa:
            if target[1] in giornate_registrate_set and classifica and classifica[0]['punti'] > 0:
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
            
            st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:35px;">{pos}°</span>
                        {logo_html}
                        <span style="flex-grow:1; margin-left:5px; font-weight:bold;">{item['nome']}</span>
                        <span style="font-weight:bold; color:#4CAF50;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
            
            if not is_coppa:
                with st.expander(f"📊 Dettaglio Giornate - {item['nome']}"):
                    if item['dettaglio']:
                        df_dettaglio = pd.DataFrame(list(item['dettaglio'].items()), columns=['Giornata', 'Punti']).sort_values('Giornata')
                        st.dataframe(df_dettaglio.set_index('Giornata'), use_container_width=True)
                    else:
                        st.info("Nessun punteggio registrato.")
    else:
        st.info("Nessuna squadra inserita nel database.")

elif st.session_state.current_page == "Schedine":
    st.title("📅 Schedine Giornaliere")
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split(" ")[1])
    
    try:
        schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        
        if squadre:
            for s in squadre:
                logo_html = f"<img src='{s.get('logo_url')}' style='width:35px; height:35px; border-radius:50%; object-fit:cover; margin-right:10px;' />" if s.get('logo_url') else "⚽ "
                st.markdown(f"<div style='display:flex; align-items:center; margin-top:15px;'>{logo_html} <h3>{s['nome_squadra']}</h3></div>", unsafe_allow_html=True)
                url = schedine_dict.get(s['id'])
                if url: 
                    st.image(url, width=300)
                    st.markdown(f"[🔗 Apri a schermo intero]({url})")
                else: 
                    st.caption("Nessuna schedina caricata.")
                st.markdown("---")
    except Exception as e:
        st.error(f"Errore nel caricamento delle schedine: {e}")
