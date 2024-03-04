import re 
   
def mes_a_numero(mes):
        meses = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        return meses.get(mes.lower(), 0)
    
def clean_text(text: str) -> str:
    cleaned = re.sub(r"(\xa0|\t+|\n+)", " ", text, flags=re.MULTILINE)
    return cleaned        