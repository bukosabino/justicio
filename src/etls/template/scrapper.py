"""
Define a class with some methods (download_day, download_document) to scrape the information.
"""

import typing as tp
from datetime import date

from src.etls.common.scrapper import BaseScrapper
from src.etls.template.metadata import TemplateMetadataDocument
from src.initialize import initialize_logging

initialize_logging()


class TemplateScrapper(BaseScrapper):
    def download_day(self, day: date) -> tp.List[TemplateMetadataDocument]:
        """
        Define how to navigate between documents for a single day
        """
        pass

    def download_document(self, url: str) -> TemplateMetadataDocument:
        """
        Define how a single document is scrapped
        """
        pass
