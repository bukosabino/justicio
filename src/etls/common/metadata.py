from pydantic import BaseModel


class MetadataDocument(BaseModel):
    # Source
    source_name: str
    source_type: str
