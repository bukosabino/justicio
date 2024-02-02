# How to deploy the service in a remote/cloud computer

## 1. Prepare your vector database

At this moment we are working with pinecone as vector database, so, please create an account and an index. Check [the pinecone documentation](https://docs.pinecone.io/docs/overview)

Once you have your pinecone index, please update the `config/config.yaml` :

* vector_store: use the name of the pinecone index that you choose.

Export environment variables:

```
export APP_PATH="."
export SENDGRID_API_KEY=<your_sendgrid_api_key>
export OPENAI_API_KEY=<your_open_api_key>
export TOKENIZERS_PARALLELISM=false
export TAVILY_API_KEY=<your_tavily_api_key>
export QDRANT_API_KEY="<your_qdrant_api_key>"
export QDRANT_API_URL="<your_qdrant_api_url>"
```

Load BOE documents into your vector database (depending on the selected data, may take a few minutes)

```
python -m src.etls.boe.load dates collection_name 2024/01/01 2024/01/31
```

If you want to update the vector database on a daily basis (BOE publishes new documents every day), run this file as a scheduled job (e.g. with CRON).

```
python -m src.etls.boe.load today collection_name
```

If you want to update the vector database on a daily basis (BOE publishes new documents every day), run this file with schedule:

```
python -m src.etls.boe.schedule
```

## 2. Deploy the service

Clone the code:

```
git clone git@github.com:bukosabino/ia-boe.git
```

Install the requirements:

```
sudo apt install python3-virtualenv
virtualenv -p python3 venv3.10
source venv3.10/bin/activate
pip install -r requirements.txt
```

Export environment variables:

```
export APP_PATH="."
export SENDGRID_API_KEY=<your_sendgrid_api_key>
export OPENAI_API_KEY=<your_open_api_key>
export TOKENIZERS_PARALLELISM=false
export TAVILY_API_KEY=<your_tavily_api_key>
export QDRANT_API_KEY="<your_qdrant_api_key>"
export QDRANT_API_URL="<your_qdrant_api_url>"
```

Run the service

```
nohup uvicorn src.service.main:APP --host=0.0.0.0 --port=5001 --workers=2 --timeout-keep-alive=125 --log-level=info > logs/output.out 2>&1 &
```

In the browser

```
http://<your.ip>:5001/docs
```

Monitor the logs of the system

```
tail -n 20 output.out
tail -f output.out
```