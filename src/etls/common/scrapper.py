import copy
import logging as lg
import typing as tp
from abc import ABC, abstractmethod
from datetime import date, timedelta

from src.etls.common.metadata import MetadataDocument
from src.initialize import initialize_logging

initialize_logging()


class BaseScrapper(ABC):
    def download_days(self, date_start: date, date_end: date) -> tp.List[MetadataDocument]:
        """Download all the documents between two dates (from date_start to date_end)"""
        logger = lg.getLogger(self.download_days.__name__)
        logger.info("Downloading content from day %s to %s", date_start, date_end)
        delta = timedelta(days=1)
        docs = []
        date_start_aux = copy.copy(date_start)
        while date_start_aux <= date_end:
            docs += self.download_day(date_start_aux)
            date_start_aux += delta
        logger.info("Downloaded content from day %s to %s", date_start, date_end)
        return docs

    @abstractmethod
    def download_day(self, day: date) -> tp.List[MetadataDocument]:
        """Download all the documents for a specific date."""
        pass

    @abstractmethod
    def download_document(self, url: str) -> MetadataDocument:
        """Get text and metadata from url document."""
        pass
