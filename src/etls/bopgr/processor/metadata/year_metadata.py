import re

from src.etls.bopgr.processor.line_processor import RegexLineProcessor, MetadataProcessor


class YearMetadata(RegexLineProcessor, MetadataProcessor):
    pattern = re.compile(r'Año (\d+)')

    def __init__(self):
        p = re.compile(r'Año (\d+)')
        super().__init__(pattern=p)

    def get_metadata(self, line: str) -> dict:
        return {
            'anio': self.pattern.search(line).group(1)
        }
