from dataclasses import dataclass
from datetime import datetime, date
import typing as tp

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


@dataclass
class BOEMetadataDocument:
    """Class for keeping metadata of a BOE Document scrapped."""
    filepath: str
    title: str
    url: str
    document_id: str
    date_doc: str = date.today().isoformat()
    datetime_insert: str = datetime.utcnow().isoformat()

    def load_metadata(self) -> dict:
        metadata_dict = {
            'title': self.title,
            'url': self.url,
            'document_id': self.document_id,
            'date_doc': self.date_doc,
            'datetime_insert': self.datetime_insert
        }
        return metadata_dict


class BOETextLoader(BaseLoader):
    """Load text files."""

    def __init__(self, file_path: str, encoding: tp.Optional[str] = None, metadata: tp.Optional[dict] = None):
        """Initialize with file path."""
        self.file_path = file_path
        self.encoding = encoding
        self.metadata = metadata

    def load(self) -> tp.List[Document]:
        """Load from file path."""
        with open(self.file_path, encoding=self.encoding) as f:
            text = f.read()
        return [Document(page_content=text, metadata=self.metadata)]
