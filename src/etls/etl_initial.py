from datetime import datetime, date
import logging

from scrapper import download_boe_day, download_boe_days, download_boe_document
# from src.utils import timeit
from etl_base import ETL
from src.initialize import initialize

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger('boelogger')


if __name__ == '__main__':
    INIT_OBJECTS = initialize()
    etl_job = ETL(
        config_loader=INIT_OBJECTS.config_loader,
        vector_store=INIT_OBJECTS.vector_store
    )
    """
    docs = download_boe_days(
        datetime.strptime(INIT_OBJECTS.config_loader['start_date'], '%Y/%m/%d').date(),
        date.today()
    )
    """
    # docs = download_boe_days(date(2022, 1, 1), date(2022, 12, 31))
    # docs = download_boe_day(date(2022, 9, 7))
    docs = [download_boe_document("https://www.boe.es/diario_boe/txt.php?id=BOE-A-2022-14630")]
    etl_job.run(docs)
