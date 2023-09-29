import typing as tp
from dataclasses import dataclass
from datetime import date, datetime

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from pydantic import field_validator, BaseModel


@dataclass
class BOEMetadataDocument2:
    # NOTE: deprecated
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


class BOEMetadataReferencia(BaseModel):
    id: str
    palabra: str
    texto: str


class BOEMetadataDocument(BaseModel):
    """Class for keeping metadata of a BOE Document scrapped."""
    # Text
    filepath: str

    # Metadatos
    identificador: str
    numero_oficial: str = ''
    departamento: str
    rango: str = ''
    titulo: str
    url_pdf: str
    origen_legislativo: str = ''
    fecha_publicacion: str
    fecha_disposicion: str = ''
    anio: str

    # Analisis
    observaciones: str = ''
    ambito_geografico: str = ''
    modalidad: str = ''
    tipo: str = ''
    materias: tp.List[str]
    alertas: tp.List[str]
    notas: tp.List[str]
    ref_posteriores: tp.List[BOEMetadataReferencia]
    ref_anteriores: tp.List[BOEMetadataReferencia]

    datetime_insert: str = datetime.utcnow().isoformat()

    @field_validator("ref_posteriores")
    @classmethod
    def ref_posteriores_to_json(cls, validators):
        return [v.json() for v in validators]

    @field_validator("ref_anteriores")
    @classmethod
    def ref_anteriores_to_json(cls, validators):
        return [v.json() for v in validators]

    @field_validator("fecha_publicacion", "fecha_disposicion")
    @classmethod
    def isoformat(cls, v):
        if v:
            return datetime.strptime(v, '%Y%m%d').strftime('%Y-%m-%d')
        return v


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
