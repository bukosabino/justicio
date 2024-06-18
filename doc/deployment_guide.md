# How to deploy the service in local

## 1. Prepare your vector database in local

At this moment, we are working with Qdrant as vector database.

Official doc: https://qdrant.tech/documentation/quick-start/

### Download the latest Qdrant image from Dockerhub:

```
docker pull qdrant/qdrant
```

### Run the service:

```
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/config/example_qdrant_local.yaml:/qdrant/config/production.yaml -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

* REST API: localhost:6333
* Web UI: localhost:6333/dashboard

## 2. Prepare Justicio

### Clone the code:

```
git clone git@github.com:bukosabino/justicio.git
```

### Install the requirements:

```
sudo apt install python3-virtualenv
virtualenv -p python3 venv3.10
source venv3.10/bin/activate
pip install -r requirements.txt
```

### Export environment variables:

Note: You need to get an API key for OpenAI and another for Sendgrid.

```
export APP_PATH="."
export SENDGRID_API_KEY=<your_sendgrid_api_key>
export OPENAI_API_KEY=<your_open_api_key>
export TOKENIZERS_PARALLELISM=false
export TAVILY_API_KEY=""
export QDRANT_API_KEY="823e071f67c198cc05c73f8bd4580865e6a8819a1f3fe57d2cd49b5c892a5233"
export QDRANT_API_URL="http://localhost:6333"
```

### Add some vector to the vector database

Load BOE documents into your vector database (depending on the selected data, may take a few minutes).

```
python -m src.etls.boe.load dates 2024/01/01 2024/01/07
```

## 3. Run Justicio in local

```
uvicorn src.service.main:APP --host=0.0.0.0 --port=5001 --workers=1 --timeout-keep-alive=125 --log-level=info
```

In the browser

```
http://<your.ip>:5001/docs
```
