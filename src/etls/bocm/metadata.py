import typing as tp
from datetime import datetime

from pydantic import BaseModel, field_validator, Field
import re

from src.etls.common.metadata import MetadataDocument


# REGEX
CVE_REGEX = r"^BOCM-\d{8}-\d{1,3}$"  # TODO: regex demasiado laxa


class BOCMMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a BOCM Document scrapped."""

    # Text
    filepath: str

    # Source
    source_name: str = "BOCM"
    source_type: str = "Boletin"

    # Metadatos
    identificador: str = Field(pattern=CVE_REGEX, examples=["BOCM-20240129-24"])
    numero_oficial: str = ""  # Número de boletín
    paginas: str
    departamento: str  # órgano (excepto sección 4, que no tiene)

    seccion_normalizada: str
    seccion: str
    subseccion: str
    tipo: str = ""
    apartado: str = ""
    rango: str = ""

    # Links
    titulo: str  # title
    url_pdf: str  # pdf_link
    url_html: str  # html_link

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
            return datetime.strptime(v, "%Y-%m-%d").strftime("%Y-%m-%d")
        return v
