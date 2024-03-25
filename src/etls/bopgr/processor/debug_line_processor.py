from src.etls.bopgr.processor.line_processor import MetadataProcessor


class DebugLineProcessor(MetadataProcessor):
    def get_metadata(self, line: str) -> dict:
        pass

    def test(self, line: str) -> bool:
        print(f"Debug: {line}")
        return False
