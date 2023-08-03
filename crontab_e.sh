# To automatize the daily run:
# 1. Rename cron_etl_daily_public.sh to cron_etl_daily.sh
# mv cron_etl_daily_public.sh cron_etl_daily.sh
# 2. Fill the api keys
# 3. Provide permissions to file:
# chmod +x cron_etl_daily.sh
# 4. Copy and paste this file on Crontab
# crontab -e

SHELL=/usr/bin/bash
CRON_TZ=UTC
PROJECT_DIR=/home/ubuntu/ia-boe

20 07 * * * $PROJECT_DIR/cron_etl_daily.sh >> $PROJECT_DIR/logs/ingest_cron.out 2>> $PROJECT_DIR/logs/ingest_cron.err
