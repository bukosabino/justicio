import logging as lg
import tempfile
import typing as tp
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

from src.etls.bopz.utils import DATA_POST
from src.etls.bopz.metadata import BOPZMetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.initialize import initialize_logging

initialize_logging()

def _extract_span_text(row: BeautifulSoup, text_label: str) -> str:
    """
    Extracts the text of the next sibling for a span element that contains the specified text_label.
    
    :param row: The BeautifulSoup row element to search within.
    :param text_label: The text to search for within the span element.
    :return: The stripped text of the next sibling if found, otherwise an empty string.
    """
    span_element = row.find('span', string=lambda t: text_label in t)
    return span_element.next_sibling.strip() if span_element and span_element.next_sibling else None

def _extract_metadata(soup) -> tp.Dict:
    metadata_dict = {}
    
    # Metadatos
    if numero_registro := _extract_span_text(soup, 'Nº. Reg:'):
        metadata_dict["numero_oficial"] = numero_registro.split('/')[0]
        metadata_dict["titulo"] = f"BOPZ-{numero_registro.replace('/', '-')}"
    
    if departamento := _extract_span_text(soup, 'Publicador:'):
        metadata_dict["departamento"] = departamento
    
    if materia := _extract_span_text(soup, 'Materia'):
        metadata_dict["materia"] = [materia]
        
    if fecha_publicacion := _extract_span_text(soup, 'Fecha Pub:'):
        fecha_publicacion = datetime.strptime(fecha_publicacion, "%d/%m/%Y").strftime("%Y-%m-%d")
        metadata_dict["fecha_publicacion"] = fecha_publicacion
        metadata_dict["fecha_disposicion"] = fecha_publicacion
        metadata_dict["anio"] = str(datetime.strptime(fecha_publicacion, "%Y-%m-%d").year)
        metadata_dict["mes"] = str(datetime.strptime(fecha_publicacion, "%Y-%m-%d").month)
        metadata_dict["dia"] = str(datetime.strptime(fecha_publicacion, "%Y-%m-%d").day)
        
    href = soup.find('a', class_='adjunto')['href'][1:]
    metadata_dict["url_pdf"] = f"{'http://bop.dpz.es/BOPZ'}{href}"
    
    return metadata_dict

def _list_links_day(url: str, day_str: str) -> tp.List[BeautifulSoup]:
    """Get a list of documents listed in a BOPZ url day

    :param url: url base link. Example: 'http://bop.dpz.es/BOPZ/portalBuscarEdictos.do'
    :param day_str: str date to scrap
    :return: list of documents to explore (BeatifullSoup objects)
    """
    logger = lg.getLogger(_list_links_day.__name__)
    logger.info("Scrapping day: %s", day_str)
    DATA_POST['fechaPubInf'] = day_str
    DATA_POST['fechaPubSup'] = day_str
    response = requests.post(url, data=DATA_POST)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find all the rows in the response which correspond to published documents
    id_links = [
        id_link for id_link in soup.find_all('div', class_='row listadoEdictos')
        if (href := id_link.find('a', class_='adjunto').get('href', '')) 
        and 'UploadServlet?ruta=Boletines' in href 
        and href.endswith('.pdf')
    ]
    logger.info("Scrapped day successfully %s (%s BOPZ documents)", url, len(id_links))
    return id_links

class BOPZScrapper(BaseScrapper):    
    def download_day(self, day: date) -> tp.List[BOPZMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOPZ content for day %s", day)
        day_str = day.strftime('%d/%m/%Y')
        metadata_documents = []
        try:
            id_links = _list_links_day('http://bop.dpz.es/BOPZ/portalBuscarEdictos.do', day_str)
            for id_link in id_links:
                try:
                    onclick_div = id_link.find('div', onclick=True)
                    if onclick_div:
                        onclick_content = onclick_div['onclick']
                        start = onclick_content.find("'") + 1
                        end = onclick_content.find("'", start)
                        idEdicto = onclick_content[start:end]
                    url_document = f'http://bop.dpz.es/BOPZ/obtenerContenidoEdicto.do?idEdicto={idEdicto}'
                    metadata_doc = self.download_document(url_document, id_link)
                    metadata_documents.append(metadata_doc)
                except HTTPError:
                    logger.error(
                        "Not scrapped document %s on day %s", url_document, day_str
                    )
                except AttributeError:
                    logger.error(
                        "Not scrapped document %s on day %s", url_document, day_str
                    )
        except HTTPError:
            logger.error("Not scrapped document on day %s", day_str)
        logger.info("Downloaded BOPZ content for day %s", day_str)
        return metadata_documents

    def download_document(self, url:str, metadata: BeautifulSoup) -> BOPZMetadataDocument:
        """Get text and metadata from a BOPZ pdf document.

        :param url: document url link. Examples:
            * http://bop.dpz.es/BOPZ/obtenerContenidoEdicto.do?idEdicto=729066
            * http://bop.dpz.es/BOPZ/obtenerContenidoEdicto.do?idEdicto=729162
        :metadata BeautifulSoup: document metadata associated with url download link.
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scrapping document: %s", url)
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        with tempfile.NamedTemporaryFile("w", delete=False) as fn:
            text = soup.find('div', class_='medium-12 panel').get_text(strip=True, separator="\n")
            fn.write(text)
        metadata_dict = _extract_metadata(metadata)
        metadata_dict["identificador"] = url.split('=')[1]
        metadata_dict['url_html'] = url
        metadata_doc = BOPZMetadataDocument(filepath=fn.name, **metadata_dict)
        logger.info("Scrapped document successfully %s", url)
        return metadata_doc
