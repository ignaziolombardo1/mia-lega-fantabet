import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time
import os
import json
import google.generativeai as genai

# =========================================================
# CONFIGURAZIONE INIZIALE E CREDENZIALI (SICURA)
# =========================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Configurazione di Google Gemini
genai.configure(api_key=GEMINI_API_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "fantabet"

st.set_page_config(page_title="FantaBet Serie A Pro", page_icon="⚽", layout="wide")

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
    .schedina-box { background: rgba(25, 25, 30, 0.9); padding: 15px; border-radius: 10px; border: 1px solid #444; margin-bottom: 15px; }
    .grid-card { background: rgba(25, 25, 30, 0.85); padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    
    .splash-screen {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #0E1117;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 99999;
        animation: fadeOut 0.6s ease-in-out 1.5s forwards;
        pointer-events: none;
    }
    @keyframes fadeOut {
        to { opacity: 0; visibility: hidden; }
    }
    .pulse-logo {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #4CAF50;
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(76, 175, 80, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# GESTIONE SPLASH SCREEN CON LOGO PULSANTE
# =========================================================

if "splash_mostrato" not in st.session_state:
    st.session_state.splash_mostrato = True
    logo_splash_url = "https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/6e1768a34a416322ca5542717fd47fbf313a10d0/IMG_3743.jpeg"
    
    st.markdown(f"""
        <div class="splash-screen">
            <img src="{logo_splash_url}" class="pulse-logo" />
            <h2 style="color: #FAFAFA; margin-top: 20px; font-family: sans-serif;">FantaBet Serie A Pro</h2>
            <p style="color: #888; font-size: 0.9em;">Caricamento in corso...</p>
        </div>
    """, unsafe_allow_html=True)

# =========================================================
# FUNZIONI DI SUPPORTO E BOT IA (GEMINI AGGIORNATO)
# =========================================================

def get_giornata_corrente():
    oggi = datetime.now().date()
    inizio = datetime(2026, 8, 23).date()
    return max(1, min(38, ((oggi - inizio).days // 7) + 1)) if oggi >= inizio else 1

giornata_idx = get_giornata_corrente() - 1

if "current_page" not in st.session_state:
    st.session_state.current_page = "Classifica"

if "admin" not in st.session_state:
    st.session_state.admin = False

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
except Exception:
    giornate_completate = set()

lista_giornate_etichette = [f"Giornata {i} {'✅' if i in giornate_completate else ''}" for i in range(1, 39)]

def analizza_schedine_ia(giornata, supabase_client):
    try:
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}. Carica prima le foto.", {}
            
        model = genai.GenerativeModel('gemini-3.6-flash')
        report = []
        dati_punti_esatti = {}

        for s in schedine:
            schedina_url = s.get('schedina_url')
            if not schedina_url:
                continue
            
            sq_obj = next((sq for sq in squadre if sq['id'] == s['squadra_id']), None)
            nome_squadra = sq_obj['nome_squadra'] if sq_obj else f"Squadra ID {s['squadra_id']}"
            
            try:
                import urllib.request
                req = urllib.request.urlopen(schedina_url)
                image_bytes = req.read()
                
                image_parts = [{
                    'mime_type': 'image/jpeg',
                    'data': image_bytes
                }]

                prompt_testo = f"""Analizza questa schedina della Giornata {giornata} di Serie A. 
                Prendi in considerazione un massimo di 10 partite presenti nella schedina.
                Valuta in autonomia i risultati reali di quelle partite e calcola i punti totali fatti da questa squadra.
                Restituisci la risposta ESCLUSIVAMENTE in formato JSON con questa struttura esatta:
                {{
                    "punteggio_totale": 5
                }}"""
                
                response = model.generate_content([image_parts[0], prompt_testo])
                testo_risposta = response.text.strip()
                
                if testo_risposta.startswith("```json"):
                    testo_risposta = testo_risposta[7:]
                if testo_risposta.endswith("```"):
                    testo_risposta = testo_risposta[:-3]
                
                risposta_json = json.loads(testo_risposta.strip())
                punti = int(risposta_json.get("punteggio_totale", 0))
                
                dati_punti_esatti[s['squadra_id']] = punti
                report.append(f"Squadra: {nome_squadra} | Punti calcolati: {punti}")
                
            except Exception as ex:
                report.append(f"Squadra: {nome_squadra} | Errore IA ({str(ex)})")
                continue
        
        return True, "\n".join(report), dati_punti_esatti
        
    except Exception as e:
        return False, f"Errore generale nel bot: {str(e)}", {}

# =========================================================
# BARRA LATERALE ADMIN
# =========================================================

with st.sidebar:
    st.subheader("⚙️ Area Amministratore Pro")
    if not st.session_state.admin:
        pwd = st.text_input("Password Admin", type="password")
        if st.button("Autenticati"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "admin123"): 
                st.session_state.admin = True
                st.toast("Accesso effettuato con successo!", icon="🔓")
                time.sleep(0.6)
                st.rerun()
            else: 
                st.error("Password errata")
    else:
        st.success("Sessione Admin Attiva")
        if st.button("Disconnetti"): 
            st.session_state.admin = False
            st.rerun()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Squadra", "🤖 Bot IA", "🎫 Schedine", "⚽ Punti", "🗑️ Elimina"])
        
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
                        st.toast("Squadra registrata correttamente!", icon="⚽")
                        time.sleep(1.0)
                        st.rerun()
                    else:
                        st.warning("Inserisci il nome della squadra.")

        with tab2:
            st.write("### 🤖 Bot Valutazione Schedine (Max 10 Partite)")
            st.caption("Il bot analizza le schedine, calcola i punti in autonomia e ti permette di caricarli con un click.")
            g_auto = st.selectbox("Giornata da Valutare", lista_giornate_etichette, index=giornata_idx, key="g_auto_api")
            num_g_auto = int(g_auto.split()[1])
            
            if st.button("🚀 Avvia Analisi IA e Calcola Punti"):
                with st.spinner("Il bot sta analizzando le schedine..."):
                    successo, messaggio, risultati_bot = analizza_schedine_ia(num_g_auto, supabase)
                    if successo:
                        st.success("Analisi completata!")
                        st.text_area("Risultato del Bot:", value=messaggio, height=180)
                        st.session_state["temp_risultati_bot"] = risultati_bot
                        st.session_state["temp_giornata_bot"] = num_g_auto
                    else:
                        st.error(messaggio)
            
            if "temp_risultati_bot" in st.session_state and st.session_state["temp_risultati_bot"]:
                st.markdown("---")
                if st.button("📥 Inserisci nella classifica", type="primary"):
                    g_target = st.session_state["temp_giornata_bot"]
                    for s_id, pt in st.session_state["temp_risultati_bot"].items():
                        supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", g_target).execute()
                        supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": pt, "giornata": g_target}).execute()
                    
                    st.toast("Punti inseriti con successo nella classifica!", icon="🎉")
                    del st.session_state["temp_risultati_bot"]
                    time.sleep(1.2)
                    st.rerun()

        with tab3:
            st.write("### 🎫 Carica Schedine in Blocco")
            if squadre:
                squadre_ordinate_admin = sorted(squadre, key=lambda x: x['nome_squadra'])
                g_sch = st.selectbox("Seleziona Giornata di Riferimento", lista_giornate_etichette, index=giornata_idx, key="g_sch_foto_multi")
                num_g_sch = int(g_sch.split()[1])
                
                st.markdown("---")
                dati_caricamento = {}
                for s in squadre_ordinate_admin:
                    st.markdown(f"<div class='schedina-box'><b>⚽ {s['nome_squadra']}</b>", unsafe_allow_html=True)
                    f_foto = st.file_uploader(f"Screenshot Schedina - {s['nome_squadra']}", type=["png", "jpg", "jpeg"], key=f"foto_{s['id']}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    dati_caricamento[s['id']] = f_foto
                
                if st.button("💾 Salva Tutte le Schedine Caricate", type="primary"):
                    with st.spinner("Caricamento in corso su Supabase..."):
                        caricate = 0
                        for s_id, file_foto in dati_caricamento.items():
                            if file_foto is not None:
                                try:
                                    file_path = f"schedine/g{num_g_sch}_{s_id}_{datetime.now().timestamp()}.png"
                                    supabase.storage.from_(BUCKET_NAME).upload(
                                        path=file_path, file=file_foto.getvalue(),
                                        file_options={"content-type": file_foto.type, "upsert": "true"}
                                    )
                                    url_img = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                                    
                                    supabase.table("schedine").delete().eq("squadra_id", s_id).eq("giornata", num_g_sch).execute()
                                    supabase.table("schedine").insert({
                                        "squadra_id": s_id,
                                        "giornata": num_g_sch,
                                        "schedina_url": url_img,
                                        "pronostici_json": {}
                                    }).execute()
                                    caricate += 1
                                except Exception as e:
                                    st.error(f"Errore per la squadra ID {s_id}: {e}")
                        
                        if caricate > 0:
                            st.toast(f"Salvate con successo {caricate} schedine!", icon="🎉")
                            time.sleep(1.2)
                            st.rerun()
                        else:
                            st.warning("Nessuna foto caricata.")
            else:
                st.info("Nessuna squadra disponibile.")
                
        with tab4:
            st.write("### Inserisci o Modifica Punti")
            if squadre:
                squadre_ordinate_admin = sorted(squadre, key=lambda x: x['nome_squadra'])
                with st.form("add_p_multi"):
                    g_pts = st.selectbox("Giornata Punti", lista_giornate_etichette, index=giornata_idx, key="g_pts_multi")
                    num_g_pts = int(g_pts.split()[1])
                    punti_inseriti = {s['id']: st.number_input(f"{s['nome_squadra']}", min_value=0, step=1, key=f"pts_{s['id']}") for s in squadre_ordinate_admin}
                    
                    col_form1, col_form2 = st.columns(2)
                    salva_punti = col_form1.form_submit_button("Aggiorna Punti")
                    azzera_giornata = col_form2.form_submit_button("🗑️ Azzera Giornata")
                    
                    if salva_punti:
                        for s_id, p in punti_inseriti.items():
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0:
                                supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_pts}).execute()
                        st.toast("Punti aggiornati con successo!", icon="✅")
                        time.sleep(1.0)
                        st.rerun()
                        
                    if azzera_giornata:
                        supabase.table("risultati").delete().eq("giornata", num_g_pts).execute()
                        st.toast(f"Punti della Giornata {num_g_pts} azzerati!", icon="⚠️")
                        time.sleep(1.0)
                        st.rerun()
            else:
                st.info("Inserisci prima le squadre.")
                
        with tab5:
            st.write("### Gestione ed Eliminazione")
            g_del = st.selectbox("Giornata", lista_giornate_etichette, index=giornata_idx, key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            try:
                schedine_g = supabase.table("schedine").select("squadra_id").eq("giornata", num_g_del).execute().data or []
                squadre_con_schedina = sorted([s for s in squadre if s['id'] in [sch['squadra_id'] for sch in schedine_g]], key=lambda x: x['nome_squadra'])
            except Exception:
                squadre_con_schedina = []
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    st.toast("Schedina rimossa correttamente.", icon="🗑️")
                    time.sleep(1.0)
                    st.rerun()
            else:
                st.info("Nessuna schedina presente.")
                
            st.markdown("---")
            if squadre:
                squadre_ordinate_admin = sorted(squadre, key=lambda x: x['nome_squadra'])
                sq_del = st.selectbox("Elimina Squadra Definitivamente", [s['nome_squadra'] for s in squadre_ordinate_admin], key="sq_del_tot")
                if st.button("Rimuovi Squadra e Dati"):
                    s_id = next(s['id'] for s in squadre if s['nome_squadra'] == sq_del)
                    supabase.table("squadre").delete().eq("id", s_id).execute()
                    supabase.table("risultati").delete().eq("squadra_id", s_id).execute()
                    supabase.table("schedine").delete().eq("squadra_id", s_id).execute()
                    st.toast("Squadra e dati eliminati.", icon="⚠️")
                    time.sleep(1.0)
                    st.rerun()

# =========================================================
# INTERFACCIA PRINCIPALE
# =========================================================

st.title("⚽ FantaBet Serie A Pro")

g_corrente = get_giornata_corrente()
st.markdown(f"""
    <div class="alert-box">
        💡 <b>Info Lega:</b> Giornata corrente stimata: <b>Giornata {g_corrente}</b>. Verifica i pronostici e segui l'andamento in tempo reale.
    </div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
if c1.button("🏆 Classifica", use_container_width=True): 
    st.session_state.current_page = "Classifica"
if c2.button("📅 Schedine", use_container_width=True): 
    st.session_state.current_page = "Schedine"
if c3.button("❄️ Coppa Inverno", use_container_width=True): 
    st.session_state.current_page = "Coppa Inverno"
if c4.button("🌸 Coppa Primavera", use_container_width=True): 
    st.session_state.current_page = "Coppa Primavera"

st.markdown("---")

def calcola_classifica(giornate_target=None):
    if not squadre: 
        return []
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
        
        if not is_coppa and 38 in giornate_registrate_set and len(classifica) >= 3:
            st.markdown("<div class='winner-card'><h2>🏆 PODIO FINALE CAMPIONATO 🏆</h2></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            for i, col in enumerate([col2, col1, col3]):
                with col:
                    logo_p = f"<img src='{classifica[i]['logo']}' style='width:65px; height:65px; border-radius:50%; object-fit:cover; margin-bottom:8px; border:2px solid #FFD700;' /><br>" if classifica[i]['logo'] else ""
                    st.markdown(f"### {'🥇' if i==0 else '🥈' if i==1 else '🥉'} {classifica[i]['nome']}")
                    if classifica[i]['logo']: 
                        st.markdown(logo_p, unsafe_allow_html=True)
                    st.write(f"**{classifica[i]['punti']} Punti**")
        
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
                        st.info("Nessun punteggio registrato.")
    else:
        st.info("Nessuna squadra configurata.")

elif st.session_state.current_page == "Schedine":
    st.title("📅 Archivio Schedine")
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split(" ")[1])
    
    try:
        schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        
        if squadre:
            squadre_ordinate = sorted(squadre, key=lambda x: x['nome_squadra'])
            for s in squadre_ordinate:
                logo_html = f"<img src='{s.get('logo_url')}' style='width:32px; height:32px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:10px;' />" if s.get('logo_url') else "⚽ "
                st.markdown(f"<div class='grid-card'>{logo_html}<b style='font-size:1.1em;'>{s['nome_squadra']}</b>", unsafe_allow_html=True)
                url = schedine_dict.get(s['id'])
                if url: 
                    st.image(url, use_container_width=True)
                    st.markdown(f"[🔍 Apri Schedina a Schermo Intero]({url})")
                else: 
                    st.caption("Nessuna schedina caricata.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Nessuna squadra registrata.")
    except Exception as e:
        st.error(f"Errore nel recupero delle schedine: {e}")
