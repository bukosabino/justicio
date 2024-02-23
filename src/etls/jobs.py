import time

import schedule

from src.etls.boe.load import today as boe_today
from src.etls.bopz.load import today as bopz_today
from src.etls.bocm.load import today as bocm_today
from src.etls.bopv.load import today as bopv_today
from src.initialize import initialize_app


INIT_OBJECTS = initialize_app()


schedule.every().day.at("11:00").do(boe_today, init_objects=INIT_OBJECTS)
schedule.every().day.at("11:05").do(bopz_today, init_objects=INIT_OBJECTS)
schedule.every().day.at("11:10").do(bocm_today, init_objects=INIT_OBJECTS)
schedule.every().day.at("11:15").do(bopv_today, init_objects=INIT_OBJECTS)
# TODO: monthly jobs

while True:
    schedule.run_pending()
    time.sleep(1)
