import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time

# Prova a importare la logica del bot se presente
try:
    from bot_logica import calcola_risultati_da_foto_o_dati
except ImportError:
    def calcola_risultati_da_foto_o_dati(giornata, supabase_client):
        return False, "Modulo bot_logica.py non trovato."

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "fantabet"

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A Pro", page_icon="⚽", layout="wide")

# 3. Stile CSS di Livello Superiore (Dark Mode & UI Moderna)
st.markdown("""
    <style>
    :root {
        --background-color: #0E1117;
        --secondary-background-color: #1F242D;
        --text-color: #FAFAFA;
    }
    .stApp { 
        background-color: #0E1117 !important;
        background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); 
        background-size: cover; 
        background-attachment: fixed; 
    }
    h1, h2, h3, h5, p, span { color: #FAFAFA !important; text-shadow: 2px 2px 4px #000; }
    .card { background: rgba(30,30,30,0.85); padding: 16px; border-radius: 14px; margin-bottom: 12px; border-left: 5px solid #4CAF50; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.2s; }
    .card:hover { transform: scale(1.01); }
    .gold { border-left: 5px solid #FFD700 !important; background: rgba(255, 215, 0, 0.12) !important; }
    .silver { border-left: 5px solid #C0C0C0 !important; background: rgba(192, 192, 192, 0.1) !important; }
    .bronze { border-left: 5px solid #CD7F32 !important; background: rgba(205, 127, 50, 0.1) !important; }
    .winner-card { background: rgba(20, 20, 20, 0.95); border: 2px solid #FFD700; padding: 30px; border-radius: 20px; text-align: center; margin: 25px 0; box-shadow: 0 0 25px rgba(255, 215, 0, 0.5); }
    .alert-box { background: rgba(33, 150, 243, 0.15); border-left: 5px solid #2196F3; padding: 14px; border-radius: 10px; margin-bottom: 25px; color: #fff; backdrop-filter: blur(5px); }
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

# Funzioni di caricamento dati con caching ottimizzato
@st.cache_data(ttl=30)
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
    st.subheader("⚙️ Area Amministratore Pro")
    if not st.session_state.admin:
        pwd = st.text_input("Password Admin", type="password")
        if st.button("Autenticati"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin123"): 
                st.session_state.admin = True
                st.success("Accesso consentito!")
                time.sleep(0.8)
                st.rerun()
            else: 
                st.error("Password errata")
    else:
        st.success("Sessione Admin Attiva")
        if st.button("Disconnetti"): 
            st.session_state.admin = False
            st.rerun()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Squadra", "🤖 Bot API", "🎫 Schedina", "⚽ Punti", "🗑️ Elimina"])
        
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra")
                logo_file = st.file_uploader("Logo Ufficiale", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("Registra Squadra"): 
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
                        st.success("Squadra salvata con successo!")
                        time.sleep(1.2)
                        st.rerun()
                    else:
                        st.warning("Inserisci il nome della squadra.")

        with tab2:
            st.write("### Controllo Automatico Bot")
            st.caption("Verifica i risultati reali tramite API e calcola i punteggi delle schedine salvate.")
            g_auto = st.selectbox("Giornata da Verificare", lista_giornate_etichette, index=giornata_idx, key="g_auto_api")
            num_g_auto = int(g_auto.split()[1])
            
            if st.button("Avvia Bot e Aggiorna"):
                with st.spinner("Elaborazione risultati in corso..."):
                    successo, messaggio = calcola_risultati_da_foto_o_dati(num_g_auto, supabase)
                    if successo:
                        st.success(messaggio)
                        time.sleep(1.2)
                        st.rerun()
                    else:
                        st.error(messaggio)

        with tab3:
            st.write("### 🎫 Carica Foto Schedina")
            st.caption("Carica lo screenshot da Milleniumbet e imposta i pronostici associati.")
            if squadre:
                g_sch = st.selectbox("Giornata Schedina", lista_giornate_etichette, index=giornata_idx, key="g_sch_foto")
                num_g_sch = int(g_sch.split()[1])
                
                sq_scelta_sch = st.selectbox("Seleziona Squadra", [s['nome_squadra'] for s in squadre], key="sq_sch_foto")
                s_id_scelta = next(s['id'] for s in squadre if s['nome_squadra'] == sq_scelta_sch)
                
                file_foto = st.file_uploader("Screenshot Schedina", type=["png", "jpg", "jpeg"], key="file_foto_sch")
                
                st.write("Pronostici chiave della giornata:")
                col_p1, col_p2 = st.columns(2)
                p1 = col_p1.selectbox("Inter - Milan", ["1", "X", "2"], key="p_im")
                p2 = col_p2.selectbox("Juventus - Napoli", ["1", "X", "2"], key="p_jn")
                
                if st.button("Salva Schedina e Pronostici"):
                    if file_foto is not None:
                        try:
                            file_path = f"schedine/g{num_g_sch}_{s_id_scelta}_{datetime.now().timestamp()}.png"
                            supabase.storage.from_(BUCKET_NAME).upload(
                                path=file_path, file=file_foto.getvalue(),
                                file_options={"content-type": file_foto.type, "upsert": "true"}
                            )
                            url_img = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                            
                            pronostici_dict = {
                                "Inter - Milan": p1,
                                "Juventus - Napoli": p2
                            }
                            
                            supabase.table("schedine").delete().eq("squadra_id", s_id_scelta).eq("giornata", num_g_sch).execute()
                            supabase.table("schedine").insert({
                                "squadra_id": s_id_scelta,
                                "giornata": num_g_sch,
                                "schedina_url": url_img,
                                "pronostici_json": pronostici_dict
                            }).execute()
                            
                            st.success("Schedina archiviata con successo!")
                            time.sleep(1.2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore di salvataggio: {e}")
                    else:
                        st.warning("Carica prima l'immagine della schedina.")
            else:
                st.info("Nessuna squadra disponibile.")
                    
        with tab4:
            st.write("### Inserisci Punti Manuali")
            if squadre:
                with st.form("add_p_multi"):
                    g_pts = st.selectbox("Giornata Punti", lista_giornate_etichette, index=giornata_idx, key="g_pts_multi")
                    num_g_pts = int(g_pts.split()[1])
                    
                    punti_inseriti = {s['id']: st.number_input(f"{s['nome_squadra']}", min_value=0, step=1, key=f"pts_{s['id']}") for s in squadre}
                    
                    if st.form_submit_button("Aggiorna Punti"):
                        for s_id, p in punti_inseriti.items():
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0:
                                supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_pts}).execute()
                        st.success("Punti salvati!")
                        time.sleep(1.2)
                        st.rerun()
            else:
                st.info("Inserisci prima le squadre.")
                
        with tab5:
            st.write("### Gestione ed Eliminazione")
            g_del = st.selectbox("Giornata", lista_giornate_etichette, index=giornata_idx, key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            try:
                schedine_g = supabase.table("schedine").select("squadra_id").eq("giornata", num_g_del).execute().data or []
                squadre_con_schedina = [s for s in squadre if s['id'] in [sch['squadra_id'] for sch in schedine_g]]
            except:
                squadre_con_schedina = []
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    st.success("Schedina rimossa!")
                    time.sleep(1.2)
                    st.rerun()
            else:
                st.info("Nessuna schedina presente per questa giornata.")
                
            st.markdown("---")
            if squadre:
                sq_del = st.selectbox("Elimina Squadra Definitivamente", [s['nome_squadra'] for s in squadre], key="sq_del_tot")
                if st.button("Rimuovi Squadra e Dati"):
                    s_id = next(s['id'] for s in squadre if s['nome_squadra'] == sq_del)
                    supabase.table("squadre").delete().eq("id", s_id).execute()
                    supabase.table("risultati").delete().eq("squadra_id", s_id).execute()
                    supabase.table("schedine").delete().eq("squadra_id", s_id).execute()
                    st.success("Squadra eliminata correttamente!")
                    time.sleep(1.2)
                    st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("⚽ FantaBet Serie A Pro")

g_corrente = get_giornata_corrente()
st.markdown(f"""
    <div class="alert-box">
        💡 <b>Info Lega:</b> Giornata corrente stimata: <b>Giornata {g_corrente}</b>. Verifica i pronostici e segui l'andamento in tempo reale.
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
            st.download_button("📥 Esporta Classifica CSV", df_export.to_csv(index=False).encode('utf-8'), "classifica_fantabet.csv", "text/csv")
        
        giornate_registrate_set = {r.get('giornata') for r in risultati}
        
        # Podio Campionato (38 giornate)
        if not is_coppa and 38 in giornate_registrate_set and len(classifica) >= 3:
            st.markdown("<div class='winner-card'><h2>🏆 PODIO FINALE CAMPIONATO 🏆</h2></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            for i, col in enumerate([col2, col1, col3]):
                with col:
                    logo_p = f"<img src='{classifica[i]['logo']}' style='width:65px; height:65px; border-radius:50%; object-fit:cover; margin-bottom:8px; border:2px solid #FFD700;' /><br>" if classifica[i]['logo'] else ""
                    st.markdown(f"### {'🥇' if i==0 else '🥈' if i==1 else '🥉'} {classifica[i]['nome']}")
                    if classifica[i]['logo']: st.markdown(logo_p, unsafe_allow_html=True)
                    st.write(f"**{classifica[i]['punti']} Punti**")
        
        # Vincitore Unico per le Coppe (Inverno: fine giornata 17, Primavera: fine giornata 32)
        if is_coppa:
            fine_coppa = 17 if st.session_state.current_page == "Coppa Inverno" else 32
            if fine_coppa in giornate_registrate_set and classifica and classifica[0]['punti'] > 0:
                vincitore = classifica[0]
                logo_v = f"<img src='{vincitore['logo']}' style='width:100px; height:100px; border-radius:50%; object-fit:cover; border:3px solid #FFD700; margin-bottom:12px; box-shadow: 0 0 15px rgba(255,215,0,0.5);' />" if vincitore['logo'] else "🏆"
                st.markdown(f"""<div class="winner-card">
                        <h2 style="color:#FFD700; letter-spacing: 1px;">🏆 TRIONFO {st.session_state.current_page.upper()} 🏆</h2>
                        {logo_v}
                        <h1 style="color:#FFF; margin-top:5px; font-size:2.2em;">🥇 {vincitore['nome']}</h1>
                        <p style="color:#4CAF50; font-weight:bold; font-size:1.2em;">Campione con {vincitore['punti']} punti</p>
                        </div>""", unsafe_allow_html=True)
                st.balloons()

        for pos, item in enumerate(classifica, 1):
            if is_coppa:
                c_class = "gold" if pos == 1 else ""
                badge_pos = "🥇" if pos == 1 else f"{pos}°"
            else:
                c_class = "gold" if pos == 1 else "silver" if pos == 2 else "bronze" if pos == 3 else ""
                badge_pos = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"{pos}°"

            logo_html = f"<img src='{item['logo']}' style='width:32px; height:32px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽ "
            
            st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:38px; font-size:1.1em;">{badge_pos}</span>
                        {logo_html}
                        <span style="flex-grow:1; margin-left:5px; font-weight:bold; font-size:1.1em;">{item['nome']}</span>
                        <span style="font-weight:bold; color:#4CAF50; font-size:1.1em;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
            
            if not is_coppa:
                with st.expander(f"📊 Dettaglio Giornate - {item['nome']}"):
                    if item['dettaglio']:
                        df_dettaglio = pd.DataFrame(list(item['dettaglio'].items()), columns=['Giornata', 'Punti']).sort_values('Giornata')
                        st.dataframe(df_dettaglio.set_index('Giornata'), use_container_width=True)
                    else:
                        st.info("Nessun punteggio registrato per questa squadra.")
    else:
        st.info("Nessuna squadra configurata nel database. Accedi all'Area Admin per aggiungerne.")

elif st.session_state.current_page == "Schedine":
    st.title("📅 Archivio Schedine")
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split(" ")[1])
    
    try:
        schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        
        if squadre:
            for s in squadre:
                logo_html = f"<img src='{s.get('logo_url')}' style='width:40px; height:40px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if s.get('logo_url') else "⚽ "
                st.markdown(f"<div style='display:flex; align-items:center; margin-top:20px;'>{logo_html} <h2>{s['nome_squadra']}</h2></div>", unsafe_allow_html=True)
                url = schedine_dict.get(s['id'])
                if url: 
                    st.image(url, width=320)
                    st.markdown(f"[🔗 Apri Immagine a Schermo Intero]({url})")
                else: 
                    st.caption("Nessuna schedina caricata per questa giornata.")
                st.markdown("---")
    except Exception as e:
        st.error(f"Errore nel recupero delle schedine: {e}")
