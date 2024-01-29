#!/bin/bash

export APP_PATH="."
export SENDGRID_API_KEY="<your_sendgrid_api_key>"
export OPENAI_API_KEY="<your_open_api_key>"
export TOKENIZERS_PARALLELISM=false
export TAVILY_API_KEY="<your_tavily_api_key>"
export QDRANT_API_KEY="<your_supabase_api_key>"
export QDRANT_API_URL="<your_supabase_api_url>"


cd ia-boe/
source venv3.9/bin/activate
pip install -r requirements.txt
python -m src.etls.boe.load.daily
