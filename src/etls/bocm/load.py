from datetime import date, datetime

import typer

from src.email.send_email import send_email
from src.etls.bocm.scrapper import BOCMScrapper
from src.etls.common.etl import ETL
from src.etls.utils import catch_exceptions
from src.etls.bocm.defs import COLLECTION_NAME
from src.initialize import initialize_app


app = typer.Typer()


@app.command()
@catch_exceptions(cancel_on_failure=True)
def today(init_objects=None):
    if init_objects is None:
        init_objects = initialize_app()
    etl_job = ETL(config_loader=init_objects.config_loader, vector_store=init_objects.vector_store[COLLECTION_NAME])
    bocm_scrapper = BOCMScrapper()
    day = date.today()
    docs = bocm_scrapper.download_day(day)
    if docs:
        etl_job.run(docs)

    subject = "[BOCM] Daily ETL executed"
    content = f"""
    Daily ETL executed
    - Date: {day}
    - Documents loaded: {len(docs)} 
    - Database used: {init_objects.config_loader['vector_store']}
    """
    send_email(init_objects.config_loader, subject, content)


@app.command()
def dates(date_start: str, date_end: str, init_objects=None):
    if init_objects is None:
        init_objects = initialize_app()
    etl_job = ETL(config_loader=init_objects.config_loader, vector_store=init_objects.vector_store[COLLECTION_NAME])
    bocm_scrapper = BOCMScrapper()
    docs = bocm_scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    if docs:
        etl_job.run(docs)

    subject = "[BOCM] Load ETL executed"
    content = f"""
    Load ETL executed
    - Date start: {date_start}
    - Date end: {date_end}
    - Documents loaded: {len(docs)} 
    - Database used: {init_objects.config_loader['vector_store']}
    """
    send_email(init_objects.config_loader, subject, content)


if __name__ == "__main__":
    app()
