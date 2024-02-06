import typing as tp
import logging as lg
import re
from src.initialize import initialize_logging

BOCM_PREFIX = "https://www.bocm.es"


initialize_logging()


def _get_url_from_cve(cve: str) -> str:
    return f"{BOCM_PREFIX}/{cve.lower()}"


# Metadata from head tags
def metadata_from_head_tags(soup) -> tp.List[str]:
    # extract cve from meta[name="TituloGSA"]
    cve = soup.select_one('meta[name="TituloGSA"]')["content"]
    fecha = cve.split("-")[1:2][0]
    fecha_publicacion = f'{fecha[:4]}-{fecha[4:6]}-{fecha[6:8]}'

    html_link = soup.select_one('meta[property="og:url"]')["content"]

    return [fecha_publicacion, cve, html_link]


# Metadata from document header
def metadata_from_doc(soup, seccion: str, cve: str) -> tp.List[str]:
    logger = lg.getLogger(metadata_from_doc.__name__)

    # Set defaults
    apartado, tipo, anunciante, organo, rango = ["", "", "", "", ""]

    # get headers
    paras = [f.get_text().strip().upper() for f in soup.select("#cabeceras p")][:3]

    # Metadata from article description
    desc_attempt = soup.select_one('meta[name="description"]')
    if (desc_attempt is not None):
        desc = desc_attempt["content"]
    else:
        desc = ''
    num_art = re.sub(r"BOCM-\d{8}-(\d{1,3})", r"\1", cve)

    try:
        if seccion == "1":
            subseccion_letter = ["A", "B", "C", "D"][int(seccion) - 1]
            subseccion_name = paras[0]
            organo = paras[2]
            # Some articles don't have filled description needed for rango field extraction
            if len(desc) > 10:
                rango = re.sub(r"^(\b[^\s]+\b)(.*)", r"\1", desc.split(num_art)[1], flags=re.ASCII).upper()
        if seccion == "2":
            subseccion_name = "DISPOSICIONES Y ANUNCIOS DEL ESTADO"
            organo = paras[0]
        if seccion == "3":
            paras_num = len(paras)
            subseccion_name = "ADMINISTRACIÓN LOCAL AYUNTAMIENTOS"
            if paras_num == 3:
                apartado, organo = paras[1:3]
            elif paras_num == 2:
                organo, apartado = paras[0:2]
            else:
                apartado = "MANCOMUNIDADES"
                organo = paras[0]

        if seccion == "4":
            subseccion_name = "ADMINISTRACIÓN DE JUSTICIA"
        if seccion == "5":
            subseccion_name = "OTROS ANUNCIOS"
            anunciante = paras[0]

    except:
        logger.error("Problem on section clasification for [%s]", cve)
        logger.error("Please review [%s]", _get_url_from_cve(cve))

    return [subseccion_name, apartado, tipo, organo, anunciante, rango]


def metadata_from_doc_header(soup) -> tp.List[str]:
    logger = lg.getLogger(metadata_from_doc_header.__name__)

    numero_oficial = soup.select_one(".cabecera_popup h1 strong").get_text().split("-")[1].strip().split(" ")[1].strip()
    s_field_a, cve_a, pags_a, *permalink = [str.get_text().split(":") for str in soup.select("#titulo_cabecera h2")]
    seccion_normalizada = s_field_a[0].strip().split(" ")[1]
    paginas = pags_a[1].strip()  # Should I convert to int??
    pdf_link = soup.select_one("#titulo_cabecera a")["href"]

    return [numero_oficial, seccion_normalizada, paginas, pdf_link]


def select_section_from_id(soup, filtered_section: str) -> tp.List[str]:
    logger = lg.getLogger(select_section_from_id.__name__)

    section_links = []
    section, subsection = filtered_section.split("-")
    section_container = soup.select_one(f'div[id*="secciones-seccion_{section}"]')
    if section_container is not None:
        if len(subsection) == 1:
            if section == "1":
                header_selector = ".view-grouping-header h3"
                content_selector = ".view-grouping-content"
            else:
                header_selector = ".view-content h3"
                content_selector = ".view-content"
            subsections = section_container.select(".view-grouping")
            for group in subsections:
                title = group.select_one(header_selector).text
                subsection_fix = f"{subsection}\)"
                if re.search(subsection_fix, title):
                    links = [f'{BOCM_PREFIX}{a["href"]}' for a in group.select(f'{content_selector} a[href*="bocm-"]')]
                    section_links += links
        else:
            links = [f'{BOCM_PREFIX}{a["href"]}' for a in section_container.select('a[href*="bocm-"]')]
            section_links += links
    logger.info(f"Captured {len(section_links)} docs from section [{section}]")
    return section_links


def filter_links_by_section(soup, sections_filter_list: tp.List[str]) -> tp.List[str]:
    logger = lg.getLogger(filter_links_by_section.__name__)

    selected = []
    for section_id in sections_filter_list:
        links = select_section_from_id(soup, section_id)
        selected += links

    logger.info("Retrieved [%s] links for current day", len(selected))
    return selected


def clean_text(text: str) -> str:
    cleaned = re.sub(r"(\xa0|\t+|\n+)", " ", text, flags=re.MULTILINE)
    return cleaned
