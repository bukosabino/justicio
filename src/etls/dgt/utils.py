from datetime import datetime, timedelta

# POST request data to do the search in DGT documents
SEARCH_POST = {
    'type1': 'on',
    'type2': 'on',
    'NMCMP_1': 'NUM-CONSULTA',
    'VLCMP_1': '',
    'OPCMP_1': '.Y',
    'NMCMP_2': 'FECHA-SALIDA',
    'VLCMP_2': '', 
    'dateIni_2': '', 
    'dateEnd_2': '',
    'OPCMP_2': '.Y',
    'NMCMP_3': 'NORMATIVA',
    'VLCMP_3': '',
    'OPCMP_3': '.Y',
    'NMCMP_4': 'CUESTION-PLANTEADA',
    'VLCMP_4': '',
    'OPCMP_4': '.Y',
    'NMCMP_5': 'DESCRIPCION-HECHOS',
    'VLCMP_5': '',
    'OPCMP_5': '.Y',
    'NMCMP_6': 'FreeText',
    'VLCMP_6': '',
    'OPCMP_6': '.Y',
    'NMCMP_7': 'CRITERIO',
    'cmpOrder': 'NUM-CONSULTA',
    'dirOrder': '0',
    'auto': '',
    'tab': '2',
    'page': '1'
}


# POST request explore data in DGT search
DOC_POST = {
    'doc': '', # doc_id
    'tab': ''
}

# HTTP headers from request
HEADERS = {
    'Referer': 'https://petete.tributos.hacienda.gob.es/consultas',
    'X-Requested-With': 'XMLHttpRequest',
}

# Target classes for extracting text
#  ["NUM-CONSULTA", "ORGANO", "FECHA-SALIDA", "NORMATIVA", "DESCRIPCION-HECHOS", 
#   "CUESTION-PLANTEADA", "CONTESTACION-COMPL"]  
TARGET_CLASSES = ["NORMATIVA", "DESCRIPCION-HECHOS", "CUESTION-PLANTEADA", "CONTESTACION-COMPL"]

def get_previous_month_dates(t_date=None):
    """
    Get the start date and end date of the previous month.
    """
    if t_date == None:
        t_date = datetime.now()
    first_day_previous_month = datetime(t_date.year, t_date.month, 1) - timedelta(days=1)
    first_day_previous_month = datetime(first_day_previous_month.year, first_day_previous_month.month, 1)
    last_day_previous_month = datetime(t_date.year, t_date.month, 1) - timedelta(days=1)
    
    return first_day_previous_month, last_day_previous_month


