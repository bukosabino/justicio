import logging as lg
import re
import tempfile
import typing as tp
from datetime import date

from pdfminer.layout import LAParams

from src.etls.bopgr.metadata import BOPGRMetadataDocument
from src.etls.bopgr.pdf_processor import pdf_download, text_extract, process_bulletin
from src.etls.bopgr.processor.cleanup.hyphens_line_cleanup import HyphensLineCleanUp
from src.etls.bopgr.processor.cleanup.new_line_cleanup import NewLineCleanUp
from src.etls.bopgr.processor.metadata.author_metadata import AuthorMetadata
from src.etls.bopgr.processor.metadata.bulletin_number_metadata import BulletinNumberMetadata
from src.etls.bopgr.processor.metadata.issn_metadata import ISSNMetadata
from src.etls.bopgr.processor.metadata.year_metadata import YearMetadata
from src.etls.bopgr.processor.line_processor import RegexLineProcessor
from src.etls.common.scrapper import BaseScrapper
from src.initialize import initialize_logging

initialize_logging()


class BOPGRScrapper(BaseScrapper):
    metadata_processors = [
        YearMetadata(),
        ISSNMetadata(),
        AuthorMetadata(),
        BulletinNumberMetadata(),
        #DebugLineProcessor()
    ]

    clean_up_processors = [
        HyphensLineCleanUp(),
        NewLineCleanUp(),
    ]

    skip_line_processors = [
        RegexLineProcessor(re.compile(r' *Página +\d+ *')),
        RegexLineProcessor(re.compile(r' *n\n')),
        RegexLineProcessor(re.compile(r' *Granada,.* \d{4}\n')),
    ]

    def download_day(self, day: date) -> tp.List[BOPGRMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOPGR content for day %s", day)
        day_str = day.strftime("%d/%m/%Y")
        metadata_documents = self.download_document(
            f"https://bop2.dipgra.es/opencms/opencms/portal/DescargaPDFBoletin?fecha={day_str}",
            day.strftime('%Y-%m-%d'))
        if len(metadata_documents) == 0:
            logger.error("Not scrapped document on day %s", day_str)
        else:
            logger.info("Downloaded BOPGR content for day %s", day_str)
        return metadata_documents

    def download_document(self, url: str, day: str = None) -> tp.List[BOPGRMetadataDocument]:
        """Get text and metadata from a BOPGR document.

        :param url: document url link. Examples:
            * https://bop2.dipgra.es/opencms/opencms/portal/DescargaPDFBoletin?fecha=21/02/2024
        :metadata BOPGRMetadataDocument: document metadata associated with url download link.
        :param day: day to download.
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_document.__name__)

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = pdf_download(url=url, temp_directory=temp_dir)

            if pdf_path:

                text_path = text_extract(pdf_path, temp_dir, laparams=LAParams(char_margin=4.0, line_margin=2.0))
                logger.debug(f"Bulletin downloaded and the text has been extracted in {text_path}.\n")

                metadata = {
                    'filepath': pdf_path,
                    'url_pdf': url,
                    'fecha_publicacion': day
                }

                return process_bulletin(text_path=text_path,
                                        metadata=metadata,
                                        metadata_processors=self.metadata_processors,
                                        clean_up_processors=self.clean_up_processors,
                                        new_content_detector=RegexLineProcessor(re.compile(r'^NÚMERO (\d+) $')),
                                        skip_processors=self.skip_line_processors)
            else:
                return []
