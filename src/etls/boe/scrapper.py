import logging as lg
import tempfile
import typing as tp
from datetime import date, datetime

from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

from src.etls.boe.metadata import BOEMetadataDocument, BOEMetadataReferencia
from src.etls.common.scrapper import BaseScrapper
from src.initialize import initialize_logging
from src.etls.utils import create_retry_session

initialize_logging()


def _extract_metadata(soup) -> tp.Dict:
    metadata_dict = {}

    # Metadatos
    if identificador := soup.documento.metadatos.identificador:
        metadata_dict["identificador"] = identificador.get_text()

    if diario := soup.documento.metadatos.diario:
        metadata_dict["diario"] = diario.get_text()

    if numero_oficial := soup.documento.metadatos.numero_oficial:
        metadata_dict["numero_oficial"] = numero_oficial.get_text()

    if departamento := soup.documento.metadatos.departamento:
        metadata_dict["departamento"] = departamento.get_text()

    if rango := soup.documento.metadatos.rango:
        metadata_dict["rango"] = rango.get_text()

    if titulo := soup.documento.metadatos.titulo:
        metadata_dict["titulo"] = titulo.get_text()

    if url_pdf := soup.documento.metadatos.url_pdf:
        metadata_dict["url_pdf"] = url_pdf.get_text()

    if origen_legislativo := soup.documento.metadatos.origen_legislativo:
        metadata_dict["origen_legislativo"] = origen_legislativo.get_text()

    if fecha_publicacion := soup.documento.metadatos.fecha_publicacion:
        metadata_dict["fecha_publicacion"] = fecha_publicacion.get_text()

    if fecha_disposicion := soup.documento.metadatos.fecha_disposicion:
        metadata_dict["fecha_disposicion"] = fecha_disposicion.get_text()

    metadata_dict["anio"] = datetime.strptime(fecha_publicacion.get_text(), "%Y%m%d").strftime("%Y")

    metadata_dict["mes"] = datetime.strptime(fecha_publicacion.get_text(), "%Y%m%d").strftime("%m")

    metadata_dict["dia"] = datetime.strptime(fecha_publicacion.get_text(), "%Y%m%d").strftime("%d")

    # Analisis
    if observaciones := soup.documento.analisis.observaciones:
        metadata_dict["observaciones"] = observaciones.get_text()

    if ambito_geografico := soup.documento.analisis.ambito_geografico:
        metadata_dict["ambito_geografico"] = ambito_geografico.get_text()

    if modalidad := soup.documento.analisis.modalidad:
        metadata_dict["modalidad"] = modalidad.get_text()

    if tipo := soup.documento.analisis.tipo:
        metadata_dict["tipo"] = tipo.get_text()

    metadata_dict["materias"] = [
        materia.get_text() for materia in soup.select("documento > analisis > materias > materia")
    ]
    metadata_dict["alertas"] = [alerta.get_text() for alerta in soup.select("documento > analisis > alertas > alerta")]
    metadata_dict["notas"] = [nota.get_text() for nota in soup.select("documento > analisis > notas > nota")]
    metadata_dict["ref_posteriores"] = [
        BOEMetadataReferencia(
            id=ref["referencia"],
            palabra=ref.palabra.get_text(),
            texto=ref.texto.get_text(),
        )
        for ref in soup.select("documento > analisis > referencias > posteriores > posterior")
    ]
    metadata_dict["ref_anteriores"] = [
        BOEMetadataReferencia(
            id=ref["referencia"],
            palabra=ref.palabra.get_text(),
            texto=ref.texto.get_text(),
        )
        for ref in soup.select("documento > analisis > referencias > anteriores > anterior")
    ]
    return metadata_dict


def _list_links_day(url: str) -> tp.List[str]:
    """Get a list of links in a BOE url day filtering by Seccion 1 and Seccion T.

    :param url: day url link. Example: https://www.boe.es/diario_boe/xml.php?id=BOE-S-20230817
    :return: list of id documents to explore (links)
    """
    logger = lg.getLogger(_list_links_day.__name__)
    logger.info("Scrapping day: %s", url)
    session = create_retry_session(retries=5)
    response = session.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    id_links = [
        url.text.split("?id=")[-1]
        for section in soup.find_all(
            lambda tag: tag.name == "seccion"
            and "num" in tag.attrs
            and (tag.attrs["num"] == "1" or tag.attrs["num"] == "T")  # Note: Sección 1 and Tribunal Supremo
        )
        for url in section.find_all("urlxml")
    ]
    logger.info("Scrapped day successfully %s (%s BOE documents)", url, len(id_links))
    return id_links


class BOEScrapper(BaseScrapper):
    def download_day(self, day: date) -> tp.List[BOEMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOE content for day %s", day)
        day_str = day.strftime("%Y%m%d")
        day_url = f"https://www.boe.es/diario_boe/xml.php?id=BOE-S-{day_str}"
        metadata_documents = []
        try:
            id_links = _list_links_day(day_url)
            for id_link in id_links:
                url_document = f"https://www.boe.es/diario_boe/xml.php?id={id_link}"
                try:
                    metadata_doc = self.download_document(url_document)
                    metadata_documents.append(metadata_doc)
                except HTTPError:
                    logger.error("Not scrapped document %s on day %s", url_document, day_url)
                except AttributeError:
                    logger.error("Not scrapped document %s on day %s", url_document, day_url)
        except HTTPError:
            logger.error("Not scrapped document on day %s", day_url)
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
        session = create_retry_session(retries=5)
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        with tempfile.NamedTemporaryFile("w", delete=False) as fn:
            if url_eli := soup.metadatos.url_eli:
                url = url_eli.get_text()
                text = self.download_eli_document(url)
            else:
                text = soup.select_one("documento > texto").get_text()
            fn.write(text)
        metadata_doc = BOEMetadataDocument(filepath=fn.name, **_extract_metadata(soup))
        logger.info("Scrapped document successfully %s", url)
        return metadata_doc

    def download_eli_document(self, url: str) -> str:
        """Get text from a BOE eli url document.

        :param url: document url link. Examples:
            * https://www.boe.es/eli/es/c/1978/12/27/(1)/con
            *
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_eli_document.__name__)
        logger.info("Scrapping consolidated text (eli) from document: %s", url)
        session = create_retry_session(retries=5)
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        div = soup.find("div", id="textoxslt")
        if marcadores := div.find('div', class_='marcadores'):
            marcadores.decompose()
        text_consolidated = div.get_text()
        logger.info("Scrapped consolidated text (eli) successfully from document: %s", url)
        return text_consolidated
