import os
from openai import OpenAI

def calcola_risultati_da_foto_o_dati(giornata, supabase_client):
    try:
        # 1. Recupera le schedine salvate per questa giornata
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}."
        
        # 2. Definiamo i risultati reali ufficiali della giornata
        risultati_reali = ottieni_risultati_reali_giornata(giornata)
        
        # Inizializziamo il client OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return False, "Chiave OpenAI non trovata nelle variabili d'ambiente o nei secrets."
            
        client = OpenAI(api_key=api_key)
        
        report = []
        for s in schedine:
            schedina_url = s.get('schedina_url')
            if not schedina_url:
                continue
            
            try:
                # 3. Chiamata a GPT-4o-mini Vision per leggere gli eventi
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "Analizza questa schedina di pronostici calcistici. Leggi tutti gli eventi presenti nell'immagine. Per ogni evento, estrai il pronostico effettuato (può essere '1', 'X', '2'). Restituisci la risposta ESCLUSIVAMENTE come una lista Python di stringhe, ad esempio: ['1', 'X', '2', '1']. Non aggiungere altro testo, nessun blocco di codice markdown (come ```python), solo la lista."
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
                # Pulisce eventuali formattazioni markdown se l'IA le inserisce per errore
                risposta_ai = risposta_ai.replace("```python", "").replace("```", "").strip()
                
                pronostici_letti = eval(risposta_ai)
                if not isinstance(pronostici_letti, list):
                    pronostici_letti = []
            except Exception as ex:
                report.append(f"Squadra ID {s['squadra_id']}: Errore lettura immagine ({str(ex)})")
                continue
            
            # 4. Confronto dinamico tra pronostici letti e risultati reali
            punti_ottenuti = 0
            totale_eventi_letti = len(pronostici_letti)
            
            for i in range(min(len(pronostici_letti), len(risultati_reali))):
                if str(pronostici_letti[i]).strip().upper() == str(risultati_reali[i]).strip().upper():
                    punti_ottenuti += 1
            
            # 5. Salva il punteggio pulendo prima il vecchio record
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

def ottieni_risultati_reali_giornata(giornata):
    # Risultati reali di riscontro per i test (4 elementi per i tuoi test attuali)
    return ['1', 'X', '2', '1']
    
