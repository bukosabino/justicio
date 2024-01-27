import typing as tp
from datetime import datetime

from pydantic import BaseModel, field_validator
import re

from src.etls.common.metadata import MetadataDocument


# TODO: regex demasiado laxa
CVE_REGEX = r'^BOCM-\d{8}-\d{1,3}$'

class BOCMMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a BOCM Document scrapped."""

    # Text
    filepath: str

    # Source
    source_name: str = "BOCM"
    source_type: str = "Boletin"

    # Metadatos
    identificador: str # CVE
    numero_oficial: str = "" # Número de boletín
    departamento: str # órgano (excepto sección 4, que no tiene)
    seccion: str # sección
    seccion_full: str
    rango: str = "" # rango
    titulo: str # title
    url_pdf: str # pdf_link
    url_html: str # html_link
    origen_legislativo: str = "" # En función de sección
    fecha_publicacion: str
    fecha_disposicion: str = ""
    anio: str
    mes: str
    dia: str
    paginas: str

    datetime_insert: str = datetime.utcnow().isoformat()

    @field_validator("fecha_publicacion", "fecha_disposicion")
    @classmethod
    def isoformat(cls, v):
        if v:
            return datetime.strptime(v, "%Y-%m-%d").strftime("%Y-%m-%d")
        return v

    @field_validator("identificador")
    @classmethod
    def cve(cls, v):
        if not re.fullmatch(CVE_REGEX, v): 
            raise ValueError(f"{v} is not a valid CVE")
        return v
