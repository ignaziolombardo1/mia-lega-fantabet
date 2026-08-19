# Aggiungi questo in alto nel file app.py, subito dopo gli import
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://raw.githubusercontent.com/tuo-utente/tuo-repo/main/background.jpg");
        background-size: cover;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 1. CLASSIFICA (Versione Bella) ---
if menu == "Classifica":
    st.header("🏆 Classifica Generale FantaBet")
    risultati = supabase.table("risultati").select("*").execute().data
    squadre = supabase.table("squadre").select("*").execute().data
    
    if squadre:
        classifica_data = []
        for s in squadre:
            punti = sum([int(r['punteggio']) for r in risultati if r['squadra_id'] == s['id']])
            classifica_data.append({
                'Logo': s.get('logo_url'), 
                'Squadra': s['nome_squadra'], 
                'Punti': punti
            })
        
        classifica_data.sort(key=lambda x: x['Punti'], reverse=True)
        
        # Trasformiamo in un DataFrame per una tabella bellissima
        import pandas as pd
        df = pd.DataFrame(classifica_data)
        
        # Mostriamo la tabella interattiva
        st.table(df)
    else:
        st.info("Nessuna squadra ancora registrata nella FantaBet.")
