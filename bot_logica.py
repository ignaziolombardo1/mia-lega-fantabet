import requests
from supabase import create_client

# Usa la tua chiave reale qui
API_KEY = "4dcfdf02c9f757fdaa4f514a4cbb7cf3"
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}

def calcola_risultati_giornata(giornata, supabase_client):
    # 1. Recupera risultati reali dall'API
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    # Nota: L'ID 135 è la Serie A. Assicurati che la stagione sia quella corretta (es 2026)
    querystring = {"league": "135", "season": "2026", "round": f"Regular Season - {giornata}"}
    
    try:
        response = requests.get(url, headers=HEADERS, params=querystring).json()
        risultati_reali = {}
        for match in response['response']:
            home = match['teams']['home']['name']
            away = match['teams']['away']['name']
            h_score = match['goals']['home']
            a_score = match['goals']['away']
            
            # Segno 1X2
            if h_score > a_score: segno = "1"
            elif a_score > h_score: segno = "2"
            else: segno = "X"
            risultati_reali[f"{home} - {away}"] = segno
        
        # 2. Confronta con le schedine nel DB
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        
        for sch in schedine:
            punti = 0
            pronostici = sch['pronostici_json']
            for partita, segno_utente in pronostici.items():
                if risultati_reali.get(partita) == segno_utente:
                    punti += 1
            
            # 3. Aggiorna la classifica
            supabase_client.table("risultati").upsert({
                "squadra_id": sch['squadra_id'],
                "punteggio": punti,
                "giornata": giornata
            }).execute()
        return True, "Classifica aggiornata con successo!"
    except Exception as e:
        return False, str(e)
