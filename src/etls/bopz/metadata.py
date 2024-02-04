import typing as tp
from datetime import datetime

from pydantic import field_validator

from src.etls.common.metadata import MetadataDocument


class BOPZMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a BOPZ Document scrapped."""

    # Text
    filepath: str

    # Source
    source_name: str = "BOPZ"
    source_type: str = "Boletin"

    # Metadatos
    identificador: str
    numero_oficial: str = ""
    departamento: str
    titulo: str = ""
    url_pdf: str
    url_html: str
    fecha_publicacion: str
    fecha_disposicion: str = ""
    anio: str
    mes: str
    dia: str

    # Analisis
    materia: tp.List[str]

    datetime_insert: str = datetime.utcnow().isoformat()

    @field_validator("fecha_publicacion", "fecha_disposicion")
    @classmethod
    def isoformat(cls, v):
        if v:
            datetime.strptime(v, "%Y-%m-%d")
        return v
