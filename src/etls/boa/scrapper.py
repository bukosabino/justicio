import logging as lg
import tempfile
import typing as tp
from datetime import date, datetime
import random
import json 
from lxml import etree

import requests

from src.etls.boa.metadata import BOAMetadataDocument
from src.etls.common.metadata import MetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.etls.common.utils import ScrapperError
from src.initialize import initialize_logging
from src.etls.utils import create_retry_session


initialize_logging()


def _remove_html_tags(text: str) -> str:
    parser = etree.HTMLParser()
    tree = etree.fromstring(text, parser)
    clean_text = etree.tostring(tree, encoding="unicode", method='text') 
    return clean_text.strip()


def _extract_metadata(doc: dict) -> tp.Dict:
    metadata_dict = {}
    
    try:
        metadata_dict["identificador"] = doc["DOCN"]
    except KeyError:
        pass

    try:
        metadata_dict["numero_boletin"] = doc["Numeroboletin"]
    except KeyError:
        pass
    
    try:
        metadata_dict["departamento"] = doc["Emisor"].capitalize()
    except KeyError:
        pass
    
    try:
        metadata_dict["url_pdf"] = doc["UrlPdf"].split('´`')[0][1:]
    except KeyError:
        pass
    
    try:
        metadata_dict["url_boletin"] = doc["UrlBCOM"].split('´`')[0][1:]
    except KeyError:
        pass
    
    try:
        metadata_dict["seccion"] = doc["Seccion"]
    except KeyError:
        pass

    try:
        metadata_dict["titulo"] = doc["Titulo"]
    except KeyError:
        pass
    
    try:
        metadata_dict["subseccion"] = doc["Subseccion"]
    except KeyError:
        pass
    
    try:
        metadata_dict["codigo_materia"] = doc["CodigoMateria"]
    except KeyError:
        pass
    
    try:
        metadata_dict["rango"] = doc["Rango"].capitalize()
    except KeyError:
        pass

    try:
        fecha_disposicion = datetime.strptime(doc["Fechadisposicion"], "%Y%m%d").strftime("%Y-%m-%d")
        metadata_dict["fecha_disposicion"] = fecha_disposicion
    except KeyError:
        pass
    
    return metadata_dict 
   
    
class BOAScrapper(BaseScrapper):
    def __init__(self):
        self.base_url = "https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
        ]
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "User-Agent": random.choice(self.user_agents),
        }    

    
    def download_day(self, day: date) -> tp.List[BOAMetadataDocument]:
        """Download all the documents for a specific date."""
        try:
            logger = lg.getLogger(self.download_day.__name__)
            logger.info("Downloading BOA content for day %s", day)
            params ={'CMD': 'VERLST',
                     'BASE': 'BZHT',
                     'DOCS': '1-250',
                     'SEC': 'OPENDATABOAJSONAPP',
                     'OUTPUTMODE': 'JSON',
                     'SEPARADOR':'',
                     'PUBL-C': day.strftime("%Y%m%d"),
                     'SECC-C':'BOA%2Bo%2BDisposiciones%2Bo%2BJusticia'
                     # versión completa (todas las secciones, incluyendo personal, etc):
                     # 'SECC-C':'BOA%2Bo%2BDisposiciones%2Bo%2BPersonal%2Bo%2BAcuerdos%2Bo%2BJusticia%2Bo%2BAnuncios' 
                     }
            session = create_retry_session(retries=5)
            response = session.get(self.base_url, params=params)
            raw_result = response.text
            if '<span class="titulo">No se han recuperado documentos</span>' in raw_result:
                logger.info(f"No hay contenido disponible para el día {day}")
                return []
            if response.status_code != 200:
                response.raise_for_status() 
            raw_result = raw_result.replace('\\', '\\\\')
            result_json = json.loads(raw_result)
            disposiciones = []
            for doc in result_json:
                metadata_doc = self.download_document(json.dumps(doc))
                fecha_publicacion_atributos = {
                    "fecha_publicacion": day.strftime("%Y-%m-%d"), 
                    "anio": day.strftime("%Y"),
                    "mes": day.strftime("%m"),
                    "dia": day.strftime("%d"),
                }
                for atributo, valor in fecha_publicacion_atributos.items():
                        setattr(metadata_doc, atributo, valor)
                disposiciones.append(metadata_doc)
            return disposiciones
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de red o HTTP al intentar acceder a {self.base_url}: {e}")
        except Exception as e:
            raise Exception(f"Error inesperado: {e}")
        

    def download_document(self, url: str) -> MetadataDocument:
        '''
        En BOAScrapper, a partir de la url diaria (en la función download_day), 
        se recibe directamente el contenido de todos los boletines. Por lo tanto,
        no hace falta scrapear cada uno de las publicaciones a partir de su url.
        
        Para ser consistentes con el resto de scrappers, se mantiene el método
        download_document, pero en este caso en vez de la url se le pasará una 
        string con el contenido y los metadatos, tal y como se recibe de la base_url
        '''
        
        logger = lg.getLogger(self.download_document.__name__)
        doc = json.loads(url) 
        url_pdf_raw = doc['UrlPdf']
        url_pdf = url_pdf_raw.split('´`')[0][1:]
        logger.info("Scrapping document: %s", url_pdf)
        content = doc['Texto']
        clean_text = _remove_html_tags(content)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding='utf-8') as fn:
            fn.write(clean_text)           
        try:
            metadata_doc = BOAMetadataDocument(filepath=fn.name,**_extract_metadata(doc))
        except:
            raise ScrapperError("No se pudo encontrar alguno de los elementos requeridos.")
        logger.info("Scrapped document successfully %s", url_pdf)
        return metadata_doc
