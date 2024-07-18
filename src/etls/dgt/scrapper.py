import re
import requests
import tempfile
import typing as tp
import logging as lg
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from datetime import date, datetime
from requests.exceptions import HTTPError

from src.etls.common.scrapper import BaseScrapper
from src.etls.dgt.metadata import DGTMetadataDocument
from src.etls.dgt.utils import SEARCH_POST, DOC_POST, HEADERS, TARGET_CLASSES

initialize_logging()

def _extract_target_class(soup: BeautifulSoup, target_class: str) -> str:
    """
    Extracts the text of the next sibling for a span element that contains the specified text_label.

    :param row: The BeautifulSoup row element to search within.
    :param regex: The regular expresion to search for within the span element.
    :return: The stripped text of the next sibling if found, otherwise an empty string.
    """

    num_consulta_value = ""
    # Extraer la información deseada
    num_consulta_tag = soup.find('tr', class_=target_class)
    num_consulta_value_ = num_consulta_tag.find_all('p', class_=target_class)
    for v in num_consulta_value_:
        num_consulta_value += v.get_text(separator='\n', strip=True)

    return num_consulta_value #num_consulta_label

def _extract_metadata(soup) -> tp.Dict:
    metadata_dict = {}
    
    metadata_dict['source_type'] = soup.find('div', class_="doc_header").contents[-1].strip()

    # Metadatos
    if numero_consulta := _extract_target_class(soup, "NUM-CONSULTA"):
        metadata_dict["numero_consulta"] = numero_consulta

    if organo := _extract_target_class(soup, "ORGANO"):
        metadata_dict["organo"] = organo

    if normativa := _extract_target_class(soup, "NORMATIVA"):
        metadata_dict["normativa"] = normativa

    if fecha_publicacion := _extract_target_class(soup, "FECHA-SALIDA"):
        fecha_publicacion = datetime.strptime(fecha_publicacion, "%d/%m/%Y").strftime("%Y-%m-%d")
        metadata_dict["fecha_publicacion"] = fecha_publicacion
        metadata_dict["fecha_disposicion"] = fecha_publicacion
        metadata_dict["anio"] = str(datetime.strptime(fecha_publicacion, "%Y-%m-%d").year)
        metadata_dict["mes"] = str(datetime.strptime(fecha_publicacion, "%Y-%m-%d").month)
        metadata_dict["dia"] = str(datetime.strptime(fecha_publicacion, "%Y-%m-%d").day)

    return metadata_dict

def _extract_text(soup: BeautifulSoup, target_classes: str) -> str:
    """
    Extracts text from HTML elements with specific classes. Iterate over 
    each class, look for elements with that class and check if they are root 
    elements (not nested). If it is a root element, it adds its text to the
    result.
    """
    extracted_text = ""
    for class_name in target_classes:
        for element in soup.find_all(class_=class_name):
            parent_with_same_class = element.find_parent(class_=class_name)
            if parent_with_same_class is None:
                extracted_text += element.get_text(separator='\n', strip=True) + "\n\n"
    return extracted_text    


def _list_links_day(url: str, day_str: str) -> tp.List[BeautifulSoup]:
    """Get a list of documents listed in a DGT url day

    :param url: url base link. Example: 'https://petete.tributos.hacienda.gob.es/consultas/do/search'
    :param day_str: str date to scrap
    :return: return: list of id documents to explore
    """
    logger = lg.getLogger(_list_links_day.__name__)
    logger.info("Scrapping day: %s", day_str)

    SEARCH_POST['dateIni_2'] = day_str
    SEARCH_POST['dateEnd_2'] = day_str 
    SEARCH_POST['VLCMP_2'] = day_str + '..' + day_str 
    
    extracted_docs = []
    for tab in range(1,3):
        SEARCH_POST['tab'] = tab
        response = requests.post(url, data=SEARCH_POST, headers=HEADERS, verify=False)  # Omitir verificación SSL
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    
        if "La consulta realizada no devuelve resultados" in soup.text:
            pass
        else:   
            # Extract total pages and current page
            total_pages = int(soup.find('span', id='total_pages').text)   

            for page in range(1, total_pages+1):
                SEARCH_POST['page'] = str(page)         
                response = requests.post(url, data=SEARCH_POST, headers=HEADERS, verify=False)  # Omitir verificación SSL
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                # Find all the docs in the response which correspond to published enquiries  
                # Use a regular expression to match 'id' attributes starting with 'doc_'
                doc_ids = soup.find_all('td', id=re.compile('^doc_'))
                
                # Extract the 'id' attribute from each matching tag
                current_extracted_docs = [(doc['id'].split('_')[1], tab) for doc in doc_ids]
                extracted_docs += current_extracted_docs
       
    logger.info("Scrapped day successfully %s (%s DGT documents)", url, len(extracted_docs))
    
    return extracted_docs

class DGTScrapper(BaseScrapper):
    def download_day(self, day: date) -> tp.List[DGTMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading DGT content for day %s", day)
        day_str = day.strftime("%d/%m/%Y")
        url_search = "https://petete.tributos.hacienda.gob.es/consultas/do/search"
        url = "https://petete.tributos.hacienda.gob.es/consultas/do/document"
        metadata_documents = []
        try:
            docs = _list_links_day(url_search, day_str)
            for id_doc, tab in docs:
                try:
                    DOC_POST['doc'] = id_doc   
                    DOC_POST['tab'] = tab              
                    encoded_params = urlencode(DOC_POST)                    
                    url_document = f"{url}?{encoded_params}"                                  
                    metadata_doc = self.download_document(url_document)
                    if metadata_doc != None:
                        metadata_documents.append(metadata_doc)
                    else:
                        logger.info("No data found in document %s", url)                        
                except HTTPError:
                    logger.error("Not scrapped document %s on day %s", url_document, day_str)
                except AttributeError:
                    logger.error("Not scrapped document %s on day %s", url_document, day_str)
        except HTTPError:
            logger.error("Not scrapped document on day %s", day_str)
        logger.info("Downloaded DGT content for day %s", day_str)
        return metadata_documents

    def download_document(self, url: str) -> DGTMetadataDocument:
        """Get text and metadata from a DGT document.

        :param url: document url link. Examples:
            * https://petete.tributos.hacienda.gob.es/consultas/do/document?doc=64316&tab=2
            * https://petete.tributos.hacienda.gob.es/consultas/do/document?doc=1&tab=1
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scrapping document: %s", url)
        response = requests.get(url, headers=HEADERS, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
      
        extracted_text = _extract_text(soup, TARGET_CLASSES)      
      
        # Check if enquiry has content
        if "Contestación completa" not in extracted_text:
            logger.info("Scrapped document is empty: %s", url)
            return 
              
        with tempfile.NamedTemporaryFile("w", delete=False) as fn:
            fn.write(extracted_text)
        metadata_dict = _extract_metadata(soup)
        metadata_dict["identificador"] = (url.split("=")[1]).split("&")[0]
        metadata_dict["url_html"] = url
        metadata_doc = DGTMetadataDocument(filepath=fn.name, **metadata_dict)
        logger.info("Scrapped document successfully %s", url)
        return metadata_doc
