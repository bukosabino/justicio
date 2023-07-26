from datetime import date

from src.etls.etl_common import ETL
from src.etls.scrapper.boe import BOEScrapper
from src.initialize import initialize_app
from src.email.send_email import send_email


if __name__ == '__main__':
    INIT_OBJECTS = initialize_app()
    etl_job = ETL(
        config_loader=INIT_OBJECTS.config_loader,
        vector_store=INIT_OBJECTS.vector_store
    )
    boe_scrapper = BOEScrapper()
    day = date.today()
    docs = boe_scrapper.download_day(day)
    etl_job.run(docs)

    subject = "Daily ETL executed"
    content = f"""
    Daily ETL executed
    - Date: {day.strftime("%Y/%m/%d")}
    - Documents loaded: {len(docs)} 
    """
    send_email(INIT_OBJECTS.config_loader, subject, content)
