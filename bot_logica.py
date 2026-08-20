import os
from openai import OpenAI

def calcola_risultati_da_foto_o_dati(giornata, supabase_client):
    try:
        # 1. Recupera le schedine salvate per questa giornata
        schedine = supabase_client.table("schedine").select("*").eq("giornata", giornata).execute().data
        if not schedine:
            return False, f"Nessuna schedina trovata per la Giornata {giornata}."
        
        # 2. Definiamo i risultati reali ufficiali della giornata 
        # (es. se nella foto ci sono 4 eventi, qui ci saranno i 4 segni reali corrispondenti)
        risultati_reali = ottieni_risultati_reali_giornata(giornata)
        
        # Inizializziamo il client OpenAI (preleverà la chiave dalle variabili d'ambiente o secrets)
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        report = []
        for s in schedine:
            schedina_url = s.get('schedina_url')
            if not schedina_url:
                continue
            
            # 3. Chiamata a GPT-4o Vision per leggere quanti e quali eventi ci sono
            # Chiediamo di restituire i pronostici sotto forma di lista pulita (es. ["1", "X", "2", "1"])
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini", # Puoi usare gpt-4o o gpt-4o-mini
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "Analizza questa schedina di pronostici calcistici. Leggi tutti gli eventi presenti nell'immagine (qualsiasi sia il loro numero). Per ogni evento, estrai il pronostico effettuato (può essere '1', 'X', '2' o doppie/triple se presenti, ma considera il segno principale). Restituisci la risposta ESCLUSIVAMENTE come una lista Python di stringhe, ad esempio: ['1', 'X', '2', '1']. Non aggiungere altro testo."
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
                # Converte la stringa della risposta in una lista Python reale
                pronostici_letti = eval(risposta_ai)
                if not isinstance(pronostici_letti, list):
                    pronostici_letti = []
            except Exception as ex:
                report.append(f"Squadra ID {s['squadra_id']}: Errore lettura immagine ({str(ex)})")
                continue
            
            # 4. Confronto dinamico: conta quanti pronostici coincidono con i risultati reali
            punti_ottenuti = 0
            totale_eventi_letti = len(pronostici_letti)
            
            for i in range(min(len(pronostici_letti), len(risultati_reali))):
                if str(pronostici_letti[i]).strip().upper() == str(risultati_reali[i]).strip().upper():
                    punti_ottenuti += 1
            
            # 5. Salva il punteggio corretto nel database Supabase
            supabase_client.table("risultati").delete().eq("squadra_id", s['squadra_id']).eq("giornata", giornata).execute()
            
            supabase_client.table("risultati").insert({
                "squadra_id": s['squadra_id'], 
                "giornata": giornata, 
                "punteggio": punti_ottenuti
            }).execute()
            
            report.append(f"Squadra ID {s['squadra_id']}: {punti_ottenuti}/{totale_eventi_letti} punti corretti (Letti: {pronostici_letti})")
        
        return True, "\n".join(report)
        
    except Exception as e:
        return False, f"Errore generale nel bot: {str(e)}"

def ottieni_risultati_reali_giornata(giornata):
    # Inserisci qui i risultati reali di riscontro per i test (es. 4 risultati se la schedina di test ne ha 4)
    return ['1', 'X', '2', '1']
