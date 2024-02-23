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

class ScrapeError(Exception):
    """
    Excepción personalizada para errores de scrapeo.
    """

    def __init__(self, message="Error durante el proceso de scraping", *args, **kwargs):
        """
        Inicializa la excepción con un mensaje de error personalizado.

        :param message: Mensaje de error que describe el fallo.
        :param args: Argumentos posicionales adicionales.
        :param kwargs: Argumentos de palabra clave adicionales.
        """
        super().__init__(message, *args, **kwargs)
        self.message = message

    def __str__(self):
        """
        Devuelve una representación en string de la excepción, que incluye el mensaje de error.
        """
        return f"ScrapeError: {self.message}"