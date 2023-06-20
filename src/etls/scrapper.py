import logging as lg
import typing as tp
import tempfile
from datetime import date, timedelta
import unicodedata

from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError

from utils import BOEMetadataDocument
from initialize import setup_logging


setup_logging()


def download_boe_days(date_start: date, date_end: date):
    """Download all the BOE documents from date_start to date_end

    :param date_start:
    :param date_end:
    :return:
    """
    logger = lg.getLogger(download_boe_days.__name__)
    logger.info("Downloading BOE content from day %s to %s", date_start, date_end)
    delta = timedelta(days=1)
    metadata_documents = []
    while date_start <= date_end:
        boe_docs = download_boe_day(date_start)
        metadata_documents += boe_docs
        date_start += delta
    logger.info("Downloaded BOE content from day %s to %s", date_start, date_end)
    return metadata_documents


def download_boe_day(day: date) -> tp.List[BOEMetadataDocument]:
    """Download all the BOE documents for a date.

    :param day:
    :return:
    """
    logger = lg.getLogger(download_boe_day.__name__)
    logger.info("Downloading BOE content for day %s", day)
    day_str = day.strftime("%Y/%m/%d")
    day_url = f"https://www.boe.es/boe/dias/{day_str}"
    metadata_documents = []
    try:
        id_links = _list_links_day(day_url)
        for id_link in id_links:
            # TODO: versión mejorada... splitting by articles...
            # url_document = f"https://www.boe.es/buscar/act.php?id={id_link}"
            url_document = f"https://www.boe.es/diario_boe/txt.php?id={id_link}"
            try:
                metadata_doc = download_boe_document(url_document)
                metadata_doc.date_doc = day.isoformat()
                metadata_documents.append(metadata_doc)
                # logger.error("Scrapped document %s on day %s", url_document, day_url)
            except HTTPError:
                logger.error("Not scrapped document %s on day %s", url_document, day_url)
    except HTTPError:
        logger.error("Not scrapped document %s on day %s", url_document, day_url)
    logger.info("Downloaded BOE content for day %s", day)
    return metadata_documents


def download_boe_document(url: str) -> BOEMetadataDocument:
    """Get a text document from a BOE url document.

    :param url: document url link. Example: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-14630
    :return: document with text content
    """
    logger = lg.getLogger(download_boe_document.__name__)
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
    metadata_doc = BOEMetadataDocument(
        filepath=fn.name,
        title=title,
        url=url,
        document_id=url.split('?id=')[-1]
    )
    logger.info("Scrapped document successfully %s", url)
    return metadata_doc


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
