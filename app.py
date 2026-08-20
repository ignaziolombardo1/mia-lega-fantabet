import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time
import os
import json
from openai import OpenAI

# =========================================================
# CONFIGURAZIONE E SUPABASE
# =========================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "fantabet"

st.set_page_config(page_title="FantaBet Serie A Pro", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    .card { background: rgba(30,30,30,0.85); padding: 16px; border-radius: 14px; margin-bottom: 12px; border-left: 5px solid #4CAF50; color: #FAFAFA; }
    .gold { border-left: 5px solid #FFD700 !important; }
    .silver { border-left: 5px solid #C0C0C0 !important; }
    .bronze { border-left: 5px solid #CD7F32 !important; }
    .grid-card { background: rgba(25, 25, 30, 0.85); padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; color: #FAFAFA; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# LOGICA BOT IA
# =========================================================

def analizza_schedine_ia(giornata, supabase_client):
    try:
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, "Nessuna schedina trovata.", {}
        
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        report = []
        risultati_calcolati = {}

        for s in schedine:
            url = s.get('schedina_url')
            if not url: continue
            
            try:
                prompt = f"""Analizza questa schedina della Giornata {giornata}. 
                Considera max 10 partite. Calcola autonomamente i punti realizzati in base ai risultati reali.
                Rispondi ESCLUSIVAMENTE in JSON: {{"punteggio_totale": 5}}"""
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": url}}]}],
                    response_format={"type": "json_object"}
                )
                
                punti = int(json.loads(response.choices[0].message.content).get("punteggio_totale", 0))
                risultati_calcolati[s['squadra_id']] = punti
                report.append(f"Squadra ID {s['squadra_id']}: {punti} punti")
            except:
                report.append(f"Squadra ID {s['squadra_id']}: Errore analisi.")
        
        return True, "\n".join(report), risultati_calcolati
    except Exception as e:
        return False, str(e), {}

# =========================================================
# FUNZIONI UTILI
# =========================================================

def get_giornata_corrente():
    inizio = datetime(2026, 8, 23).date()
    return max(1, min(38, ((datetime.now().date() - inizio).days // 7) + 1))

squadre = supabase.table("squadre").select("*").execute().data or []
giornata_idx = get_giornata_corrente() - 1

# =========================================================
# INTERFACCIA ADMIN
# =========================================================

with st.sidebar:
    if not st.session_state.get("admin", False):
        if st.text_input("Password Admin", type="password") == st.secrets.get("ADMIN_PASSWORD"):
            if st.button("Login"): st.session_state.admin = True; st.rerun()
    else:
        st.write("### 🤖 Bot IA")
        g_auto = st.selectbox("Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx)
        num_g = int(g_auto.split()[1])
        
        if st.button("🚀 Avvia Analisi"):
            with st.spinner("Analisi in corso..."):
                ok, msg, res = analizza_schedine_ia(num_g, supabase)
                if ok:
                    st.success("Analisi completata!")
                    st.text_area("Risultati:", msg)
                    st.session_state["ris_temp"] = res
                    st.session_state["g_temp"] = num_g
                else: st.error(msg)
        
        if "ris_temp" in st.session_state:
            if st.button("📥 Inserisci nella classifica", type="primary"):
                for s_id, pt in st.session_state["ris_temp"].items():
                    supabase.table("risultati").delete().eq("squadra_id", s_id).eq("giornata", st.session_state["g_temp"]).execute()
                    supabase.table("risultati").insert({"squadra_id": s_id, "punteggio": pt, "giornata": st.session_state["g_temp"]}).execute()
                st.toast("Punti inseriti!"); del st.session_state["ris_temp"]; st.rerun()

# =========================================================
# INTERFACCIA PRINCIPALE
# =========================================================

st.title("⚽ FantaBet Serie A Pro")
page = st.radio("Navigazione", ["Classifica", "Schedine"], horizontal=True)

if page == "Classifica":
    res = supabase.table("risultati").select("*").execute().data or []
    cl = []
    for s in squadre:
        punti = sum(int(r['punteggio']) for r in res if r['squadra_id'] == s['id'])
        cl.append({"nome": s['nome_squadra'], "punti": punti})
    
    for item in sorted(cl, key=lambda x: -x['punti']):
        st.markdown(f"<div class='card'>{item['nome']} - <b>{item['punti']} pts</b></div>", unsafe_allow_html=True)

else:
    st.title("📅 Archivio Schedine")
    num_g = int(st.selectbox("Giornata", [f"Giornata {i}" for i in range(1, 39)], index=giornata_idx).split()[1])
    schedine = supabase.table("schedine").select("*").eq("giornata", num_g).execute().data or []
    for s in squadre:
        sch = next((x for x in schedine if x['squadra_id'] == s['id']), None)
        st.markdown(f"<div class='grid-card'><b>{s['nome_squadra']}</b></div>", unsafe_allow_html=True)
        if sch: st.image(sch['schedina_url'])
