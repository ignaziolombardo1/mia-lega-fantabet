import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time
import os
from openai import OpenAI

# 1. Configurazione Supabase
SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "fantabet"

# 2. Configurazione Pagina
st.set_page_config(page_title="FantaBet Serie A Pro", page_icon="⚽", layout="wide")

# 3. Logica del Bot integrata direttamente per evitare errori di importazione
def calcola_risultati_da_foto_o_dati(giornata, supabase_client):
    try:
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}."
        
        # Risultati reali di test (adattabili a piacimento)
        risultati_reali = ['1', 'X', '2', '1']
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("OPENAI_API_KEY")
            except:
                pass
                
        if not api_key:
            return False, "Chiave OpenAI non trovata nei secrets o nelle variabili d'ambiente."
            
        client = OpenAI(api_key=api_key)
        
        report = []
        for s in schedine:
            schedina_url = s.get('schedina_url')
            if not schedina_url:
                continue
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "Analizza questa schedina di pronostici calcistici. Leggi tutti gli eventi presenti nell'immagine. Per ogni evento, estrai il pronostico effettuato (può essere '1', 'X', '2'). Restituisci la risposta ESCLUSIVAMENTE come una lista Python di stringhe, ad esempio: ['1', 'X', '2', '1']. Non aggiungere altro testo, nessun blocco di codice markdown, solo la lista."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": schedina_url}
                                }
                            ]
                        }
                    ],
                    max_tokens=200
                ]
                
                risposta_ai = response.choices[0].message.content.strip()
                risposta_ai = risposta_ai.replace("```python", "").replace("```", "").strip()
                
                pronostici_letti = eval(risposta_ai)
                if not isinstance(pronostici_letti, list):
                    pronostici_letti = []
            except Exception as ex:
                report.append(f"Squadra ID {s['squadra_id']}: Errore lettura immagine ({str(ex)})")
                continue
            
            punti_ottenuti = 0
            totale_eventi_letti = len(pronostici_letti)
            
            for i in range(min(len(pronostici_letti), len(risultati_reali))):
                if str(pronostici_letti[i]).strip().upper() == str(risultati_reali[i]).strip().upper():
                    punti_ottenuti += 1
            
            supabase_client.table("risultati").delete().eq("squadra_id", s['squadra_id']).eq("giornata", giornata).execute()
            
            supabase_client.table("risultati").insert({
                "squadra_id": s['squadra_id'], 
                "giornata": giornata, 
                "punteggio": punti_ottenuti
            }).execute()
            
            report.append(f"Squadra ID {s['squadra_id']}: {punti_ottenuti}/{totale_eventi_letti} punti (Letti: {pronostici_letti})")
        
        return True, "\n".join(report)
        
    except Exception as e:
        return False, f"Errore generale nel bot: {str(e)}"

