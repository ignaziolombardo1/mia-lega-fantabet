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

# Nessun fallback in chiaro: se manca il secret, l'accesso admin resta disabilitato
# finché non viene configurato correttamente.
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD")

# Nome del modello Gemini configurabile via secrets, con un default.
# NB: verifica su https://ai.google.dev/gemini-api/docs/models il nome esatto
# del modello disponibile per il tuo account/API key prima del deploy:
# 'gemini-3.6-flash' non è un nome di modello che risulta pubblicato al momento
# in cui questo codice è stato scritto.
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
    """Ritorna la lista squadre già ordinata, per evitare di riordinare in ogni tab."""
    return sorted(squadre, key=lambda x: x['nome_squadra'])


def valida_immagine(file, max_mb=MAX_UPLOAD_MB):
    """Controlla dimensione e tipo di un file caricato prima di inviarlo allo storage."""
    if file is None:
        return True, ""
    if file.size > max_mb * 1024 * 1024:
        return False, f"'{file.name}' supera i {max_mb}MB consentiti."
    if not file.type or not file.type.startswith("image/"):
        return False, f"'{file.name}' non è un'immagine valida."
    return True, ""


def carica_su_storage(file, cartella, nome_file):
    """Carica un file validato su Supabase Storage e ritorna l'URL pubblico, o None in caso di errore."""
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
    """Rimuove un file dallo storage a partire dal suo URL pubblico, per evitare file orfani."""
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
        st.warning(f"Impossibile rimuovere un file dallo storage ({e}). Potrebbe restare un file orfano nel bucket.")


def trascrivi_schedina_ia(giornata, supabase_client):
    """Il bot si limita a leggere i pronostici dall'immagine per aiutarti nel controllo visivo."""
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
# ANALISI AUTOMATICA SCHEDINE E CALCOLO PUNTI (IA + API RISULTATI)
# =========================================================

TIPI_VALIDI = {"fissa", "doppia", "gg_ng", "over_under"}
SEGNI_VALIDI = {
    "fissa": {"1", "X", "2"},
    "doppia": {"1X", "12", "X2"},
    "gg_ng": {"GG", "NG"},
    "over_under": {"OVER", "UNDER"},
}


def normalizza_nome_squadra(nome):
    """Normalizza un nome squadra per il confronto (rimuove prefissi societari comuni, minuscolo)."""
    if not nome:
        return ""
    nome = nome.lower().strip()
    prefissi = ["ac ", "as ", "us ", "ssc ", "fc ", "ss ", "u.s. ", "a.c. ", "hellas ", "calcio "]
    for p in prefissi:
        if nome.startswith(p):
            nome = nome[len(p):]
    return nome.strip()


def squadre_corrispondono(nome_a, nome_b):
    """Confronto fuzzy tra due nomi squadra: normalizza ed esegue un controllo di sottostringa."""
    na, nb = normalizza_nome_squadra(nome_a), normalizza_nome_squadra(nome_b)
    if not na or not nb:
        return False
    return na == nb or na in nb or nb in na


@st.cache_data(ttl=3600)
def recupera_risultati_giornata(giornata):
    """Recupera i risultati finali della giornata di Serie A da football-data.org.
    Ritorna (lista_risultati, errore)."""
    if not FOOTBALL_DATA_API_KEY:
        return None, "Chiave FOOTBALL_DATA_API_KEY non configurata nei secrets. Registrati gratis su football-data.org."
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
    """Ritorna True/False se il pronostico è corretto rispetto al risultato reale del match."""
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
    """Usa Gemini Vision per trascrivere in JSON strutturato i pronostici di una schedina.
    Ritorna (lista_pronostici, errore)."""
    try:
        import urllib.request
        req = urllib.request.urlopen(schedina_url, timeout=15)
        image_bytes = req.read()
        image_part = {'mime_type': 'image/jpeg', 'data': image_bytes}

        prompt = """Analizza l'immagine di questa schedina di pronostici sportivi e trascrivi OGNI pronostico presente, uno per elemento. Per ciascuno indica:
- squadra_casa: nome della squadra di casa
- squadra_trasferta: nome della squadra in trasferta
- tipo: uno tra "fissa" (1X2 secco), "doppia" (doppia chance: 1X, 12, X2), "gg_ng" (Goal/No Goal), "over_under" (Over/Under 2.5 gol)
- pronostico: il segno scelto, esattamente uno tra questi valori a seconda del tipo:
  - fissa: "1", "X", "2"
  - doppia: "1X", "12", "X2"
  - gg_ng: "GG", "NG"
  - over_under: "OVER", "UNDER"

Rispondi SOLO con un array JSON valido, senza testo aggiuntivo, markdown o spiegazioni, nel formato:
[{"squadra_casa": "...", "squadra_trasferta": "...", "tipo": "...", "pronostico": "..."}]"""

        response = model.generate_content(
            [image_part, prompt],
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
        )
        testo = response.text.strip()
        picks = json.loads(testo)

        picks_validi = []
        for p in picks:
            tipo = p.get("tipo")
            pronostico = p.get("pronostico")
            if tipo in TIPI_VALIDI and pronostico in SEGNI_VALIDI.get(tipo, set()) and p.get("squadra_casa") and p.get("squadra_trasferta"):
                picks_validi.append(p)
        return picks_validi, None
    except json.JSONDecodeError:
        return None, "L'IA non ha restituito un JSON valido: riprova o controlla la qualità della foto."
    except Exception as e:
        return None, f"Errore lettura/analisi immagine: {e}"


