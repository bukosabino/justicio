import time

import schedule

from src.etls.boe.load import today


schedule.every().day.at("11:00").do(today, collection_name="<template>")

while True:
    schedule.run_pending()
    time.sleep(1)