# Stile CSS
st.markdown("""
    <style>
    :root { --background-color: #0E1117; --secondary-background-color: #1F242D; --text-color: #FAFAFA; }
    .stApp { background-color: #0E1117 !important; background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("https://raw.githubusercontent.com/ignaziolombardo1/mia-lega-fantabet/09303f4ca4eb42c4588877ea340edf896abdef02/background.jpg"); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, h5, p, span { color: #FAFAFA !important; text-shadow: 2px 2px 4px #000; }
    .card { background: rgba(30,30,30,0.85); padding: 16px; border-radius: 14px; margin-bottom: 12px; border-left: 5px solid #4CAF50; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .gold { border-left: 5px solid #FFD700 !important; background: rgba(255, 215, 0, 0.12) !important; }
    .silver { border-left: 5px solid #C0C0C0 !important; background: rgba(192, 192, 192, 0.1) !important; }
    .bronze { border-left: 5px solid #CD7F32 !important; background: rgba(205, 127, 50, 0.1) !important; }
    .winner-card { background: rgba(20, 20, 20, 0.95); border: 2px solid #FFD700; padding: 30px; border-radius: 20px; text-align: center; margin: 25px 0; }
    .alert-box { background: rgba(33, 150, 243, 0.15); border-left: 5px solid #2196F3; padding: 14px; border-radius: 10px; margin-bottom: 25px; color: #fff; }
    .schedina-box { background: rgba(25, 25, 30, 0.9); padding: 15px; border-radius: 10px; border: 1px solid #444; margin-bottom: 15px; }
    .grid-card { background: rgba(25, 25, 30, 0.85); padding: 15px; border-radius: 12px; border: 1px solid #333; text-align: center; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

def get_giornata_corrente():
    oggi = datetime.now().date()
    inizio = datetime(2026, 8, 23).date()
    return max(1, min(38, ((oggi - inizio).days // 7) + 1)) if oggi >= inizio else 1

giornata_idx = get_giornata_corrente() - 1

if "current_page" not in st.session_state: st.session_state.current_page = "Classifica"
if "admin" not in st.session_state: st.session_state.admin = False

@st.cache_data(ttl=30)
def carica_dati_db():
    try:
        sq = sorted(supabase.table("squadre").select("*").execute().data or [], key=lambda x: x['nome_squadra'])
        res = supabase.table("risultati").select("*").execute().data or []
        return sq, res
    except:
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
                st.toast("Accesso effettuato!", icon="🔓")
                time.sleep(0.6)
                st.rerun()
            else: 
                st.error("Password errata")
    else:
        st.success("Sessione Admin Attiva")
        if st.button("Disconnetti"): 
            st.session_state.admin = False
            st.rerun()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Squadra", "🤖 Bot API", "🎫 Schedine", "⚽ Punti", "🗑️ Elimina"])
        
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
                                st.error(f"Errore logo: {e}")
                        supabase.table("squadre").insert({"nome_squadra": n, "logo_url": logo_url}).execute()
                        st.toast("Squadra registrata!", icon="⚽")
                        time.sleep(1.0)
                        st.rerun()

        with tab2:
            st.write("### Controllo Automatico Bot")
            g_auto = st.selectbox("Giornata da Verificare", lista_giornate_etichette, index=giornata_idx, key="g_auto_api")
            num_g_auto = int(g_auto.split()[1])
            
            if st.button("Avvia Analisi IA Schedine"):
                with st.spinner("Analisi immagini in corso con IA..."):
                    successo, messaggio = calcola_risultati_da_foto_o_dati(num_g_auto, supabase)
                    if successo:
                        st.success("Analisi completata!")
                        st.text_area("Log esito Bot:", value=messaggio, height=150)
                    else:
                        st.error(messaggio)

        with tab3:
            st.write("### 🎫 Carica Schedine in Blocco")
            if squadre:
                g_sch = st.selectbox("Giornata di Riferimento", lista_giornate_etichette, index=giornata_idx, key="g_sch_foto_multi")
                num_g_sch = int(g_sch.split()[1])
                dati_caricamento = {}
                for s in squadre:
                    st.markdown(f"<div class='schedina-box'><b>⚽ {s['nome_squadra']}</b>", unsafe_allow_html=True)
                    f_foto = st.file_uploader(f"Screenshot - {s['nome_squadra']}", type=["png", "jpg", "jpeg"], key=f"foto_{s['id']}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    dati_caricamento[s['id']] = f_foto
                
                if st.button("💾 Salva Tutte le Schedine", type="primary"):
                    with st.spinner("Caricamento..."):
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
                                        "squadra_id": s_id, "giornata": num_g_sch,
                                        "schedina_url": url_img, "pronostici_json": {}
                                    }).execute()
                                    caricate += 1
                                except Exception as e:
                                    st.error(f"Errore ID {s_id}: {e}")
                        if caricate > 0:
                            st.toast(f"Salvate {caricate} schedine!", icon="🎉")
                            time.sleep(1.2)
                            st.rerun()
            else:
                st.info("Inserisci prima le squadre.")
                    
        with tab4:
            st.write("### Inserisci o Modifica Punti")
            if squadre:
                with st.form("add_p_multi"):
                    g_pts = st.selectbox("Giornata Punti", lista_giornate_etichette, index=giornata_idx, key="g_pts_multi")
                    num_g_pts = int(g_pts.split()[1])
                    punti_inseriti = {s['id']: st.number_input(f"{s['nome_squadra']}", min_value=0, step=1, key=f"pts_{s['id']}") for s in squadre}
                    
                    c_f1, c_f2 = st.columns(2)
                    salva_punti = c_f1.form_submit_button("Aggiorna Punti")
                    azzera_giornata = c_f2.form_submit_button("🗑️ Azzera Giornata")
                    
                    if salva_punti:
                        for s_id, p in punti_inseriti.items():
                            supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", num_g_pts).execute()
                            if p >= 0:
                                supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": p, "giornata": num_g_pts}).execute()
                        st.toast("Punti aggiornati!", icon="✅")
                        time.sleep(1.0)
                        st.rerun()
                        
                    if azzera_giornata:
                        supabase.table("risultati").delete().eq("giornata", num_g_pts).execute()
                        st.toast(f"Giornata {num_g_pts} azzerata!", icon="⚠️")
                        time.sleep(1.0)
                        st.rerun()

        with tab5:
            st.write("### Gestione ed Eliminazione")
            g_del = st.selectbox("Giornata", lista_giornate_etichette, index=giornata_idx, key="g_del_sch")
            num_g_del = int(g_del.split()[1])
            if st.button("Elimina Squadre o Dati"):
                pass

# --- INTERFACCIA PRINCIPALE ---
st.title("⚽ FantaBet Serie A Pro")

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
        for pos, item in enumerate(classifica, 1):
            c_class = "gold" if pos == 1 else "silver" if pos == 2 else "bronze" if pos == 3 else ""
            badge_pos = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"{pos}°"
            logo_html = f"<img src='{item['logo']}' style='width:32px; height:32px; border-radius:50%; object-fit:cover; margin-right:12px;' />" if item['logo'] else "⚽ "
            st.markdown(f"""<div class="card {c_class}"><div style="display:flex; align-items:center;">
                        <span style="font-weight:bold; width:38px; font-size:1.1em;">{badge_pos}</span>
                        {logo_html}
                        <span style="flex-grow:1; margin-left:5px; font-weight:bold; font-size:1.1em;">{item['nome']}</span>
                        <span style="font-weight:bold; color:#4CAF50; font-size:1.1em;">{item['punti']} pts</span></div></div>""", unsafe_allow_html=True)

elif st.session_state.current_page == "Schedine":
    st.title("📅 Archivio Schedine (Galleria)")
    giornata_scelta = st.selectbox("Seleziona Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
    num_g = int(giornata_scelta.split(" ")[1])
    try:
        schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []
        schedine_dict = {sch['squadra_id']: sch['schedina_url'] for sch in schedine}
        if squadre:
            cols = st.columns(3)
            for idx, s in enumerate(squadre):
                with cols[idx % 3]:
                    st.markdown(f"<div class='grid-card'><b>{s['nome_squadra']}</b>", unsafe_allow_html=True)
                    url = schedine_dict.get(s['id'])
                    if url: st.image(url, use_container_width=True)
                    else: st.caption("Nessuna schedina.")
                    st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Errore: {e}")
