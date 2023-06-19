from datetime import date
import logging

from scrapper import download_boe_day
from etl_base import ETL
from initialize import initialize

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger('boelogger')


if __name__ == '__main__':
    INIT_OBJECTS = initialize()
    etl_job = ETL(
        config_loader=INIT_OBJECTS.config_loader,
        vector_store=INIT_OBJECTS.vector_store
    )
    docs = download_boe_day(date.today())
    etl_job.run(docs)
