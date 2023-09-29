import typing as tp
from abc import ABC, abstractmethod
from datetime import date

from src.etls.utils import BOEMetadataDocument


class BaseScrapper(ABC):

    @abstractmethod
    def download_days(self, date_start: date, date_end: date) -> tp.List[BOEMetadataDocument]:
        """Download all the documents between two dates (from date_start to date_end)
        """
        pass

    @abstractmethod
    def download_day(self, day: date) -> tp.List[BOEMetadataDocument]:
        """Download all the documents for a specific date.
        """
        pass

    @abstractmethod
    def download_document(self, url: str) -> BOEMetadataDocument:
        """Get text and metadata from a BOE xml url document.

        :param url: document url link. Examples:
            * https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-14630
            * https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-12203
        :return: document with metadata and filepath with text content
        """
        pass
