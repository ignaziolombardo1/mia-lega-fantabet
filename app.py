import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time
import html
import json
import requests
import google.generativeai as genai

# =========================================================
# CONFIGURAZIONE INIZIALE E CREDENZIALI (SICURA)
# =========================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD")
GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", "gemini-2.0-flash")
FOOTBALL_DATA_API_KEY = st.secrets.get("FOOTBALL_DATA_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "fantabet"
MAX_UPLOAD_MB = 5

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
# FUNZIONI DI SUPPORTO
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
    sq = sorted(supabase.table("squadre").select("*").execute().data or [], key=lambda x: x['nome_squadra'])
    res = supabase.table("risultati").select("*").execute().data or []
    return sq, res

try:
    squadre, risultati = carica_dati_db()
    errore_caricamento = False
except Exception as e:
    squadre, risultati = [], []
    errore_caricamento = True
    st.error(f"Errore nel caricamento dei dati da Supabase: {e}")

try:
    risultati_globali = supabase.table("risultati").select("giornata").execute().data or []
    giornate_completate = set(r['giornata'] for r in risultati_globali if r.get('giornata'))
except Exception as e:
    giornate_completate = set()
    if not errore_caricamento:
        st.warning(f"Impossibile determinare le giornate completate: {e}")

lista_giornate_etichette = [f"Giornata {i} {'✅' if i in giornate_completate else ''}" for i in range(1, 39)]


def squadre_ordinate():
    return sorted(squadre, key=lambda x: x['nome_squadra'])


def valida_immagine(file, max_mb=MAX_UPLOAD_MB):
    if file is None:
        return True, ""
    if file.size > max_mb * 1024 * 1024:
        return False, f"'{file.name}' supera i {max_mb}MB consentiti."
    if not file.type or not file.type.startswith("image/"):
        return False, f"'{file.name}' non è un'immagine valida."
    return True, ""


def carica_su_storage(file, cartella, nome_file):
    ok, msg = valida_immagine(file)
    if not ok:
        st.error(msg)
        return None
    try:
        file_path = f"{cartella}/{nome_file}"
        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path, file=file.getvalue(),
            file_options={"content-type": file.type, "upsert": "true"}
        )
        return supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
    except Exception as e:
        st.error(f"Errore caricamento file su storage: {e}")
        return None


def elimina_da_storage(url):
    if not url:
        return
    try:
        marker = f"/{BUCKET_NAME}/"
        idx = url.find(marker)
        if idx == -1:
            return
        path = url[idx + len(marker):]
        supabase.storage.from_(BUCKET_NAME).remove([path])
    except Exception as e:
        st.warning(f"Impossibile rimuovere un file dallo storage ({e}).")


def trascrivi_schedina_ia(giornata, supabase_client):
    try:
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}. Carica prima le foto."

        model = genai.GenerativeModel(GEMINI_MODEL)
        report = []

        for s in schedine:
            schedina_url = s.get('schedina_url')
            if not schedina_url:
                continue

            sq_obj = next((sq for sq in squadre if sq['id'] == s['squadra_id']), None)
            nome_squadra = sq_obj['nome_squadra'] if sq_obj else f"Squadra ID {s['squadra_id']}"

            try:
                import urllib.request
                req = urllib.request.urlopen(schedina_url, timeout=15)
                image_bytes = req.read()
                image_parts = [{'mime_type': 'image/jpeg', 'data': image_bytes}]
                prompt_testo = """Trascrivi chiaramente tutti i pronostici e le partite che vedi in questa schedina. Elenca le partite e i segni/risultati scelti in modo sintetico e leggibile."""
                response = model.generate_content([image_parts[0], prompt_testo])
                testo_risposta = response.text.strip()
                report.append(f"📌 **{nome_squadra}**:\n{testo_risposta}\n" + "-" * 30)
            except Exception as ex:
                report.append(f"📌 **{nome_squadra}** | Errore lettura immagine: {str(ex)}\n" + "-" * 30)
                continue

        return True, "\n".join(report)
    except Exception as e:
        return False, f"Errore generale: {str(e)}"


# =========================================================
# ANALISI AUTOMATICA SCHEDINE E CALCOLO PUNTI
# =========================================================

