from datetime import datetime
from typing import Optional

from src.etls.common.metadata import MetadataDocument


class BOAMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a BOA Document scrapped."""

    # Text
    filepath: str

    # Source
    source_name: str = "BOA"
    source_type: str = "Boletin"

    # Metadatos
    numero_boletin: str 
    identificador: str # DOCN
    departamento: Optional[str] = None 
    seccion: Optional[str] = None 
    subseccion: Optional[str] = None 
    rango: Optional[str] = None 
    codigo_materia: Optional[str] = None 

    # Links
    titulo: Optional[str] = None 
    url_pdf: str  
    url_boletin: Optional[str] = None

    fecha_disposicion: str = "" 
    fecha_publicacion: str = ""
    anio: Optional[str] = None
    mes: Optional[str] = None
    dia: Optional[str] = None

    datetime_insert: str = datetime.utcnow().isoformat()

