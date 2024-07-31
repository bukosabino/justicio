from datetime import date, datetime
import json

import typer

from src.email.send_email import send_email
from src.etls.bopv.scrapper import BOPVScrapper
from src.etls.bopv.defs import COLLECTION_NAME
from src.etls.common.etl import ETL
from src.initialize import initialize_app

# TBD