TIPI_VALIDI = {"fissa", "doppia", "gg_ng", "over_under"}
SEGNI_VALIDI = {
    "fissa": {"1", "X", "2"},
    "doppia": {"1X", "12", "X2"},
    "gg_ng": {"GG", "NG"},
    "over_under": {"OVER", "UNDER"},
}


def normalizza_nome_squadra(nome):
    if not nome:
        return ""
    nome = nome.lower().strip()
    prefissi = ["ac ", "as ", "us ", "ssc ", "fc ", "ss ", "u.s. ", "a.c. ", "hellas ", "calcio "]
    for p in prefissi:
        if nome.startswith(p):
            nome = nome[len(p):]
    return nome.strip()


def squadre_corrispondono(nome_a, nome_b):
    na, nb = normalizza_nome_squadra(nome_a), normalizza_nome_squadra(nome_b)
    if not na or not nb:
        return False
    return na == nb or na in nb or nb in na


@st.cache_data(ttl=3600)
def recupera_risultati_giornata(giornata):
    if not FOOTBALL_DATA_API_KEY:
        return None, "Chiave FOOTBALL_DATA_API_KEY non configurata nei secrets."
    try:
        headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
        url = f"https://api.football-data.org/v4/competitions/SA/matches?matchday={giornata}"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        risultati = []
        for m in data.get("matches", []):
            if m.get("status") != "FINISHED":
                continue
            score = m.get("score", {}).get("fullTime", {})
            gol_casa, gol_trasferta = score.get("home"), score.get("away")
            if gol_casa is None or gol_trasferta is None:
                continue
            risultati.append({
                "casa": m["homeTeam"]["name"],
                "trasferta": m["awayTeam"]["name"],
                "gol_casa": gol_casa,
                "gol_trasferta": gol_trasferta,
            })
        if not risultati:
            return None, f"Nessun risultato finale disponibile ancora per la Giornata {giornata}."
        return risultati, None
    except Exception as e:
        return None, f"Errore nel recupero risultati da football-data.org: {e}"


def trova_match_reale(squadra_casa, squadra_trasferta, risultati_reali):
    for m in risultati_reali:
        if squadre_corrispondono(squadra_casa, m["casa"]) and squadre_corrispondono(squadra_trasferta, m["trasferta"]):
            return m
    return None


def valuta_pronostico(pick, match):
    gol_casa, gol_trasferta = match["gol_casa"], match["gol_trasferta"]
    segno = "1" if gol_casa > gol_trasferta else "2" if gol_trasferta > gol_casa else "X"
    tipo, pronostico = pick.get("tipo"), pick.get("pronostico")

    if tipo == "fissa":
        return pronostico == segno
    if tipo == "doppia":
        mappa = {"1X": {"1", "X"}, "12": {"1", "2"}, "X2": {"X", "2"}}
        return segno in mappa.get(pronostico, set())
    if tipo == "gg_ng":
        gg = gol_casa > 0 and gol_trasferta > 0
        return pronostico == ("GG" if gg else "NG")
    if tipo == "over_under":
        over = (gol_casa + gol_trasferta) > 2.5
        return pronostico == ("OVER" if over else "UNDER")
    return False


def estrai_pronostici_schedina(schedina_url, model):
    try:
        import urllib.request
        req = urllib.request.urlopen(schedina_url, timeout=15)
        image_bytes = req.read()
        image_part = {'mime_type': 'image/jpeg', 'data': image_bytes}
        prompt = """Analizza l'immagine di questa schedina e trascrivi OGNI pronostico presente in formato JSON valido:
[{"squadra_casa": "...", "squadra_trasferta": "...", "tipo": "...", "pronostico": "..."}]"""
        response = model.generate_content(
            [image_part, prompt],
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
        )
        picks = json.loads(response.text.strip())
        picks_validi = []
        for p in picks:
            tipo = p.get("tipo")
            pronostico = p.get("pronostico")
            if tipo in TIPI_VALIDI and pronostico in SEGNI_VALIDI.get(tipo, set()) and p.get("squadra_casa") and p.get("squadra_trasferta"):
                picks_validi.append(p)
        return picks_validi, None
    except Exception as e:
        return None, f"Errore lettura/analisi immagine: {e}"


