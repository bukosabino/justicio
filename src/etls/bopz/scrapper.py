import logging as lg
import tempfile
import typing as tp
from datetime import date, datetime

import re
import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from langchain_community.document_loaders import OnlinePDFLoader

from src.etls.bopz.metadata import BOPZMetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.initialize import initialize_logging

initialize_logging()

# POST data to filter retrieved BOPZ documents
data_post = {
	'numPag': '',
	'idProcedente': '8610',
	'idPortador': '',
	'hProcedente': ' AYUNTAMIENTO DE ZARAGOZA',
	'hPortador': '',
	'idPagadora': '8610',
	'hPagadora': ' AYUNTAMIENTO DE ZARAGOZA',
	'primeraVez': 'N',
	'ficheroDoc': 'N',
	'numRegistroInf': '',
	'numRegistroSup': '',
	'esPortalSN': 'S',
	'numBoletinInf': '',
	'numRegistroNumInf': '',
	'numRegistroAnyoInf': '',
	'numRegistroNumSup': '',
	'numRegistroAnyoSup': '',
	'numBoletinAuxInf': '',
	'anyoBoletinInf': '',
	'numBoletinSup': '',
	'anyoBoletinSup': '',
	'fechaPubInf': '',
    'fechaPubSup': '',
	'procedente': ' AYUNTAMIENTO DE ZARAGOZA',
	'tematica': '',
	'titulo': '',
	'contenido': ''
}

def _extract_span_text(row: bs4.element.Tag, text_label: str) -> str:
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
    
    if identificador := _extract_span_text(soup, 'Nº. Reg:'):
        metadata_dict["identificador"] = identificador
        metadata_dict["numero_oficial"] = identificador.split('/')[0]
        metadata_dict["titulo"] = f"BOPZ-{identificador.replace('/', '-')}"
    
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
    
    return metadata_dict

def _list_links_day(url: str, day: date) -> tp.List[str]:
    """Get a list of documents listed in a BOPZ url day

    :param url: url base link. Example: http://bop.dpz.es/BOPZ
    :param day: date to scrap
    :return: list of documents to explore (BeatifullSoup objects)
    """
    logger = lg.getLogger(_list_links_day.__name__)
    day_str = day.strftime('%d/%m/%Y')
    logger.info("Scrapping day: %s", day_str)
    data_post['fechaPubInf'] = day_str
    data_post['fechaPubSup'] = day_str
    response = requests.post('http://bop.dpz.es/BOPZ/portalBuscarEdictos.do', data=data_post)
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
    BASE_URL = 'http://bop.dpz.es/BOPZ'
    
    def download_day(self, day: date) -> tp.List[BOPZMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOPZ content for day %s", day)
        metadata_documents = []
        try:
            id_links = _list_links_day(self.BASE_URL, day)
            # For each id_link, scrap pdf link and metadata
            for id_link in id_links:
                try:
                    metadata_doc = self.download_document(id_link)
                    metadata_documents.append(metadata_doc)
                except Exception as e:
                    logger.error(
                        "Not scrapped document %s on day %s. Error: %s", e.args[0]
                    )
        except HTTPError:
            logger.error("Not scrapped document on day %s", day)
        logger.info("Downloaded BOPZ content for day %s", day)
        return metadata_documents

    def download_document(self, soap: BeautifulSoup) -> BOPZMetadataDocument:
        """Get text and metadata from a BOPZ pdf document.

        :param soap: document BeautifulSoup object.
        Examples of valid url_pdf after href extraction from soap:
            * http://bop.dpz.es/BOPZ/UploadServlet?ruta=Boletines/2021/159/Edictos/bop_6523_2021.pdf
            * http://bop.dpz.es/BOPZ/UploadServlet?ruta=Boletines/2021/159/Edictos/bop_6550_2021.pdf
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_document.__name__)
        # Find pdf attached to the url
        href = soap.find('a', class_='adjunto')['href'][1:]
        url_pdf = f"{self.BASE_URL+href}"
        logger.info("Scrapping document: %s", url_pdf)
        loader = OnlinePDFLoader(url_pdf)
        with tempfile.NamedTemporaryFile("w", delete=False) as fn:
            data = loader.load()
            text = data[0].page_content
            text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.M) # Remove page numbers
            text = re.sub(r'(\w+)- (\w+)', r'\1\2', text) # Remove hyphens between words
            text = re.sub(r'\n+', '\n', text).rstrip('\n')  # Remove redundant newlines
            fn.write(text)
        metadata_dict = _extract_metadata(soap)
        metadata_dict["url_pdf"] = url_pdf
        metadata_doc = BOPZMetadataDocument(filepath=fn.name, **metadata_dict)
        logger.info("Scrapped document successfully %s", url_pdf)
        return metadata_doc
