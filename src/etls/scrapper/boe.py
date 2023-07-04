import logging as lg
import typing as tp
import tempfile
import unicodedata
from datetime import date, timedelta

from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError

from src.etls.scrapper.base import BaseScrapper
from src.etls.utils import BOEMetadataDocument, BOEMetadataReferencia, BOEMetadataDocument2
from src.initialize import initialize_logging


initialize_logging()


def _extract_metadata(soup) -> tp.Dict:
    metadata_dict = {}

    # Metadatos
    identificador = soup.documento.metadatos.identificador
    if identificador:
        metadata_dict['identificador'] = identificador.get_text()

    if numero_oficial := soup.documento.metadatos.numero_oficial:
        metadata_dict['numero_oficial'] = numero_oficial.get_text()

    if departamento := soup.documento.metadatos.departamento:
        metadata_dict['departamento'] = departamento.get_text()

    if rango := soup.documento.metadatos.rango:
        metadata_dict['rango'] = rango.get_text()

    if titulo := soup.documento.metadatos.titulo:
        metadata_dict['titulo'] = titulo.get_text()

    if url_pdf := soup.documento.metadatos.url_pdf:
        metadata_dict['url_pdf'] = url_pdf.get_text()

    if origen_legislativo := soup.documento.metadatos.origen_legislativo:
        metadata_dict['origen_legislativo'] = origen_legislativo.get_text()

    if fecha_publicacion := soup.documento.metadatos.fecha_publicacion:
        metadata_dict['fecha_publicacion'] = fecha_publicacion.get_text()

    if fecha_disposicion := soup.documento.metadatos.fecha_disposicion:
        metadata_dict['fecha_disposicion'] = fecha_disposicion.get_text()

    # Analisis
    if observaciones := soup.documento.analisis.observaciones:
        metadata_dict['observaciones'] = observaciones.get_text()

    if ambito_geografico := soup.documento.analisis.ambito_geografico:
        metadata_dict['ambito_geografico'] = ambito_geografico.get_text()

    if modalidad := soup.documento.analisis.modalidad:
        metadata_dict['modalidad'] = modalidad.get_text()

    if tipo := soup.documento.analisis.tipo:
        metadata_dict['tipo'] = tipo.get_text()

    metadata_dict['materias'] = [
        materia.get_text() for materia in soup.select('documento > analisis > materias > materia')
    ]
    metadata_dict['alertas'] = [
        alerta.get_text() for alerta in soup.select('documento > analisis > alertas > alerta')
    ]
    metadata_dict['notas'] = [
        nota.get_text() for nota in soup.select('documento > analisis > notas > nota')
    ]
    metadata_dict['ref_posteriores'] = [
        BOEMetadataReferencia(id=ref['referencia'], palabra=ref.palabra.get_text(), texto=ref.texto.get_text())
        for ref in soup.select('documento > analisis > referencias > posteriores > posterior')
    ]
    metadata_dict['ref_anteriores'] = [
        BOEMetadataReferencia(id=ref['referencia'], palabra=ref.palabra.get_text(), texto=ref.texto.get_text())
        for ref in soup.select('documento > analisis > referencias > anteriores > anterior')
    ]
    return metadata_dict


def _list_links_day(url: str) -> tp.List[str]:
    """Get a list of links in a BOE url day.

    :param url: day url link. Example: https://www.boe.es/boe/dias/2022/09/07/
    :return: list of id documents to explore (links)
    """
    logger = lg.getLogger(_list_links_day.__name__)
    logger.info("Scrapping day: %s", url)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    id_links = [
        link.find('a').get('href').split('?id=')[-1]
        for link in soup.find_all('li', class_='puntoHTML')
    ]
    logger.info("Scrapped day successfully %s", url)
    return id_links


class BOEScrapper(BaseScrapper):

    def download_days(self, date_start: date, date_end: date) -> tp.List[BOEMetadataDocument]:
        """Download all the documents between two dates (from date_start to date_end)
        """
        logger = lg.getLogger(self.download_days.__name__)
        logger.info("Downloading BOE content from day %s to %s", date_start, date_end)
        delta = timedelta(days=1)
        metadata_documents = []
        while date_start <= date_end:
            boe_docs = self.download_day(date_start)
            metadata_documents += boe_docs
            date_start += delta
        logger.info("Downloaded BOE content from day %s to %s", date_start, date_end)
        return metadata_documents

    def download_day(self, day: date) -> tp.List[BOEMetadataDocument]:
        """Download all the documents for a specific date.
        """
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOE content for day %s", day)
        day_str = day.strftime("%Y/%m/%d")
        day_url = f"https://www.boe.es/boe/dias/{day_str}"
        metadata_documents = []
        try:
            id_links = _list_links_day(day_url)
            for id_link in id_links:
                # TODO: versión mejorada... splitting by articles...
                # url_document = f"https://www.boe.es/buscar/act.php?id={id_link}"
                url_document = f"https://www.boe.es/diario_boe/xml.php?id={id_link}"
                try:
                    metadata_doc = self.download_document(url_document)
                    metadata_documents.append(metadata_doc)
                    # logger.error("Scrapped document %s on day %s", url_document, day_url)
                except HTTPError:
                    logger.error("Not scrapped document %s on day %s", url_document, day_url)
        except HTTPError:
            logger.error("Not scrapped document %s on day %s", url_document, day_url)
        logger.info("Downloaded BOE content for day %s", day)
        return metadata_documents

    def download_document(self, url: str) -> BOEMetadataDocument:
        """Get text and metadata from a BOE xml url document.

        :param url: document url link. Examples:
            * https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-14630
            * https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-12203
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scrapping document: %s", url)
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        with tempfile.NamedTemporaryFile('w', delete=False) as fn:
            text = soup.select_one("documento > texto").get_text()
            fn.write(text)
        metadata_doc = BOEMetadataDocument(
            filepath=fn.name,
            **_extract_metadata(soup)
        )
        logger.info("Scrapped document successfully %s", url)
        return metadata_doc

    def download_document_txt(self, url: str) -> BOEMetadataDocument2:
        # NOTE: deprecated

        """Get a text document from a BOE url document.

        :param url: document url link. Example: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-14630
        :return: document with text content
        """
        logger = lg.getLogger(self.download_document_txt.__name__)
        logger.info("Scrapping document: %s", url)
        response = requests.get(url)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile('w', delete=False) as fn:
            soup = BeautifulSoup(response.text, 'html.parser')  # 'html5lib'
            text = soup.find('div', id='textoxslt').get_text()
            text = unicodedata.normalize('NFKC', text)
            fn.write(text)
        span_tag = soup.find('span', class_='puntoConso')
        if span_tag:
            span_tag = span_tag.extract()
            # TODO: link to span_tag.a['href'] to improve the split by articles -> https://www.boe.es/buscar/act.php?id=BOE-A-2022-14630
        title = soup.find('h3', class_='documento-tit').get_text()
        metadata_doc = BOEMetadataDocument2(
            filepath=fn.name,
            title=title,
            url=url,
            document_id=url.split('?id=')[-1]
        )
        logger.info("Scrapped document successfully %s", url)
        return metadata_doc
