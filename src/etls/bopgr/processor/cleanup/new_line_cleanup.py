import re

from src.etls.bopgr.processor.line_processor import RegexLineProcessor, CleanUpProcessor


class NewLineCleanUp(RegexLineProcessor, CleanUpProcessor):

    def __init__(self):
        p = re.compile(r'.*\w+[^\S\r\n]*\n')
        super().__init__(pattern=p)

    def clean(self, line: str) -> str:
        return line.strip() + " "
