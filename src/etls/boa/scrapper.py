import logging as lg
import tempfile
import typing as tp
from datetime import date
import random
import json 
from lxml import etree

import requests

from src.etls.boa.metadata import BOAMetadataDocument
from src.etls.common.metadata import MetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.etls.common.utils import ScrapperError
from src.initialize import initialize_logging


initialize_logging()


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

    def _remove_html_tags(self, text):
        parser = etree.HTMLParser()
        tree = etree.fromstring(text, parser)
        clean_text = etree.tostring(tree, encoding="unicode", method='text') 
        return clean_text.strip()
    
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
                     'SECC-C':'BOA%2Bo%2BDisposiciones%2Bo%2BJusticia%2Bo%2BAnuncios'
                     # versión completa (todas las secciones, incluyendo personal, etc):
                     # 'SECC-C':'BOA%2Bo%2BDisposiciones%2Bo%2BPersonal%2Bo%2BAcuerdos%2Bo%2BJusticia%2Bo%2BAnuncios' 
                     }
            response = requests.get(self.base_url, params=params)
            raw_result = response.text
            if '<span class="titulo">No se han recuperado documentos</span>' in raw_result:
                logger.info(f"No hay contenido disponible para el día {day}")
                return []
            if response.status_code != 200:
                response.raise_for_status() 
            result_json = json.loads(raw_result)
            disposiciones = []
            for doc in result_json:
                content = doc['Texto']
                numero_boletin = doc['Numeroboletin']
                identificador = doc['DOCN']
                departamento = doc['Emisor']
                url_pdf_raw = doc['UrlPdf']
                url_pdf = url_pdf_raw.split('´`')[0][1:]
                seccion = doc['Seccion']
                if not content or not numero_boletin or not identificador or not departamento or not url_pdf or not seccion:
                    raise ScrapperError("No se pudo encontrar alguno de los elementos requeridos.")
                
                clean_text = self._remove_html_tags(content)

                with tempfile.NamedTemporaryFile("w", delete=False, encoding='utf-8') as fn:
                    fn.write(clean_text)           
                document_data = BOAMetadataDocument(**{"filepath": fn.name,
                                                       "numero_boletin": numero_boletin,
                                                       "identificador": identificador,
                                                       "departamento": departamento,
                                                       "url_pdf": url_pdf,
                                                       "seccion": seccion, 
                                                       })
                titulo = doc['Titulo']
                url_boletin_raw = doc['UrlBCOM'] 
                url_boletin = url_boletin_raw.split('´`')[0][1:]
                subseccion = doc['Subseccion']
                codigo_materia = doc['CodigoMateria']
                rango = doc['Rango']
                fecha_disposicion = doc['Fechadisposicion']

                if not titulo:
                    raise ScrapperError("No se pudo encontrar el título en uno de los bloques.") 
                
                disposition_summary = {
                    "titulo": titulo,                        
                    "url_boletin": url_boletin,
                    "subseccion": subseccion,
                    "codigo_materia": codigo_materia,
                    "rango": rango,
                    "fecha_disposicion": fecha_disposicion,
                    "fecha_publicacion": day.strftime("%Y-%m-%d"), 
                    "anio": str(day.year),
                    "mes": str(day.month),
                    "dia": str(day.day),
                }
                for atributo, valor in disposition_summary.items():
                        setattr(document_data, atributo, valor)
                disposiciones.append(document_data)
            return disposiciones
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de red o HTTP al intentar acceder a {self.base_url}: {e}")
        except Exception as e:
            raise Exception(f"Error inesperado: {e}")
        

    def download_document(self, url: str) -> MetadataDocument:
        """ En este caso, dado que al acceder a la url diaria, el BOA devuelve el texto de todos los
            boletines en un JSON, no es necesario hacer uso de un método download_document(). 
            De todas formas, se debe incluir para el correcto funcionamiento del programa, ya que
            la clase BaseScrapper requiere que exista este método."""
        pass
