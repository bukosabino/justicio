# IA BOE

Question/Answering Assistant that generates answers from user questions about the Official State Gazette of Spain: 
Boletín Oficial del Estado (BOE).

[Spanish link](https://www.boe.es)

[English link](https://www.boe.es/index.php?lang=en)

**TL;DR:** All BOE articles are embedded in vectors and stored in a vector database. When a question is asked, the question 
is embedded in the same latent space and the most relevant text is retrieved from the vector database by performing a 
query using the embedded question. The retrieved pieces of text are then sent to the LLM to construct an answer.

# How it works under the hood

<img width="1594" alt="Captura de pantalla 2023-06-19 a las 18 37 41" src="https://github.com/bukosabino/ia-boe/assets/4375209/7266699b-8ad6-4a1c-8b6c-fe05c837af3a">

## Flow

0. All BOE articles are embedded in vectors and stored in a vector database. This process is run at startup and every day.
1. The user writes (using natural language) any question related to the BOE as input to the system.
2. The backend service handles the input request (user question), transforms the question into an embedding, and sends the generated embedding as a query to the embedding database.
3. The embedding database returns documents most similar to the query.
4. The most similar documents returned by the embedding database are added as context to the input request. Then it sends a request to the LLM API model with all the information.
5. The LLM API model returns a natural language answer to the user's question. 
6. The user gets an AI generated response output.

## Components

### Backend service

It is the web service, and it is a central component for all the system doing most of the tasks:

* Handle the input requests from the user.
* Transform the input text to embeddings.
* Send requests to Embeddings database and LLM API Model.
* Save traces.
* Handle input/output exceptions.

### Embedding/Vector database

#### Loading data

It has all the documents on the BOE broken down into small chunks of text (for example, 2000 characters). Each text 
chunk is transformed into an embedding (a numerically dense vector of 768 sizes, for example). Also, some additional 
metadata is stored along with the vectors, so we can pre-filter or post-filter the search results.

The BOE is updated every day, so we need to run an ETL job every day to retrieve the new documents, transform them 
into embeddings, link the metadata, and store them in the embedding database.

#### Reading data

It implements APIs to transform the input question into a vector, and to perform ANN (Appproximate Nearest Neighbour) 
against all the vectors in the database.

There are different types of search (semantic search, keyword search, or hybrid search).

There are different types of ANNs (cosine similarity, Euclidean distance, or dot product).

#### Embedding Model

The text in BOE is written in Spanish, so we need a sentence transformer model that is fine-tuned using Spanish 
datasets. We are experimenting with this: https://github.com/bukosabino/sbert-spanish

More info: https://www.newsletter.swirlai.com/p/sai-notes-07-what-is-a-vector-database

### LLM API Model

It is a Large Language Model (LLM) which generates answers to questions 

Options:
* OpenAI
* Falcon

# How to work

```
export PINECONE_API_KEY=<your_pinecone_api_key>
export PINECONE_ENV=<your_pinecone_env>
export OPENAI_API_KEY=<your_open_api_key>
```

## Init ETL

```
python src/etls/etl_initial.py
```

## Daily ETL

```
python src/etls/etl_daily.py
```

## Run service

```
uvicorn src.service.app:APP --host=0.0.0.0 --port=5001 --workers=2 --timeout-keep-alive=125 --log-level=error
```

# Structure of the repo

In progress.

# Future features

* Summarize ELI5
* From QA to chat conversation (using memory)
* Add other regional and/or provincial gazettes https://www.boe.es/legislacion/otros_diarios_oficiales.php
* Generate smart questions from an article
* Use OpenAI Moderation API to filter wrong behaviours from users: https://platform.openai.com/docs/guides/moderation
* Create an OpenAI plugin
