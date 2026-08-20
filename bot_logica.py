def calcola_risultati_da_foto_o_dati(giornata, supabase_client):
    try:
        # 1. Recupera le schedine salvate per questa giornata
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}."
        
        # 2. SIMULAZIONE / RECUPERO RISULTATI REALI DELLE 10 PARTITE
        # Qui dovresti recuperare i risultati reali (es. ['1', 'X', '2', '1', '1', '2', 'X', '1', '2', 'X'])
        # Per ora usiamo una funzione di esempio o recuperiamo i dati dal DB se li salvi altrove.
        risultati_reali = ottieni_risultati_reali_giornata(giornata) 
        
        report = []
        for s in schedine:
            # Supponiamo che nella schedina ci sia un campo JSON o un dizionario con i 10 pronostici della squadra:
            # es. s['pronostici_json'] = {'partita_1': '1', 'partita_2': 'X', ...}
            pronostici_squadra = s.get('pronostici_json', {})
            
            punti_ottenuti = 0
            
            # 3. Confronto logico (da 0 a 10 punti)
            for i, risultato_reale in enumerate(risultati_reali):
                # Controlla se il pronostico della squadra per la partita i-esima corrisponde a quello reale
                chiave_partita = f"partita_{i+1}"
                if pronostici_squadra.get(chiave_partita) == risultato_reale:
                    punti_ottenuti += 1  # +1 punto per ogni pronostico corretto
            
            # Assicuriamoci che non superi mai 10 (o il numero massimo di partite)
            punti_ottenuti = min(punti_ottenuti, 10)
            
            # 4. Salva il punteggio calcolato (da 0 a 10) nel database Supabase
            supabase_client.table("risultati").upsert({
                "squadra_id": s['squadra_id'], 
                "giornata": giornata, 
                "punteggio": punti_ottenuti
            }, on_conflict="squadra_id,giornata").execute()
            
            report.append(f"Squadra ID {s['squadra_id']}: {punti_ottenuti}/10 punti corretti")
        
        return True, "\n".join(report)
        
    except Exception as e:
        return False, f"Errore nel calcolo dei punti: {str(e)}"

def ottieni_risultati_reali_giornata(giornata):
    # Funzione di supporto: qui collegherai la tua API o la logica per estrarre i 10 segni esatti (1, X, 2)
    # Esempio fittizio di 10 risultati:
    return ['1', 'X', '2', '1', '1', '2', 'X', '1', '2', 'X']
