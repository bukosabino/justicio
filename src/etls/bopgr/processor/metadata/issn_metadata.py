import re

from src.etls.bopgr.processor.line_processor import RegexLineProcessor, MetadataProcessor


class ISSNMetadata(RegexLineProcessor, MetadataProcessor):

    def __init__(self):
        p = re.compile(r'.*DL GR (.+?)\..*I\.S\.S\.N\.: (.+?)\..*Edición.*')
        super().__init__(pattern=p)

    def get_metadata(self, line: str) -> dict:
        return {
            'legal_deposit': self.pattern.search(line).group(1),
            'issn': self.pattern.search(line).group(2),
        }
