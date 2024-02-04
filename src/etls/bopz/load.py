from datetime import date, datetime

import typer

from src.email.send_email import send_email
from src.etls.bopz.scrapper import BOPZScrapper
from src.etls.bopz.defs import COLLECTION_NAME
from src.etls.common.etl import ETL
from src.initialize import initialize_app


app = typer.Typer()
INIT_OBJECTS = initialize_app()


@app.command()
def today():
    etl_job = ETL(config_loader=INIT_OBJECTS.config_loader, vector_store=INIT_OBJECTS.vector_store[COLLECTION_NAME])
    bopz_scrapper = BOPZScrapper()
    day = date.today()
    docs = bopz_scrapper.download_day(day)
    if docs:
        etl_job.run(docs)

    subject = "[BOPZ] Daily ETL executed"
    content = f"""
    Daily ETL executed
    - Date: {day}
    - Documents loaded: {len(docs)} 
    - Database used: {INIT_OBJECTS.config_loader['vector_store']}
    """
    send_email(INIT_OBJECTS.config_loader, subject, content)


@app.command()
def dates(date_start: str, date_end: str):
    etl_job = ETL(config_loader=INIT_OBJECTS.config_loader, vector_store=INIT_OBJECTS.vector_store[COLLECTION_NAME])
    bopz_scrapper = BOPZScrapper()
    docs = bopz_scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    if docs:
        etl_job.run(docs)

    subject = "[BOPZ] Load ETL executed"
    content = f"""
    Load ETL executed
    - Date start: {date_start}
    - Date end: {date_end}
    - Documents loaded: {len(docs)} 
    - Database used: {INIT_OBJECTS.config_loader['vector_store']}
    """
    send_email(INIT_OBJECTS.config_loader, subject, content)


if __name__ == "__main__":
    app()
