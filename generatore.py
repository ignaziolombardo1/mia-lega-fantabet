from PIL import Image, ImageDraw, ImageFont
import io

def crea_immagine_schedina(nome_squadra, giornata, pronostici_dict):
    """
    Crea l'immagine grafica della schedina con le partite e i pronostici.
    """
    width, height = 450, 600
    img = Image.new('RGB', (width, height), color='#0E1117')
    draw = ImageDraw.Draw(img)
    
    try:
        font_titolo = ImageFont.truetype("arial.ttf", 22)
        font_testo = ImageFont.truetype("arial.ttf", 16)
    except:
        font_titolo = ImageFont.load_default()
        font_testo = ImageFont.load_default()

    # Intestazione
    draw.text((20, 20), f"SCHEDINA: {nome_squadra}", fill="#4CAF50", font=font_titolo)
    draw.text((20, 50), f"Giornata n. {giornata}", fill="white", font=font_testo)
    
    # Linea divisoria
    draw.line([(20, 80), (430, 80)], fill="#333333", width=2)
    
    # Disegna le partite e i pronostici
    y = 100
    for partita, segno in pronostici_dict.items():
        draw.text((20, y), f"{partita}", fill="white", font=font_testo)
        draw.text((380, y), f"{segno}", fill="#FFD700", font=font_testo)
        y += 40
        
    # Salva in memoria
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
