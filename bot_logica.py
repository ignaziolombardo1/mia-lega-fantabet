import requests

# Inserisci qui la tua chiave API (quella fornita in precedenza)
API_KEY = "4dcfdf02c9f757fdaa4f514a4cbb7cf3"
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}

def calcola_risultati_giornata(giornata, supabase_client):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"league": "135", "season": "2026", "round": f"Regular Season - {giornata}"}
    
    try:
        response = requests.get(url, headers=HEADERS, params=querystring).json()
        risultati_reali = {}
        
        for match in response.get('response', []):
            home = match['teams']['home']['name']
            away = match['teams']['away']['name']
            h_score = match['goals']['home']
            a_score = match['goals']['away']
            
            if h_score is None or a_score is None:
                continue
                
            # Calcolo del segno 1X2
            if h_score > a_score: segno = "1"
            elif a_score > h_score: segno = "2"
            else: segno = "X"
            
            risultati_reali[f"{home} - {away}"] = segno
        
        if not risultati_reali:
            return False, "Nessun risultato ufficiale trovato per questa giornata (le partite potrebbero non essere ancora iniziate)."
        
        # Recupera le schedine degli utenti dal database
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        
        if not schedine:
            return False, "Nessuna schedina trovata per questa giornata nel database."
        
        for sch in schedine:
            punti = 0
            pronostici = sch['pronostici_json']
            for partita, segno_utente in pronostici.items():
                if risultati_reali.get(partita) == segno_utente:
                    punti += 1
            
            # Aggiorna la tabella dei risultati su Supabase
            supabase_client.table("risultati").upsert({
                "squadra_id": sch['squadra_id'],
                "punteggio": punti,
                "giornata": giornata
            }, on_conflict="squadra_id,giornata").execute()
            
        return True, "Classifica aggiornata con successo dal Bot!"
    except Exception as e:
        return False, f"Errore di connessione o elaborazione: {str(e)}"
