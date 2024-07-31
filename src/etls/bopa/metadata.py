from datetime import datetime
from typing import Optional
from src.etls.common.metadata import MetadataDocument

class BOPAMetadataDocument(MetadataDocument):
    # Class for keeping metadata of a BOPA Document scrapped

    # Source
    source_name: str = "BOPA"
    source_type: str = "Boletin"

    # Metadata (TBD)

    disposition_date: str
    reference_number: str
    section_name: str
    department_name: str
    content: str