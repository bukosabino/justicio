import logging as lg
import tempfile
import typing as tp
from datetime import date
import re

from src.etls.boja.metadata import BOJAMetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.etls.common.utils import ScrapperError, HTTPRequester
from src.etls.boja.utils import mes_a_numero, clean_text
from src.initialize import initialize_logging


initialize_logging()

def clean_text(text: str) -> str:
    cleaned = re.sub(r"(\xa0|\t+|\n+)", " ", text, flags=re.MULTILINE)
    return cleaned


class BOJAScrapper(BaseScrapper):
    def __init__(self):
        self.base_url = "https://www.juntadeandalucia.es/"
        
    @staticmethod
    def check_extraordinary_boja(url):       
            return re.match(r".*/\d{8}\.html$", url) is not None
        
    @staticmethod
    def extract_bojas_from_extraordinary(url):
        urls_bojas = []
        soup = HTTPRequester.get_soup(url)
        try:           
            uls = soup.find_all('ul', class_="mt-4 pl-3")
            for ul in uls:
                links = ul.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    es_extraordinario = "extraordinario" in link.text.lower()
                    urls_bojas.append((href, es_extraordinario))

            return urls_bojas        
        except Exception as e:
            raise Exception(f"Error inesperado: {e}")
        
    @staticmethod    
    def find_disposiciones(url_boletin):        
        enlaces_html = []
        enlaces_finales = []
        soup = HTTPRequester.get_soup(url_boletin)
        try:            
            listado_principal = soup.find('ol', class_='listado_ordenado_boja raiz')
            if not listado_principal:                
                listado_principal = soup.find(['ol', 'ul'], class_=['listado_ordenado_boja','listado_ordenado'])
            if listado_principal:                
                items_a = listado_principal.find_all('a')
                for item in items_a:                    
                    if re.search(r'\b(Disposiciones Generales|Otras Disposiciones)\b', item.text, re.IGNORECASE):                        
                        enlaces_html.append(item.get('href'))
                for enlace in enlaces_html:                    
                    soup_intermedio = HTTPRequester.get_soup(enlace)
                    enlaces_intermedios = soup_intermedio.find_all('a', class_='item_html', title=re.compile("Versión HTML CVE"))
                    enlaces_intermedios += soup_intermedio.find_all('a', title="Ver disposición") 
                    for enlace_final in enlaces_intermedios:
                        enlaces_finales.append(enlace_final.get('href'))                                                         
            else:
                raise ScrapperError("No se encontró el listado ordenado con las clases especificadas.")          
        except Exception as e:
            raise Exception(f"Error inesperado: {e}")
        return enlaces_finales

    def _get_summary_link_from_date(self, fecha_busqueda):
        url = f"{self.base_url}/{'eboja' if fecha_busqueda.year >= 2012 else 'boja'}/{fecha_busqueda.year}"
        soup = HTTPRequester.get_soup(url)
        try:
            tablas_calendario = soup.find_all('table', class_='calendario_tabla')
            for tabla in tablas_calendario:
                summary_text = tabla.get('summary', '')
                mes_año_match = re.search(r"Boletines del mes de (\w+) de (\d{4})", summary_text)
                if mes_año_match:
                    mes = mes_año_match.group(1)
                    año = mes_año_match.group(2)
                    enlaces = tabla.find_all('a')
                    for enlace in enlaces:
                        href = enlace.get('href')
                        dia = enlace.text.strip()
                        fecha_iso = f"{año}-{mes_a_numero(mes):02d}-{int(dia):02d}"
                        if fecha_iso == fecha_busqueda.strftime('%Y-%m-%d'):
                            if BOJAScrapper.check_extraordinary_boja(href):
                                urls_bojas = BOJAScrapper.extract_bojas_from_extraordinary(href)
                                enlaces_extraordinarios = []
                                for url_boja, es_extraordinario in urls_bojas:
                                    enlaces_extraordinarios.append({
                                        "url": url_boja,
                                        "fecha": fecha_iso,
                                        "extraordinario": es_extraordinario
                                    })
                                return enlaces_extraordinarios
                            else:                             
                                return [{
                                    "url": href,
                                    "fecha": fecha_iso,
                                    "extraordinario": False
                                }]
        except Exception as e:
            raise Exception(f"Error inesperado: {e}")

    def download_day(self, day: date) -> tp.List[BOJAMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOJA content for day %s", day)
        try:
            disposiciones = []
            lista_boletines = self._get_summary_link_from_date(day) 
            if not lista_boletines:
                logger.info(f"No hay contenido disponible para el día {day}")
                return [] #None =  para ese dia no hay boletín            
            for boletin in lista_boletines: # Boletines. Si hay boletin extraordinario esto será 2                            
                for disposicion in BOJAScrapper.find_disposiciones(boletin['url']):
                    document_data = self.download_document(disposicion)
                    if document_data:
                        disposition_summary = {
                            "url_boletin": boletin['url'],
                            "url_html": disposicion,
                            "fecha_disposicion": day.strftime("%Y-%m-%d"),
                            "anio": str(day.year),
                            "mes": str(day.month),
                            "dia": str(day.day),
                        }
                        for atributo, valor in disposition_summary.items():
                            setattr(document_data, atributo, valor)
                        disposiciones.append(document_data) 
            return disposiciones 
        except Exception as e:
            raise Exception(f"Error inesperado descargando dia {day}: {e}")
        
    def download_document(self, url: str) -> BOJAMetadataDocument:
        """
        Extracts the content, the issuing body, and the PDF URL of a specific disposition from BOJA given its URL.
        
        :param url_disposicion: The full URL of the disposition from which the content and PDF URL are to be extracted.
        Example: "https://www.juntadeandalucia.es/eboja/2024/7/s51.html"
        :return: A BOJAMMetadataDocument containing the content of the disposition, the name of the issuing body, and the PDF URL.
        If the content, the issuing body, or the PDF URL is not found, it returns empty strings for those values.
        """
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scrapping document: %s", url)
        texto_completo = ""
        soup = HTTPRequester.get_soup(url)
        try:
            cuerpo = soup.find(id="cuerpo", class_="grid_11 contenidos_nivel3 boja_disposicion")        
            cabecera = soup.find(class_="punteado_izquierda cabecera_detalle_disposicion")
            if not cabecera or not cuerpo:
                raise ScrapperError("No se pudo encontrar la cabecera o el cuerpo del documento")
            h2 = cabecera.find('h2')
            h5 = cabecera.find('h5')
            h3 = cabecera.find('h3')
            titulo_div = cabecera.find('div', class_="item")
            if titulo_div and titulo_div.p:
                titulo = titulo_div.p.text.strip()
            else:
                h4 = cabecera.find('h4') 
                titulo = h4.text.strip() if h4 else ""  
                   
            tipo_disposicion = h2.text.strip() if h2 else ""
            organo_disposicion = h5.text.strip() if h5 is not None else (h3.text.strip() if h3 is not None else "")
            enlace_pdf = soup.find('a', class_="item_pdf_disposicion").get('href')
            parrafos = cuerpo.find_all('p')            

            for parrafo in parrafos:
                if parrafo.parent.get('class') == ['alerta']:
                    continue
                texto_completo += parrafo.text + "\n"
            text_cleaned = clean_text(texto_completo)
            with tempfile.NamedTemporaryFile("w", delete=False) as fn:
                fn.write(text_cleaned)
            logger.info("Scrapped document successfully %s", url)      
            metadata_doc = BOJAMetadataDocument(**{ "filepath": fn.name,
                                                    "identificador": '/'.join(url.split("/")[-3:]),
                                                    "titulo": titulo,
                                                    "departamento": clean_text(organo_disposicion),
                                                    "url_pdf": enlace_pdf,
                                                    "tipologia": re.sub(r"^\d+\.\s*", "", tipo_disposicion),                                                 
                                                    })
            return metadata_doc              
        except Exception as e:
            raise Exception(f"Error inesperado procesando el documento {url}: {e}")
