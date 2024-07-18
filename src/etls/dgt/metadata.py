from datetime import datetime
from pydantic import field_validator

from src.etls.common.metadata import MetadataDocument


class DGTMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a DGT Document scrapped."""

    # Text
    filepath: str

    # Source
    source_name: str = "DGT"
    source_type: str 

    # Metadatos
    identificador: str
    numero_consulta: str
    organo: str
    normativa: str = ""
    url_html: str
    fecha_publicacion: str
    fecha_disposicion: str = ""
    anio: str
    mes: str
    dia: str

    datetime_insert: str = datetime.utcnow().isoformat()

    @field_validator("fecha_publicacion", "fecha_disposicion")
    @classmethod
    def isoformat(cls, v):
        if v:
            datetime.strptime(v, "%Y-%m-%d")
        return v
