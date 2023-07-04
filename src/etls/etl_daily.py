from datetime import date

from src.etls.etl_common import ETL
from src.etls.scrapper.boe import BOEScrapper
from src.initialize import initialize_app


if __name__ == '__main__':
    INIT_OBJECTS = initialize_app()
    etl_job = ETL(
        config_loader=INIT_OBJECTS.config_loader,
        vector_store=INIT_OBJECTS.vector_store
    )
    boe_scrapper = BOEScrapper()
    docs = boe_scrapper.download_day(date.today())
    etl_job.run(docs)
