#!/bin/bash

export PINECONE_API_KEY="<your_pinecone_api_key>"
export PINECONE_ENV="<your_pinecone_env>"
export OPENAI_API_KEY="<your_open_api_key>"
export SENDGRID_API_KEY="<your_sendgrid_api_key>"
export APP_PATH="."

cd ia-boe/
source venv3.9/bin/activate
pip install -r requirements.txt
python -m src.etls.etl_daily
