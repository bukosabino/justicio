import logging as lg
import tempfile
import typing as tp
from datetime import date
import re
import random

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from src.etls.bopv.metadata import BOPVMetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.etls.common.utils import ScrapperError
from src.initialize import initialize_logging


initialize_logging()

def clean_text(text: str) -> str:
    cleaned = re.sub(r"(\xa0|\t+|\n+)", " ", text, flags=re.MULTILINE)
    return cleaned


class BOPVScrapper(BaseScrapper):
    def __init__(self):
        self.base_url = "https://www.euskadi.eus/bopv2/datos/"
        self.boletin_url_base = "https://www.euskadi.eus/web01-bopv/es/bopv2/datos/"
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

    def _get_boletin_url(self, date: date, enlace_dia: str) -> str:
        """Generates a bulletin URL for a given date and link day."""
        return f"{self.boletin_url_base}{date.year}/{date.strftime('%m')}/{enlace_dia}"

    def _get_monthly_url(self, date: date) -> str:
        """Generates a monthly URL for a given date."""
        month_year = date.strftime("%m%Y")
        return f"{self.boletin_url_base}{month_year}.shtml"  

    def _get_summary_link_from_date(self, requested_date: date):
        url = self._get_monthly_url(requested_date)
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            html = response.text
            dias_habilitados_pattern = re.compile(r"var diasHabilitados = (\[.*?\]);")
            enlaces_pattern = re.compile(r"var enlaces = (\[.*?\]);")
            dias_habilitados_match = dias_habilitados_pattern.search(html)
            enlaces_match = enlaces_pattern.search(html)

            if dias_habilitados_match and enlaces_match:
                dias_habilitados = eval(dias_habilitados_match.group(1))
                enlaces = eval(enlaces_match.group(1))
                requested_date_formatted = requested_date.strftime("%Y%m%d")
                if requested_date_formatted in dias_habilitados:
                    index = dias_habilitados.index(requested_date_formatted)
                    enlace = enlaces[index]
                    if isinstance(enlace, list):
                        enlace = enlace[0]
                    final_url = self._get_boletin_url(requested_date, enlace)
                    return final_url
                else:
                    return None
        except requests.HTTPError as err:
            raise ValueError(f"Error en la solicitud HTTP: {err}")
        except ValueError as err:
            raise ValueError(f"Error en la solicitud HTTP: {err}")
    
    def download_day(self, day: date) -> tp.List[BOPVMetadataDocument]:
        """Download all the documents for a specific date."""
        try:
            logger = lg.getLogger(self.download_day.__name__)
            logger.info("Downloading BOCM content for day %s", day)
            summary_link = self._get_summary_link_from_date(day)
            if summary_link is None:
                logger.info(f"No hay contenido disponible para el día {day}")
                return []                
            response = requests.get(summary_link)
            if response.status_code != 200:
                response.raise_for_status()        
            disposiciones = []
            soup = BeautifulSoup(response.content, 'html.parser')
            txt_blocks = soup.find_all('div', class_='txtBloque')           
            for block in txt_blocks:
                titulo = block.find('p', class_='BOPVSumarioTitulo')
                if not titulo or not titulo.find('a'):
                    raise ScrapperError("No se pudo encontrar el título o el enlace en uno de los bloques.")            
                href = titulo.find('a')['href']
                url_disposicion = summary_link.rsplit('/', 1)[0] + '/' + href
                document_data = self.download_document(url_disposicion)
                if document_data:
                    disposition_summary = {
                        "titulo": titulo.text.strip(),                        
                        "url_html": url_disposicion,
                        "url_boletin": summary_link,
                        "fecha_disposicion": day.strftime("%Y-%m-%d"),
                        "anio": str(day.year),
                        "mes": str(day.month),
                        "dia": str(day.day),
                    }
                    for atributo, valor in disposition_summary.items():
                            setattr(document_data, atributo, valor)
                    disposiciones.append(document_data)                    
            return disposiciones 
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de red o HTTP al intentar acceder a {summary_link}: {e}")
        except Exception as e:
            raise Exception(f"Error inesperado: {e}")
        
    def download_document(self, url: str) -> BOPVMetadataDocument:
        """
        Extracts the content, the issuing body, and the PDF URL of a specific disposition from BOPV given its URL.
        
        :param url_disposicion: The full URL of the disposition from which the content and PDF URL are to be extracted.
        Example: "https://www.euskadi.eus/web01-bopv/es/bopv2/datos/2024/01/2400001a.shtml"
        :return: A BOCMMetadataDocument containing the content of the disposition, the name of the issuing body, and the PDF URL.
        If the content, the issuing body, or the PDF URL is not found, it returns empty strings for those values.
        """
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scrapping document: %s", url)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                response.raise_for_status() 
            soup = BeautifulSoup(response.content, "html.parser")
            seccion_tag = soup.find("h4", class_="BOPVSeccion")
            if not seccion_tag:
                raise ScrapperError("No se pudo encontrar la sección requerida.")

            seccion_text = seccion_tag.get_text(strip=True).upper()
            if seccion_text not in ['DISPOSICIONES GENERALES', 'OTRAS DISPOSICIONES']:
                return         
            tipologia = seccion_tag.get_text(strip=True)
            organismo_tag = soup.find("h5", class_="BOPVOrganismo")
            content_block = soup.find("div", class_="colCentralinterior")
            pdf_link_tag = soup.find("li", class_="formatoPdf").find('a')
            
            if not organismo_tag or not content_block or not pdf_link_tag:
                raise ScrapperError("No se pudo encontrar algunos de los elementos requeridos.")

            organismo = organismo_tag.get_text(strip=True) if organismo_tag else ""
            base_url = url.rsplit('/', 1)[0] + '/'
            pdf_href = pdf_link_tag.get('href') if pdf_link_tag else ""
            pdf_url = urljoin(base_url, pdf_href)            
            paragraphs = content_block.find_all("p", class_=re.compile(r"BOPV(Detalle|Titulo|FirmaLugFec|FirmaPuesto|FirmaNombre)"))
            content_paragraphs = [p.get_text(strip=True) for p in paragraphs]
            additional_elements = content_block.find_all(["h5", "div"], class_=re.compile(r"BOPV(Titulo|FirmaLugFec|FirmaPuesto|FirmaNombre)"))
            content_additional = [elem.get_text(strip=True) for elem in additional_elements]
            content = "\n".join(content_paragraphs + content_additional)
            
            with tempfile.NamedTemporaryFile("w", delete=False) as fn:
                text_cleaned = clean_text(content) 
                fn.write(text_cleaned)            
            metadata_doc = BOPVMetadataDocument(**{"filepath": fn.name,
                                                   "identificador": '/'.join(url.split('.')[-2].split("/")[-3:]),
                                                   "departamento": organismo,
                                                   "url_pdf": pdf_url,
                                                   "tipologia": tipologia,                                                 
                                                   })
            logger.info("Scrapped document successfully %s", url)
            return metadata_doc
               
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de red o HTTP al intentar acceder a {url}: {e}")
        except Exception as e:
            raise Exception(f"Error de red o HTTP al intentar acceder a {url}: {e}")