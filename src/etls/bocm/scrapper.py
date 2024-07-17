import logging as lg
import tempfile
import typing as tp
from datetime import date, datetime
import re

import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

from src.etls.bocm.metadata import BOCMMetadataDocument
from src.etls.bocm.utils import *
from src.etls.common.scrapper import BaseScrapper
from src.initialize import initialize_logging
from src.etls.utils import create_retry_session


initialize_logging()


# transformation from url retrieve from redirection to one pointing to complete summary
def _adapt_link_to_complete_summary(url: str) -> str:
    """Get complete summary url transforming the url received by param

    :url: url to transform. Example : https://www.bocm.es/boletin/bocm-20240126-22
    :return: summary of the day url. Example: https://www.bocm.es/boletin-completo/BOCM-20240126/22
    """
    tmp_str = url.replace("boletin", "boletin-completo").replace("/bocm", "/BOCM")
    res = re.sub(r"(\d)-(\d+)", r"\1/\2", tmp_str)
    return res


# get url from response redirection
def _get_summary_link_from_date(day: date) -> str:
    """Get summary url from response redirection

    :day: day format for request param: '%d/%m/%Y'
    :return: summary of the day url
    """
    logger = lg.getLogger(_get_summary_link_from_date.__name__)

    search_url = "https://www.bocm.es/search-day-month"

    try:
        response = requests.post(search_url, data={"field_date[date]": day})
        response.raise_for_status()
        link = response.headers["Link"].split(";")[0].replace("<", "").replace(">", "")
        if re.search("search-day-month", link):
            raise ValueError("No link published")
        else:
            final_url = _adapt_link_to_complete_summary(link)

    except HTTPError:
        logger.error("No link got on day %s", day)
        final_url = None

    except ValueError as err:
        logger.error("%s for day %s. Skiping...", err.args[0], day)
        final_url = None

    return final_url


def _extract_metadata(soup) -> tp.Dict:
    metadata_dict = {}

    # Metadata from head tags
    fecha_publicacion, cve, html_link = metadata_from_head_tags(soup)

    # Desc doc header
    numero_oficial, seccion_normalizada, paginas, pdf_link = metadata_from_doc_header(soup)

    # Metadata from document
    seccion = seccion_normalizada.split(".")[0]
    subseccion, apartado, tipo, organo, anunciante, rango = metadata_from_doc(soup, seccion, cve)

    metadata_dict["rango"] = rango
    metadata_dict["identificador"] = cve
    metadata_dict["numero_oficial"] = numero_oficial
    metadata_dict["paginas"] = paginas

    # departamento always match with organo
    metadata_dict["departamento"] = organo

    metadata_dict["seccion_normalizada"] = seccion_normalizada
    metadata_dict["seccion"] = seccion.upper()
    metadata_dict["subseccion"] = subseccion
    metadata_dict["tipo"] = tipo
    metadata_dict["apartado"] = apartado

    metadata_dict["titulo"] = cve
    metadata_dict["url_pdf"] = pdf_link
    metadata_dict["url_html"] = html_link

    metadata_dict["fecha_publicacion"] = fecha_publicacion
    metadata_dict["fecha_disposicion"] = fecha_publicacion

    metadata_dict["anio"] = datetime.strptime(fecha_publicacion, "%Y-%m-%d").strftime("%Y")

    metadata_dict["mes"] = datetime.strptime(fecha_publicacion, "%Y-%m-%d").strftime("%m")

    metadata_dict["dia"] = datetime.strptime(fecha_publicacion, "%Y-%m-%d").strftime("%d")

    return metadata_dict


def _list_links_day(url: str) -> tp.List[str]:
    """Get a list of links in a BOCM url day filtering by Seccion 1-A, 3 and 4.

    :param url: summary url link. Example: https://www.bocm.es/boletin-completo/BOCM-20240103/2
    :return: list of urls filtered by sections to download
    """
    logger = lg.getLogger(_list_links_day.__name__)

    logger.info("Scrapping day: %s", url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, features="lxml")

    # filter by sections
    sections_to_filter = ["1-A", "3-", "4-"]
    filtered_links = filter_links_by_section(soup, sections_to_filter)
    logger.info("Scrapped day successfully %s (%s BOCM documents)", url, len(filtered_links))

    return filtered_links


class BOCMScrapper(BaseScrapper):
    def download_day(self, day: date) -> tp.List[BOCMMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOCM content for day %s", day)
        day_str = day.strftime("%d/%m/%Y")

        summary_url = _get_summary_link_from_date(day_str)

        metadata_documents = []
        if summary_url is not None:
            logger.info("Got summary url for day %s", day)
            logger.info("URL: [%s] for selected day [%s]", summary_url, day)

            try:
                list_urls = _list_links_day(summary_url)
                for url in list_urls:
                    try:
                        # Skip urls that contains in the path 'boletin'
                        if not re.search("boletin", url):
                            metadata_doc = self.download_document(url)
                            metadata_documents.append(metadata_doc)
                    except HTTPError:
                        logger.error("Not scrapped document %s on day %s", url, day)
                    except AttributeError:
                        logger.error("Not scrapped document %s on day %s", url, day)
            except HTTPError:
                logger.error("Not scrapped document %s on day %s", url, day)
            logger.info("Downloaded all BOCM docs for day %s", day)
        return metadata_documents

    def download_document(self, url: str) -> BOCMMetadataDocument:
        """Get text and metadata from BOCM summary html url document.

        :param url: document url link. Examples:
            * https://www.bocm.es/bocm-20240123-76
            * https://www.bocm.es/bocm-20240123-98
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scrapping document: %s", url)
        session = create_retry_session(retries=5)
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, features="lxml")
        with tempfile.NamedTemporaryFile("w", delete=False) as fn:
            text = soup.select_one("#main").get_text()
            text_cleaned = clean_text(text)
            fn.write(text_cleaned)
        metadata_doc = BOCMMetadataDocument(filepath=fn.name, **_extract_metadata(soup))
        logger.info("Scrapped document successfully %s", url)
        return metadata_doc
