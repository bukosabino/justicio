from src.etls.bopgr.processor.line_processor import LineProcessor


class DebugLineProcessor(LineProcessor):
    def test(self, line: str) -> bool:
        print(f"Debug: {line}")
        return False
