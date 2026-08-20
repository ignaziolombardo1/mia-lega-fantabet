def calcola_risultati_da_foto_o_dati(giornata, supabase_client):
    try:
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}."
        
        risultati_reali = ottieni_risultati_reali_giornata(giornata) 
        
        report = []
        for s in schedine:
            pronostici_squadra = s.get('pronostici_json', {}) or {}
            
            punti_ottenuti = 0
            for i, risultato_reale in enumerate(risultati_reali):
                chiave_partita = f"partita_{i+1}"
                if pronostici_squadra.get(chiave_partita) == risultato_reale:
                    punti_ottenuti += 1
            
            punti_ottenuti = min(punti_ottenuti, 10)
            
            # PRIMA ELIMINHIAMO IL VECCHIO PUNTEGGIO PER QUESTA SQUADRA/GIORNATA
            supabase_client.table("risultati").delete().eq("squadra_id", s['squadra_id']).eq("giornata", giornata).execute()
            
            # POI INSERIAMO IL NUOVO PUNTEGGIO (da 0 a 10)
            supabase_client.table("risultati").insert({
                "squadra_id": s['squadra_id'], 
                "giornata": giornata, 
                "punteggio": punti_ottenuti
            }).execute()
            
            report.append(f"Squadra ID {s['squadra_id']}: {punti_ottenuti}/10 punti corretti")
        
        return True, "\n".join(report)
        
    except Exception as e:
        return False, f"Errore nel calcolo dei punti: {str(e)}"

def ottieni_risultati_reali_giornata(giornata):
    # Restituisce i 10 risultati reali (es. '1', 'X', '2')
    return ['1', 'X', '2', '1', '1', '2', 'X', '1', '2', 'X']
