from datetime import date, datetime

import typer

from src.email.send_email import send_email
from src.etls.template.scrapper import TemplateScrapper
from src.etls.common.etl import ETL
from src.etls.template.defs import COLLECTION_NAME
from src.initialize import initialize_app


app = typer.Typer()


@app.command()
def today(init_objects=None):
    if init_objects is None:
        init_objects = initialize_app()
    etl_job = ETL(config_loader=init_objects.config_loader, vector_store=init_objects.vector_store[COLLECTION_NAME])
    boe_scrapper = TemplateScrapper()
    day = date.today()
    docs = boe_scrapper.download_day(day)
    if docs:
        etl_job.run(docs)

    subject = "Today ETL executed"
    content = f"""
        Today ETL executed
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
    scrapper = TemplateScrapper()
    docs = scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    if docs:
        etl_job.run(docs)

    subject = "Load ETL executed"
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
