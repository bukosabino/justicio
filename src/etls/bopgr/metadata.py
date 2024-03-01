from datetime import datetime
from typing import Optional

from pydantic import field_validator

from src.etls.common.metadata import MetadataDocument


class BOPGRMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a BOPGR Document scrapped."""

    # Text
    filepath: str

    # Source
    source_name: str = "BOPGR"
    source_type: str = "Boletin"

    # Metadatos
    identificador: str
    numero_oficial: str = ""
    departamento: str = ""
    titulo: str = ""
    url_pdf: str = ""
    url_html: str = ""
    fecha_publicacion: str
    fecha_disposicion: str = ""
    anio: str = ""
    mes: str = ""
    dia: str = ""
    entidad: Optional[str]
    provincia: Optional[str]
    asunto: Optional[str]
    edicto: Optional[str]

    legal_deposit: Optional[str]
    issn: Optional[str]
    administracion: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]
    fax: Optional[str]

    # Analisis
    materia: Optional[str]

    datetime_insert: str = datetime.utcnow().isoformat()

    @field_validator("fecha_publicacion", "fecha_disposicion")
    @classmethod
    def isoformat(cls, v):
        if v:
            datetime.strptime(v, "%Y-%m-%d")
        return v
