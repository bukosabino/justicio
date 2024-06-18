from datetime import datetime
from typing import Optional

from src.etls.common.metadata import MetadataDocument




class BOJAMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a BOJA Document scrapped."""    

    # Text
    filepath: str

    # Source
    source_name: str = "BOJA"
    source_type: str = "Boletin"

    # Metadatos
    identificador: str
    departamento: str
    tipologia: str   

    # Links
    titulo: Optional[str] = None
    url_pdf: str  # pdf_link
    url_html: Optional[str] = None
    url_boletin: Optional[str] = None

    fecha_disposicion: Optional[str] = None
    anio: Optional[str] = None
    mes: Optional[str] = None
    dia: Optional[str] = None

    datetime_insert: str = datetime.utcnow().isoformat()

