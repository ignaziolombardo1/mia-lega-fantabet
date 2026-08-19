import streamlit as st
from supabase import create_client
import uuid

# Configurazione Supabase
SUPABASE_URL = "https://jynplanvtoytucanxsbn.supabase.co"
SUPABASE_KEY = "sb_publishable_kiM3YkFbdFcyLxB8a3Ok6w_rqGhdKHY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gestione Lega FantaBet", page_icon="⚽")
st.title("⚽ Gestione Lega FantaBet")

menu = st.sidebar.selectbox("Navigazione", ["Classifica", "Admin: Gestione Squadre", "Admin: Inserisci Punteggi"])

# --- 1. CLASSIFICA ---
if menu == "Classifica":
    st.header("Classifica Generale FantaBet")
    risultati = supabase.table("risultati").select("*").execute().data
    squadre = supabase.table("squadre").select("*").execute().data
    
    if squadre:
        # Ordiniamo le squadre per punteggio totale
        classifica_data = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica_data.append({'nome': s['nome_squadra'], 'punti': punti, 'logo': s.get('logo_url')})
        
        classifica_data.sort(key=lambda x: x['punti'], reverse=True)
        
        for item in classifica_data:
            col1, col2 = st.columns([1, 4])
            if item['logo']:
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/leghe-fantabet/{item['logo']}"
                col1.image(public_url, width=60)
            col2.write(f"### {item['nome']}: {item['punti']} punti")
    else:
        st.info("Nessuna squadra ancora registrata nella FantaBet.")

# --- 2. ADMIN: GESTIONE SQUADRE ---
elif menu == "Admin: Gestione Squadre":
    st.header("Registra Squadra FantaBet")
    with st.form("form_squadra"):
        nome_squadra = st.text_input("Nome Squadra")
        presidente = st.text_input("Nome Presidente")
        vicepresidente = st.text_input("Nome Vicepresidente")
        logo = st.file_uploader("Carica Logo Squadra", type=['jpg', 'png'])
        
        if st.form_submit_button("Salva Squadra"):
            logo_name = None
            if logo:
                logo_name = f"{uuid.uuid4()}.png"
                supabase.storage.from_("leghe-fantabet").upload(logo_name, logo.getvalue())
            
            supabase.table("squadre").insert({
                "nome_squadra": nome_squadra,
                "presidente": presidente,
                "vicepresidente": vicepresidente,
                "logo_url": logo_name
            }).execute()
            st.success(f"Squadra '{nome_squadra}' aggiunta alla FantaBet!")

# --- 3. ADMIN: INSERISCI PUNTEGGI ---
elif menu == "Admin: Inserisci Punteggi":
    st.header("Inserisci Punteggi FantaBet")
    squadre_res = supabase.table("squadre").select("id, nome_squadra").execute().data
    
    if squadre_res:
        squadra_dict = {s["nome_squadra"]: s["id"] for s in squadre_res}
        with st.form("form_punti"):
            squadra_scelta = st.selectbox("Seleziona Squadra", list(squadra_dict.keys()))
            giornata = st.number_input("Giornata", min_value=1, step=1)
            punteggio = st.number_input("Punteggio", min_value=0, step=1, format="%d")
            
            if st.form_submit_button("Salva Punteggio FantaBet"):
                supabase.table("risultati").insert({
                    "squadra_id": squadra_dict[squadra_scelta],
                    "giornata": giornata,
                    "punteggio": punteggio
                }).execute()
                st.success("Punteggio registrato!")
