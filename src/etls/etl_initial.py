from datetime import datetime

from src.etls.etl_common import ETL
from src.initialize import initialize_app
from src.etls.scrapper.boe import BOEScrapper
from src.email.send_email import send_email


if __name__ == '__main__':
    INIT_OBJECTS = initialize_app()
    etl_job = ETL(
        config_loader=INIT_OBJECTS.config_loader,
        vector_store=INIT_OBJECTS.vector_store
    )
    boe_scrapper = BOEScrapper()
    docs = boe_scrapper.download_days(
        date_start=datetime.strptime(INIT_OBJECTS.config_loader['date_start'], '%Y/%m/%d').date(),
        date_end=datetime.strptime(INIT_OBJECTS.config_loader['date_end'], '%Y/%m/%d').date(),
    )
    # docs = [boe_scrapper.download_document("https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-14630")]
    etl_job.run(docs)

    subject = "Initial ETL executed"
    content = f"""
    Initial ETL executed
    - Date start: {INIT_OBJECTS.config_loader['date_start']}
    - Date end: {INIT_OBJECTS.config_loader['date_end']}
    - Documents loaded: {len(docs)} 
    """
    send_email(INIT_OBJECTS.config_loader, subject, content)
