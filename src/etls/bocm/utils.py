import typing as tp
import logging as lg
import re
from src.initialize import initialize_logging

BOCM_PREFIX = 'https://www.bocm.es'

SECTIONS = {
    'i. c' : 1,
    'ii. ' : 2,
    'iii.' : 3,
    'iv. ' : 4,
    'v. o' : 5
}
APARTADOS = {
    "a)" : "A",
    "b)" : "B",
    "c)" : "C",
    "d)" : "D"
}
ORIGEN_LEGISLATIVO = {
    1 : "REGIONAL",
    2 : "ESTATAL",
    3 : "MUNICIPAL",
    4 : "JUSTICIA",
    5 : "CCAA"
}

initialize_logging()

def _get_url_from_cve(cve: str) -> str:
    return f'{BOCM_PREFIX}/{cve.lower()}'


# Metadata from head tags
def metadata_from_head_tags(soup) -> tp.List[str]:    
    fecha_publicacion = soup.select_one('meta[property="article:published_time"]')['content'].split("T")[0]
    cve = soup.select_one('meta[property="og:title"]')['content']
    html_link = soup.select_one('meta[property="og:url"]')['content']

    return [fecha_publicacion,cve,html_link]


# Metadata from document header
def metadata_from_doc_header(soup, cve: str) -> tp.List[str]:
    logger = lg.getLogger(metadata_from_doc_header.__name__)
    
    seccion,*paras = [f.get_text().strip().lower() for f in soup.select('#cabeceras #cabeceras p')] 
    current_seccion = SECTIONS[seccion[0:4]]

    try:
        if (current_seccion == 1 and len(paras) == 3):
            apartado,r,organo = paras
        elif (current_seccion == 3 and len(paras) == 3):
            otro,apartado,organo = paras
        elif (current_seccion == 3 and len(paras) == 2):
            organo,apartado = paras
            rango = ''
        elif (current_seccion == 3 and len(paras) == 1):
            organo = paras[0]
            rango = ''
            apartado = ''
        elif (current_seccion == 4):
            apartado = paras[0]
            organo = ''
        else:
            organo,apartado = paras
        
        # TODO: section 5 will have value
        anunciante = ''

    except:
        logger.error('Problem on section clasification for [%s]', cve)
        logger.error('Please review [%s]',_get_url_from_cve(cve))

    # Fix some inconsistencies of each section regarding rango field

    # Metadata from article description
    desc = soup.select_one('meta[name="description"]')["content"]
    num_art = re.sub(r'BOCM-\d{8}-(\d{1,3})', r'\1' ,cve)
    
    # Some articles don't have filled description needed for rango field extraction
    if (len(desc) > 10 and current_seccion == 1):
        # Using ASCII, doesn't work with re.UNICODE
        rango = re.sub(r'^(\b[^\s]+\b)(.*)', r'\1', desc.split(num_art)[1], flags=re.ASCII).upper()
    else:
        rango = ''

    if (current_seccion != 4):
        departamento = organo.upper()
    else:
        departamento = ''


    return [departamento,seccion,apartado,rango,organo,anunciante]


# Desc doc header
def metadata_from_doc_desc_header(soup) -> tp.List[str]:
    numero_oficial = soup.select_one('.cabecera_popup h1 strong').get_text().split("-")[1].strip().split(" ")[1].strip()
    s_field_a, cve_a, pags_a = [str.get_text().split(":") for str in soup.select('#titulo_cabecera h2')]
    seccion_full = s_field_a[0].strip().split(' ')[1]
    paginas = pags_a[1].strip()  # Should I convert to int??
    pdf_link = soup.select_one('#titulo_cabecera a')['href']

    return [numero_oficial,seccion_full,paginas,pdf_link]

# Custom from BOCM

def _normalize_section_from_title(title) -> str:
    words_arr = re.sub(r'\</?strong\>',"",title).lower().replace(":", "|").split('|')
    arr = list(map(lambda s: s.strip(), words_arr))
    normalized = f'{SECTIONS[arr[1][0:4]]}-'
    if (len(arr) > 2 and normalized == '1-'):
        normalized = f'{normalized}-{APARTADOS[arr[2][0:2]]}'
    
    return normalized 

def filter_links_by_section(soup,sections_filter_list: tp.List[str]) -> tp.List[str]:
    logger = lg.getLogger(filter_links_by_section.__name__)

    sections = soup.select('div[id*="secciones-seccion"]')
    selected = []
    for section in sections:
        section_num = int(section["id"][-1])
        if (section_num == 1):
            header_selector = '.view-grouping-header h3'
            content_selector = '.view-grouping-content'
        else:
            header_selector = '.view-content h3'
            content_selector = '.view-content'
        title_text = section.select_one(header_selector).text
        normalized_section = _normalize_section_from_title(title_text)
        if (normalized_section in sections_filter_list):
            links = [f'{BOCM_PREFIX}{a["href"]}' for a in section.select('a[href*="bocm-"]')] 
            selected += links
    
    logger.info("Retrieved [%s] links for current day", len(selected))
    return selected

def get_origen_legislativo_by_seccion(seccion: str) -> str:
    return ORIGEN_LEGISLATIVO[SECTIONS[seccion[0:4]]]