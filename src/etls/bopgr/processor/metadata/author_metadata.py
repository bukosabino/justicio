import re

from src.etls.bopgr.processor.line_processor import MetadataProcessor, RegexLineProcessor


class AuthorMetadata(RegexLineProcessor, MetadataProcessor):
    def __init__(self):
        p = re.compile(r'.*Administración: (.+?)\..*Domicilio: (.+?)\..*Tel\.: (\d{3} \d{6}) / Fax: (\d{3} \d{6})')
        super().__init__(pattern=p)

    def get_metadata(self, line: str) -> dict:
        return {
            'administracion': self.pattern.search(line).group(1),
            'direccion': self.pattern.search(line).group(2),
            'telefono': self.pattern.search(line).group(3),
            'fax': self.pattern.search(line).group(4)
        }