def analizza_e_calcola_punti(giornata, supabase_client, squadre_lista):
    risultati_reali, err = recupera_risultati_giornata(giornata)
    if err:
        return None, err

    schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data or []
    if not schedine:
        return None, f"Nessuna schedina caricata per la Giornata {giornata}."

    model = genai.GenerativeModel(GEMINI_MODEL)
    report = []

    for s in schedine:
        sq_obj = next((sq for sq in squadre_lista if sq['id'] == s['squadra_id']), None)
        nome_squadra = sq_obj['nome_squadra'] if sq_obj else f"Squadra ID {s['squadra_id']}"
        schedina_url = s.get('schedina_url')

        picks, err2 = estrai_pronostici_schedina(schedina_url, model) if schedina_url else (None, "Nessuna foto")
        if err2:
            report.append({"squadra_id": s['squadra_id'], "nome": nome_squadra, "errore": err2, "punti_calcolati": None, "dettaglio": []})
            continue

        punti = 0
        dettaglio = []
        for p in picks:
            match = trova_match_reale(p["squadra_casa"], p["squadra_trasferta"], risultati_reali)
            if match is None:
                dettaglio.append({**p, "esito": "❓ partita non trovata"})
                continue
            corretto = valuta_pronostico(p, match)
            if corretto:
                punti += 1
            dettaglio.append({**p, "esito": "✅" if corretto else "❌", "risultato_reale": f"{match['gol_casa']}-{match['gol_trasferta']}"})

        report.append({"squadra_id": s['squadra_id'], "nome": nome_squadra, "errore": None, "punti_calcolati": punti, "dettaglio": dettaglio})

    return report, None


# =========================================================
# FUNZIONI PER STATISTICHE E BADGE
# =========================================================

def calcola_statistiche_squadra(squadra_id, risultati_totali):
    res_squadra = [r for r in risultati_totali if r['squadra_id'] == squadra_id and r.get('punteggio') is not None]
    if not res_squadra:
        return {"media": 0.0, "best": 0, "giornate_giocate": 0, "badge": []}
    
    punti_lista = [int(r['punteggio']) for r in res_squadra]
    tot_giornate = len(punti_lista)
    media = sum(punti_lista) / tot_giornate if tot_giornate > 0 else 0
    best = max(punti_lista) if punti_lista else 0
    
    badge = []
    if best >= 8:
        badge.append("🔥 Bomber di Giornata")
    if tot_giornate >= 3 and media >= 5.0:
        badge.append("🎯 Cecchino Costante")
        
    return {
        "media": round(media, 2),
        "best": best,
        "giornate_giocate": tot_giornate,
        "badge": badge
    }


# =========================================================
# BARRA LATERALE ADMIN
# =========================================================

