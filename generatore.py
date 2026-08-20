from PIL import Image, ImageDraw, ImageFont
import io

def crea_immagine_schedina(nome_squadra, giornata, pronostici_dict):
    """
    nome_squadra: Stringa
    giornata: Int
    pronostici_dict: Dizionario, es: {"Inter-Juve": "1", "Roma-Lazio": "X"}
    """
    # Creiamo un'immagine con fondo scuro (stile FantaBet)
    width, height = 400, 500
    img = Image.new('RGB', (width, height), color='#0E1117')
    draw = ImageDraw.Draw(img)
    
    # Carichiamo un font (usiamo quello di default)
    try:
        font_titolo = ImageFont.truetype("arial.ttf", 30)
        font_testo = ImageFont.truetype("arial.ttf", 20)
    except:
        font_titolo = ImageFont.load_default()
        font_testo = ImageFont.load_default()

    # Disegniamo il titolo
    draw.text((20, 20), f"Schedina {nome_squadra}", fill="#4CAF50", font=font_titolo)
    draw.text((20, 60), f"Giornata n. {giornata}", fill="white", font=font_testo)
    
    # Disegniamo le partite
    y = 100
    for partita, segno in pronostici_dict.items():
        draw.text((20, y), f"{partita}:  {segno}", fill="white", font=font_testo)
        y += 40
        
    # Salva in memoria
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