def analizza_e_calcola_punti(giornata, supabase_client, squadre_lista):
    """Analizza tutte le schedine di una giornata con l'IA e calcola i punti suggeriti
    confrontandoli con i risultati reali. Ritorna (report, errore)."""
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
            dettaglio.append({**p, "esito": "✅" if corretto else "❌",
                               "risultato_reale": f"{match['gol_casa']}-{match['gol_trasferta']}"})

        report.append({"squadra_id": s['squadra_id'], "nome": nome_squadra, "errore": None,
                        "punti_calcolati": punti, "dettaglio": dettaglio})

    return report, None


# =========================================================
# BARRA LATERALE ADMIN
# =========================================================

with st.sidebar:
    st.subheader("⚙️ Area Amministratore Pro")
    if not st.session_state.admin:
        if not ADMIN_PASSWORD:
            st.error("ADMIN_PASSWORD non configurata nei secrets. Impostala per abilitare l'accesso admin.")
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
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Squadra", "🤖 Trascrizione IA", "🎫 Schedine", "⚽ Punti Manuali", "🗑️ Elimina"])
        
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
            st.caption("L'IA legge ogni schedina, la confronta con i risultati reali della giornata (via football-data.org) e propone un punteggio. Controlla sempre il dettaglio prima di salvare: l'IA può sbagliare lettura o abbinamento partite.")
            g_auto = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_auto_api")
            num_g_auto = int(g_auto.split()[1])

            col_a1, col_a2 = st.columns(2)
            if col_a1.button("🔍 Solo trascrivi schedine (testo libero)"):
                with st.spinner("Estrazione pronostici in corso..."):
                    successo, messaggio = trascrivi_schedina_ia(num_g_auto, supabase)
                    if successo:
                        st.success("Lettura completata!")
                        st.markdown(messaggio)
                    else:
                        st.error(messaggio)

            if col_a2.button("🧮 Analizza e Calcola Punti IA", type="primary"):
                with st.spinner("Analisi schedine e confronto con i risultati reali in corso..."):
                    report, err = analizza_e_calcola_punti(num_g_auto, supabase, squadre)
                    if err:
                        st.error(err)
                        st.session_state.pop("report_ia", None)
                    else:
                        st.session_state.report_ia = {"giornata": num_g_auto, "dati": report}
                        st.success("Analisi completata! Controlla il dettaglio qui sotto prima di salvare.")

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
                            df_dett = pd.DataFrame(item["dettaglio"])
                            st.dataframe(df_dett, use_container_width=True)
                        else:
                            st.info("Nessun pronostico riconosciuto nella schedina.")
                        punti_corretti = st.number_input(
                            "Punti da salvare per questa squadra (modifica se necessario)",
                            min_value=0, value=int(item["punti_calcolati"]), step=1,
                            key=f"ia_pts_{item['squadra_id']}"
                        )
                        punti_da_salvare[item["squadra_id"]] = punti_corretti

                if punti_da_salvare and st.button("💾 Conferma e Salva Punti in Classifica", type="primary"):
                    for s_id, p in punti_da_salvare.items():
                        supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_auto).execute()
                        supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_auto}).execute()
                    st.session_state.pop("report_ia", None)
                    st.toast("Punti calcolati dall'IA salvati in classifica!", icon="✅")
                    time.sleep(1.0)
                    st.rerun()

        with tab3:
            st.write("### 🎫 Carica Schedine in Blocco")
            if squadre:
                g_sch = st.selectbox("Seleziona Giornata di Riferimento", lista_giornate_etichette, index=giornata_idx, key="g_sch_foto_multi")
                num_g_sch = int(g_sch.split()[1])
                
                st.markdown("---")
                dati_caricamento = {}
                for s in squadre_ordinate():
                    st.markdown(f"<div class='schedina-box'><b>⚽ {html.escape(s['nome_squadra'])}</b>", unsafe_allow_html=True)
                    f_foto = st.file_uploader(f"Screenshot Schedina - {s['nome_squadra']}", type=["png", "jpg", "jpeg"], key=f"foto_{s['id']}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    dati_caricamento[s['id']] = f_foto
                
                if st.button("💾 Salva Tutte le Schedine Caricate", type="primary"):
                    with st.spinner("Caricamento in corso su Supabase..."):
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
                                        "pronostici_json": {}
                                    }).execute()
                                    caricate += 1
                        
                        if caricate > 0:
                            st.toast(f"Salvate con successo {caricate} schedine!", icon="🎉")
                            time.sleep(1.2)
                            st.rerun()
                        else:
                            st.warning("Nessuna foto caricata correttamente.")
            else:
                st.info("Nessuna squadra disponibile.")
                
        with tab4:
            st.write("### ⚽ Gestione Punti Manuali (100% Sicuro)")
            st.caption("Inserisci direttamente il punteggio esatto ottenuto da ogni squadra nella giornata selezionata.")
            if squadre:
                g_pts = st.selectbox("Seleziona Giornata", lista_giornate_etichette, index=giornata_idx, key="g_pts_multi")
                num_g_pts = int(g_pts.split()[1])
                
                existing_res = {r['squadra_id']: r['punteggio'] for r in supabase.table("risultati").select("squadra_id, punteggio").eq("giornata", num_g_pts).execute().data or []}

                with st.form("add_p_multi"):
                    punti_inseriti = {}
                    for s in squadre_ordinate():
                        valore_precedente = existing_res.get(s['id'], 0)
                        punti_inseriti[s['id']] = st.number_input(f"Punti {s['nome_squadra']}", min_value=0, value=int(valore_precedente), step=1, key=f"pts_{s['id']}")
                    
                    col_form1, col_form2 = st.columns(2)
                    salva_punti = col_form1.form_submit_button("💾 Salva Tutti i Punti", type="primary")
                    azzera_giornata = col_form2.form_submit_button("🗑️ Azzera Giornata")
                    
                    if salva_punti:
                        for s_id, p in punti_inseriti.items():
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0:
                                supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_pts}).execute()
                        st.toast("Punti aggiornati con successo nella classifica!", icon="✅")
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
                schedine_g = supabase.table("schedine").select("*").eq("giornata", num_g_del).execute().data or []
                squadre_con_schedina = sorted(
                    [s for s in squadre if s['id'] in [sch['squadra_id'] for sch in schedine_g]],
                    key=lambda x: x['nome_squadra']
                )
            except Exception as e:
                schedine_g = []
                squadre_con_schedina = []
                st.error(f"Errore nel recupero delle schedine: {e}")
            
            if squadre_con_schedina:
                sq_sch_del = st.selectbox("Squadra Schedina", [s['nome_squadra'] for s in squadre_con_schedina], key="sq_sch_del")
                if st.button("Elimina Schedina"):
                    s_id_del = next(s['id'] for s in squadre_con_schedina if s['nome_squadra'] == sq_sch_del)
                    schedina_da_rimuovere = next((sch for sch in schedine_g if sch['squadra_id'] == s_id_del), None)
                    supabase.table("schedine").delete().eq("squadra_id", s_id_del).eq("giornata", num_g_del).execute()
                    if schedina_da_rimuovere:
                        elimina_da_storage(schedina_da_rimuovere.get('schedina_url'))
                    st.toast("Schedina rimossa correttamente.", icon="🗑️")
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

                    # Pulizia dei file nello storage per non lasciare file orfani nel bucket
                    elimina_da_storage(squadra_obj.get('logo_url'))
                    for sch in schedine_squadra:
                        elimina_da_storage(sch.get('schedina_url'))

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
                    logo_p = f"<img src='{html.escape(classifica[i]['logo'])}' style='width:65px; height:65px; border-radius:50%; object-fit:cover; margin-bottom:8px; border:2px solid #FFD700;' /><br>" if classifica[i]['logo'] else ""
                    st.markdown(f"### {'🥇' if i==0 else '🥈' if i==1 else '🥉'} {html.escape(classifica[i]['nome'])}")
                    if classifica[i]['logo']: 
                        st.markdown(logo_p, unsafe_allow_html=True)
                    st.write(f"**{classifica[i]['punti']} Punti**")
        
        if is_coppa:
            fine_coppa = 17 if st.session_state.current_page == "Coppa Inverno" else 32
            if fine_coppa in giornate_registrate_set and classifica and classifica[0]['punti'] > 0:
                vincitore = classifica[0]
                logo_v = f"<img src='{html.escape(vincitore['logo'])}' style='width:100px; height:100px; border-radius:50%; object-fit:cover; border:3px solid #FFD700; margin-bottom:12px; box-shadow: 0 0 15px rgba(255,215,0,0.5);' />" if vincitore['logo'] else "🏆"
                st.markdown(f"""<div class="winner-card">
                        <h2 style="color:#FFD700; letter-spacing: 1px;">🏆 TRIONFO {html.escape(st.session_state.current_page.upper())} 🏆</h2>
                        {logo_v}
                        <h1 style="color:#FFF; margin-top:5px; font-size:2.2em;">🥇 {html.escape(vincitore['nome'])}</h1>
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

            logo_html = f"<img src='{html.escape(item['logo'])}' style='width:32px; height:32px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽ "
            
            st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:38px; font-size:1.1em;">{badge_pos}</span>
                        {logo_html}
                        <span style="flex-grow:1; margin-left:5px; font-weight:bold; font-size:1.1em;">{html.escape(item['nome'])}</span>
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
            for s in squadre_ordinate():
                logo_html = f"<img src='{html.escape(s.get('logo_url'))}' style='width:32px; height:32px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:10px;' />" if s.get('logo_url') else "⚽ "
                st.markdown(f"<div class='grid-card'>{logo_html}<b style='font-size:1.1em;'>{html.escape(s['nome_squadra'])}</b>", unsafe_allow_html=True)
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
