import re

from src.etls.bopgr.processor.line_processor import RegexLineProcessor, MetadataProcessor


class SubjectMetadata(RegexLineProcessor, MetadataProcessor):
    def __init__(self):
        p = re.compile(".*NÚMERO ([\d./]+) ([A-Z ÑÜÁÉÍÓÚ\-]+) ?(?:\(\w+\))?(.+)EDICTO", re.DOTALL)
        super().__init__(pattern=p)

    def get_metadata(self, line: str) -> dict:
        groups = self.pattern.search(line).groups()
        return {
            'edicto': groups[0].strip(),
            'entidad': groups[1].strip().replace("\n", ""),
            'provincia': 'Granada',
            'asunto': 'No disponible' if groups[2] is None else groups[2].strip().replace("\n", ""),
        }