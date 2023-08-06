# To automatize the daily run:
# 1. Rename cron_etl_daily_public.sh to cron_etl_daily.sh
# mv cron_etl_daily_public.sh cron_etl_daily.sh
# 2. Fill the api keys
# 3. Provide permissions to file:
# chmod +x cron_etl_daily.sh
# 4. Copy and paste this file on Crontab
# crontab -e
# Note: Using Ubuntu 22.04 as host probably you find errors like: requests.exceptions.SSLError: HTTPSConnectionPool(host='www.boe.es', port=443): Max retries exceeded with url: /boe/dias/2023/08/02 (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1129)')))
# Solution (Vulnerable to the Man-in-the-Middle): https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled


SHELL=/usr/bin/bash
CRON_TZ=UTC
PROJECT_DIR=/home/ubuntu/ia-boe

20 07 * * * $PROJECT_DIR/cron_etl_daily.sh >> $PROJECT_DIR/logs/ingest_cron.out 2>> $PROJECT_DIR/logs/ingest_cron.err
