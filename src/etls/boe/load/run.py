from datetime import datetime

from src.email.send_email import send_email
from src.etls.boe.scrapper import BOEScrapper
from src.etls.common.etl import ETL
from src.initialize import initialize_app

if __name__ == "__main__":
    INIT_OBJECTS = initialize_app()
    etl_job = ETL(
        config_loader=INIT_OBJECTS.config_loader, vector_store=INIT_OBJECTS.vector_store
    )
    boe_scrapper = BOEScrapper()
    docs = boe_scrapper.download_days(
        date_start=datetime.strptime(
            INIT_OBJECTS.config_loader["date_start"], "%Y/%m/%d"
        ).date(),
        date_end=datetime.strptime(
            INIT_OBJECTS.config_loader["date_end"], "%Y/%m/%d"
        ).date(),
    )
    if docs:
        etl_job.run(docs)

    subject = "[BOE] Load ETL executed"
    content = f"""
    Load ETL executed
    - Date start: {INIT_OBJECTS.config_loader['date_start']}
    - Date end: {INIT_OBJECTS.config_loader['date_end']}
    - Documents loaded: {len(docs)} 
    - Database used: {INIT_OBJECTS.config_loader['vector_store']}
    """
    send_email(INIT_OBJECTS.config_loader, subject, content)
