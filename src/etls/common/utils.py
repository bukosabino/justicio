import typing as tp

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


class TextLoader(BaseLoader):
    """Load text files."""

    def __init__(
        self,
        file_path: str,
        encoding: tp.Optional[str] = None,
        metadata: tp.Optional[dict] = None,
    ):
        """Initialize with file path."""
        self.file_path = file_path
        self.encoding = encoding
        self.metadata = metadata

    def load(self) -> tp.List[Document]:
        """Load from file path."""
        with open(self.file_path, encoding=self.encoding) as f:
            text = f.read()
        return [Document(page_content=text, metadata=self.metadata)]
