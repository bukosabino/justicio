import logging as lg
import os
import tempfile
import typing as tp

import requests
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

from src.etls.bopgr.metadata import BOPGRMetadataDocument
from src.etls.bopgr.processor.line_processor import MetadataProcessor, CleanUpProcessor, LineProcessor


def pdf_download(url, temp_directory):
    """
    Download a PDF file from a given URL.

    Args:
        url (str): The URL of the PDF file.
        temp_directory (str): The temporary directory to store the downloaded file.

    Returns:
        str: The path to the downloaded PDF file or None if the download fails.
    """
    logger = lg.getLogger(pdf_download.__name__)
    response = requests.get(url)

    # Bad server implementation, returns 200 if file does not exist.
    if response.status_code == 200 and len(response.content) > 0:
        with tempfile.NamedTemporaryFile(dir=temp_directory, suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(response.content)
            pdf_path = temp_pdf.name
            logger.info(f"Downloaded PDF from {url} to {pdf_path}.")
        return pdf_path
    else:
        logger.warning(f"Can not download the URL {url}. Status code: {response.status_code}")
        return None


def text_extract(pdf_path: str, temp_directory: str, laparams=tp.Optional[LAParams]):
    """
    Download a PDF file from a given URL.

    :param str url: The URL of the PDF file.
    :param str temp_directory: The temporary directory to store the downloaded file.

    :return: The path to the downloaded PDF file or None if the download fails.
    :rtype: str or None
    """
    logger = lg.getLogger(text_extract.__name__)
    text = extract_text(pdf_path, laparams=laparams)
    logger.debug(f"PDF {pdf_path} has been extracted: \n{text}\n")

    fd, text_path = tempfile.mkstemp(dir=temp_directory, suffix=".txt")
    with os.fdopen(fd, 'w', encoding='utf-8') as temp_text:
        temp_text.write(text)
        logger.info(f"PDF {pdf_path} has been stored as text in {text_path}.")
    return text_path


def process_bulletin(text_path:str,
                     metadata: dict,
                     metadata_processors: tp.List[MetadataProcessor],
                     clean_up_processors: tp.List[CleanUpProcessor],
                     skip_processors: tp.List[LineProcessor],
                     new_content_detector: LineProcessor
                     ) -> tp.List[BOPGRMetadataDocument]:
    """
    Process a bulletin, extracting metadata and relevant content.

    :param str text_path: The path to the text file containing the bulletin content.
    :param dict metadata: Metadata dictionary to be populated.
    :param List[MetadataProcessor] metadata_processors: List of processors for extracting metadata.
    :param List[CleanUpProcessor] clean_up_processors: List of processors for cleaning up content.
    :param List[LineProcessor] skip_processors: List of processors for lines that should be skipped.
    :param LineProcessor new_content_detector: Processor for detecting new content.

    :return: List of BOPGRMetadataDocument objects representing processed bulletins.
    :rtype: List[BOPGRMetadataDocument]
    """
    metadata_documents = []
    new_content = False
    with open(text_path, 'r', encoding='utf-8') as file:
        content = None
        for line in file:
            if any(skip_line.test(line) for skip_line in skip_processors):
                continue

            process_content = True
            for processor in metadata_processors:
                if processor.test(line):
                    metadata = metadata | processor.get_metadata(line)
                    process_content = processor.include_line()
                    break
            if not process_content:
                continue

            if new_content_detector.test(line):
                new_content = True
                if content:
                    meta = BOPGRMetadataDocument(materia=content, **metadata)
                    metadata_documents.append(meta)
                content = ""

            if new_content:
                for processor in clean_up_processors:
                    if processor.test(line):
                        line = processor.clean(line)
                content += line
    return metadata_documents

