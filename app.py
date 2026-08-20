import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import time
import os
from openai import OpenAI

# =========================================================
# CONFIGURAZIONE INIZIALE E STILE
# =========================================================

SUPABASE_URL = "https://rkomejsxqfvdhnyxzqkt.supabase.co"
SUPABASE_KEY = "sb_publishable_OCL6sqOZDuP_2nONpV8mXg_szn04DQT"
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
    .grid-card { background: rgba(25, 25, 30, 0.85); padding: 15px; border-radius: 12px; border: 1px solid #333; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# FUNZIONI DI SUPPORTO E LOGICA DEL BOT
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

def calcola_risultati_da_foto_o_dati(giornata, supabase_client):
    try:
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}."
        
        risultati_reali = ['1', 'X', '2', '1']
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("OPENAI_API_KEY")
            except Exception:
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
                prompt_testo = "Analizza questa schedina. Leggi tutti gli eventi presenti. Estrai i pronostici (1, X, 2). Restituisci la risposta ESCLUSIVAMENTE come una lista Python di stringhe, ad esempio: ['1', 'X', '2', '1']. Nient'altro."
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt_testo
                        }
                    ],
                    max_tokens=200
                )
                
                risposta_ai = response.choices[0].message.content.strip()
                risposta_ai = risposta_ai.replace("```python", "").replace("
