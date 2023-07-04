from src.etls.etl_common import ETL
from src.initialize import initialize_app
from src.etls.scrapper.boe import BOEScrapper

if __name__ == '__main__':
    INIT_OBJECTS = initialize_app()
    etl_job = ETL(
        config_loader=INIT_OBJECTS.config_loader,
        vector_store=INIT_OBJECTS.vector_store
    )
    boe_scrapper = BOEScrapper()
    """
    docs = boe_scrapper.download_days(
        date_start=datetime.strptime(INIT_OBJECTS.config_loader['date_start'], '%Y/%m/%d').date(),
        date_end=datetime.strptime(INIT_OBJECTS.config_loader['date_end'], '%Y/%m/%d').date(),
    )
    """
    docs = [boe_scrapper.download_document("https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-14630")]
    etl_job.run(docs)
