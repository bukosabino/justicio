# IA BOE

Question/Answering Assistant that generates answers from user questions about the Official State Gazette 
of Spain: Boletín Oficial del Estado (BOE).

[Spanish link](https://www.boe.es)
[English link](https://www.boe.es/index.php?lang=en)

# How it works under the hood

*image*

## Flow

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

### Embedding database

It has all documents on the BOE splited in small text chunks (1500 characters for example). 
Each text chunk is transformed on an embedding (a numerical dense vector of 768 sizes for 
example).

It implements endpoints to get semantic search or keyword search.

Options:
* Pinecone (memory)
* Supabase (hard disk)
* Pgvector (hard disk)

The BOE is updated every day, so, we need to run an ETL job daily, getting the new documents, transforming to embeddings and saving on the Embedding database.

### LLM API Model

In progress.

Options:
* OpenAI
* Falcon

# Structure of the repo

In progress.

# Future features

* Summarize ELI5
* From QA to chat conversation (using memory)
* Add other regional and/or provincial gazettes https://www.boe.es/legislacion/otros_diarios_oficiales.php
* Create a OpenAI plugin
* Generate smart questions from an article
* Use OpenAI Moderation API to filter wrong behaviours from users: https://platform.openai.com/docs/guides/moderation