with st.sidebar:
    st.subheader("⚙️ Area Amministratore Pro")
    if not st.session_state.admin:
        if not ADMIN_PASSWORD:
            st.error("ADMIN_PASSWORD non configurata nei secrets.")
        pwd = st.text_input("Password Admin", type="password", disabled=not ADMIN_PASSWORD)
        if st.button("Autenticati", disabled=not ADMIN_PASSWORD):
            if pwd == ADMIN_PASSWORD:
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
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["➕ Squadra", "🤖 IA", "🎫 Schedine", "⚽ Punti", "🗑️ Elimina", "📢 News"])
        
        with tab1:
            with st.form("add_s"):
                n = st.text_input("Nome Squadra")
                logo_file = st.file_uploader("Logo Ufficiale", type=["png", "jpg", "jpeg"])
                
                if st.form_submit_button("Registra Squadra"): 
                    if n:
                        logo_url = ""
                        if logo_file is not None:
                            nome_file = f"{datetime.now().timestamp()}_{logo_file.name}"
                            risultato_url = carica_su_storage(logo_file, "loghi", nome_file)
                            logo_url = risultato_url or ""

                        supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo_url}).execute()
                        st.toast("Squadra registrata correttamente!", icon="⚽")
                        time.sleep(1.0)
                        st.rerun()
                    else:
                        st.warning("Inserisci il nome della squadra.")

        with tab2:
            st.write("### 🤖 Calcolo Punti Automatico con IA")
            g_auto = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_auto_api")
            num_g_auto = int(g_auto.split()[1])

            col_a1, col_a2 = st.columns(2)
            if col_a1.button("🔍 Solo trascrivi schedine"):
                with st.spinner("Estrazione pronostici in corso..."):
                    successo, messaggio = trascrivi_schedina_ia(num_g_auto, supabase)
                    if successo:
                        st.success("Lettura completata!")
                        st.markdown(messaggio)
                    else:
                        st.error(messaggio)

            if col_a2.button("🧮 Analizza e Calcola Punti IA", type="primary"):
                with st.spinner("Analisi schedine in corso..."):
                    report, err = analizza_e_calcola_punti(num_g_auto, supabase, squadre)
                    if err:
                        st.error(err)
                        st.session_state.pop("report_ia", None)
                    else:
                        st.session_state.report_ia = {"giornata": num_g_auto, "dati": report}
                        st.success("Analisi completata!")

            report_sessione = st.session_state.get("report_ia")
            if report_sessione and report_sessione["giornata"] == num_g_auto:
                st.markdown("---")
                punti_da_salvare = {}
                for item in report_sessione["dati"]:
                    with st.expander(f"📌 {item['nome']} — {'⚠️ Errore' if item['errore'] else str(item['punti_calcolati']) + ' punti suggeriti'}"):
                        if item["errore"]:
                            st.error(item["errore"])
                            continue
                        if item["dettaglio"]:
                            st.dataframe(pd.DataFrame(item["dettaglio"]), use_container_width=True)
                        punti_corretti = st.number_input("Punti da salvare", min_value=0, value=int(item['punti_calcolati'] or 0), step=1, key=f"ia_pts_{item['squadra_id']}")
                        punti_da_salvare[item["squadra_id"]] = punti_corretti

                if punti_da_salvare and st.button("💾 Conferma e Salva Punti in Classifica", type="primary"):
                    for s_id, p in punti_da_salvare.items():
                        supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_auto).execute()
                        supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_auto}).execute()
                    st.session_state.pop("report_ia", None)
                    st.toast("Punti salvati!", icon="✅")
                    time.sleep(1.0)
                    st.rerun()

        with tab3:
            st.write("### 🎫 Carica Schedine in Blocco")
            if squadre:
                g_sch = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_sch_foto_multi")
                num_g_sch = int(g_sch.split()[1])
                
                st.markdown("---")
                dati_caricamento = {}
                for s in squadre_ordinate():
                    st.markdown(f"<div class='schedina-box'><b>⚽ {html.escape(s['nome_squadra'])}</b>", unsafe_allow_html=True)
                    f_foto = st.file_uploader(f"Screenshot Schedina - {s['nome_squadra']}", type=["png", "jpg", "jpeg"], key=f"foto_{s['id']}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    dati_caricamento[s['id']] = f_foto
                
                if st.button("💾 Salva Tutte le Schedine Caricate", type="primary"):
                    with st.spinner("Caricamento in corso..."):
                        caricate = 0
                        for s_id, file_foto in dati_caricamento.items():
                            if file_foto is not None:
                                nome_file = f"g{num_g_sch}_{s_id}_{datetime.now().timestamp()}.png"
                                url_img = carica_su_storage(file_foto, "schedine", nome_file)
                                if url_img:
                                    supabase.table("schedine").delete().eq("squadra_id", s_id).eq("giornata", num_g_sch).execute()
                                    supabase.table("schedine").insert({
                                        "squadra_id": s_id,
                                        "giornata": num_g_sch,
                                        "schedina_url": url_img,
                                        "pronostici_json": {},
                                        "visibile": False
                                    }).execute()
                                    caricate += 1
                        
                        if caricate > 0:
                            st.toast(f"Salvate {caricate} schedine (Nascoste al pubblico)!", icon="🎉")
                            time.sleep(1.2)
                            st.rerun()
                        else:
                            st.warning("Nessuna foto caricata.")
                
                st.markdown("---")
                if st.button(f"🔓 Rivela Schedine Giornata {num_g_sch} al Pubblico", type="primary"):
                    supabase.table("schedine").update({"visibile": True}).eq("giornata", num_g_sch).execute()
                    st.toast(f"Schedine della Giornata {num_g_sch} ora visibili a tutti!", icon="👁️")
                    time.sleep(1.0)
                    st.rerun()
            else:
                st.info("Nessuna squadra disponibile.")
                
        with tab4:
            st.write("### ⚽ Gestione Punti Manuali")
            if squadre:
                g_pts = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_pts_multi")
                num_g_pts = int(g_pts.split()[1])
                existing_res = {r['squadra_id']: r['punteggio'] for r in supabase.table("risultati").select("squadra_id, punteggio").eq("giornata", num_g_pts).execute().data or []}

                with st.form("add_p_multi"):
                    punti_inseriti = {}
                    for s in squadre_ordinate():
                        punti_inseriti[s['id']] = st.number_input(f"Punti {s['nome_squadra']}", min_value=0, value=int(existing_res.get(s['id'], 0)), step=1, key=f"pts_{s['id']}")
                    
                    c_f1, c_f2 = st.columns(2)
                    if c_f1.form_submit_button("💾 Salva Tutti i Punti", type="primary"):
                        for s_id, p in punti_inseriti.items():
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0:
                                supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_pts}).execute()
                        st.toast("Punti aggiornati!", icon="✅")
                        time.sleep(1.0)
                        st.rerun()
                    if c_f2.form_submit_button("🗑️ Azzera Giornata"):
                        supabase.table("risultati").delete().eq("giornata", num_g_pts).execute()
                        st.toast("Giornata azzerata!", icon="⚠️")
                        time.sleep(1.0)
                        st.rerun()
            else:
                st.info("Inserisci prima le squadre.")
                
        with tab5:
            st.write("### Gestione ed Eliminazione")
            g_del = st.selectbox("Giornata", lista_giornate_etichette, index=giornata_idx, key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            schedine_g = supabase.table("schedine").select("*").eq("giornata", num_g_del).execute().data or []
            squadre_con_schedina = sorted([s for s in squadre if s['id'] in [sch['squadra_id'] for sch in schedine_g]], key=lambda x: x['nome_squadra'])
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    schedina_da_rimuovere = next((sch for sch in schedine_g if sch['squadra_id'] == s_id_del), None)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    if schedina_da_rimuovere:
                        elimina_da_storage(schedina_da_rimuovere.get('schedina_url'))
                    st.toast("Schedina rimossa.", icon="🗑️")
                    time.sleep(1.0)
                    st.rerun()
            else:
                st.info("Nessuna schedina presente.")
                
            st.markdown("---")
            if squadre:
                sq_del = st.selectbox("Elimina Squadra Definitivamente", [s['nome_squadra'] for s in squadre_ordinate()], key="sq_del_tot")
                if st.button("Rimuovi Squadra e Dati"):
                    s_id = next(s['id'] for s in squadre if s['nome_squadra'] == sq_del)
                    squadra_obj = next(s for s in squadre if s['id'] == s_id)
                    schedine_squadra = supabase.table("schedine").select("schedina_url").eq("squadra_id", s_id).execute().data or []
                    supabase.table("squadre").delete().eq("id", s_id).execute()
                    supabase.table("risultati").delete().eq("squadra_id", s_id).execute()
                    supabase.table("schedine").delete().eq("squadra_id", s_id).execute()
                    elimina_da_storage(squadra_obj.get('logo_url'))
                    for sch in schedine_squadra:
                        elimina_da_storage(sch.get('schedina_url'))
                    st.toast("Squadra eliminata.", icon="⚠️")
                    time.sleep(1.0)
                    st.rerun()

        with tab6:
            st.write("### 📢 Bacheca Ultime Notizie & Video")
            nuova_news = st.text_area("Messaggio Bacheca", placeholder="Es. Ricordatevi di caricare le schedine!")
            
            # Campo caricamento video opzionale
            video_file = st.file_uploader("Carica Video Notizia (Opzionale)", type=["mp4", "mov", "avi"])
            
            if st.button("Pubblica News con Video"):
                video_url = ""
                if video_file is not None:
                    nome_file_vid = f"news_{datetime.now().timestamp()}_{video_file.name}"
                    try:
                        file_path = f"news/{nome_file_vid}"
                        supabase.storage.from_(BUCKET_NAME).upload(
                            path=file_path, file=video_file.getvalue(),
                            file_options={"content-type": video_file.type, "upsert": "true"}
                        )
                        video_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                    except Exception as e:
                        st.error(f"Errore caricamento video: {e}")

                try:
                    supabase.table("news").delete().neq("id", 0).execute()
                except Exception:
                    pass
                    
                supabase.table("news").insert({
                    "testo": nuova_news, 
                    "video_url": video_url, 
                    "data": str(datetime.now().date())
                }).execute()
                
                st.toast("News e Video pubblicati con successo!", icon="🎬")
                time.sleep(1.0)
                st.rerun()

# =========================================================
# INTERFACCIA PRINCIPALE
# =========================================================

st.title("⚽ FantaBet Serie A Pro")

# Mostra la bacheca news e l'eventuale video
try:
    news_data = supabase.table("news").select("*").execute().data
    if news_data:
        ultima_news = news_data[0].get('testo', '')
        video_url_news = news_data[0].get('video_url', '')
        
        st.markdown(f"""
            <div class="alert-box" style="border-left: 5px solid #FFD700; background: rgba(255, 215, 0, 0.1);">
                📢 <b>Comunicato della Lega:</b> {html.escape(ultima_news)}
            </div>
        """, unsafe_allow_html=True)
        
        if video_url_news:
            st.video(video_url_news)
            
except Exception:
    pass

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
        classifica_temp.append({'id': s['id'], 'nome': s['nome_squadra'], 'punti': punti_totali, 'logo': s.get('logo_url'), 'dettaglio': dettaglio_giornate})
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
        
        for pos, item in enumerate(classifica, 1):
            c_class = "gold" if pos == 1 else "silver" if pos == 2 else "bronze" if pos == 3 else "" if not is_coppa else ("gold" if pos == 1 else "")
            badge_pos = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"{pos}°" if not is_coppa else ("🥇" if pos == 1 else f"{pos}°")
            logo_html = f"<img src='{html.escape(item['logo'])}' style='width:32px; height:32px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽ "
            
            st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:38px; font-size:1.1em;">{badge_pos}</span>
                        {logo_html}
                        <span style="flex-grow:1; margin-left:5px; font-weight:bold; font-size:1.1em;">{html.escape(item['nome'])}</span>
                        <span style="font-weight:bold; color:#4CAF50; font-size:1.1em;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)
            
            if not is_coppa:
                stats = calcola_statistiche_squadra(item['id'], risultati)
                with st.expander(f"📊 Dettaglio & Statistiche - {item['nome']}"):
                    if stats['badge']:
                        st.markdown("##### 🏆 Riconoscimenti & Badge")
                        badges_html = " ".join([f"<span style='background:rgba(255,215,0,0.2); border:1px solid #FFD700; padding:4px 8px; border-radius:8px; font-size:0.85em; margin-right:5px;'>{b}</span>" for b in stats['badge']])
                        st.markdown(badges_html, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    col_stat1.metric("Media Punti", stats['media'])
                    col_stat2.metric("Record Giornata", stats['best'])
                    col_stat3.metric("Giornate Giocate", stats['giornate_giocate'])
                    
                    if item['dettaglio']:
                        st.markdown("---")
                        df_dettaglio = pd.DataFrame(list(item['dettaglio'].items()), columns=['Giornata', 'Punti']).sort_values('Giornata')
                        st.dataframe(df_dettaglio.set_index('Giornata'), use_container_width=True)
                    else:
                        st.info("Nessun punteggio registrato.")
    else:
        st.info("Nessuna squadra configurata.")

elif st.session_state.current_page == "Schedine":
    st.title("📅 Archivio Schedine")
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split()[1])
    
    try:
        query = supabase.table("schedine").select("*").eq("giornata", num_g)
        if not st.session_state.get("admin", False):
            query = query.eq("visibile", True)
            
        schedine = query.execute().data or []
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        
        if not schedine and not st.session_state.get("admin", False):
            st.info("🤐 Le schedine per questa giornata non sono ancora state rivelate dall'amministratore!")
        elif squadre:
            for s in squadre_ordinate():
                logo_html = f"<img src='{html.escape(s.get('logo_url'))}' style='width:32px; height:32px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:10px;' />" if s.get('logo_url') else "⚽ "
                st.markdown(f"<div class='grid-card'>{logo_html}<b style='font-size:1.1em;'>{html.escape(s['nome_squadra'])}</b>", unsafe_allow_html=True)
                url = schedine_dict.get(s['id'])
                if url: 
                    st.image(url, use_container_width=True)
                    st.markdown(f"[🔍 Apri Schedina a Schermo Intero]({url})")
                else: 
                    st.caption("Nessuna schedina caricata o ancora nascosta.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Nessuna squadra registrata.")
    except Exception as e:
        st.error(f"Errore nel recupero delle schedine: {e}")
