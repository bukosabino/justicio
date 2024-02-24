import re
from src.etls.bopgr.processor.line_processor import RegexLineProcessor, CleanUpProcessor


class HyphensLineCleanUp(RegexLineProcessor, CleanUpProcessor):

    def __init__(self):
        p = re.compile(r'-\n$')
        super().__init__(pattern=p)

    def clean(self, line: str) -> str:
        return _replace_last_occurrence(line, "-\n", "")


def _replace_last_occurrence(input_string, text_to_replace, new_text):
    last_occurrence = input_string.rfind(text_to_replace)

    if last_occurrence != -1:
        modified_string = input_string[:last_occurrence] + new_text + input_string[last_occurrence + len(text_to_replace):]
        return modified_string
    else:
        # If no occurrence is found, return the original string
        return input_string