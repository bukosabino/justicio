import re

from src.etls.bopgr.processor.line_processor import RegexLineProcessor, MetadataProcessor


class BulletinNumberMetadata(RegexLineProcessor, MetadataProcessor):
    def __init__(self):
        p = re.compile(r'B\.O\.P\..*número *(\d+)')
        super().__init__(pattern=p)

    def get_metadata(self, line: str) -> dict:
        return {
            'identificador': self.pattern.search(line).group(1),
        }
