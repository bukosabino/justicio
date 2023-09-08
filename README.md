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
2. The backend service processes the input request (user question), transforms the question into an embedding, and sends the generated embedding as a query to the embedding database.
3. The embedding database returns documents that most closely match the query.
4. The most similar documents returned by the embedding database are added as context to the input request. Then it sends a request with all the information to the LLM API model.
5. The LLM API model returns a natural language answer to the user's question. 
6. The user receives an AI-generated response output.

## Components

### Backend service

It is the web service, and it is a central component for the whole system, doing most of the tasks:

* Process the input requests from the user.
* Transform the input text into embeddings.
* Send requests to the embeddings database to get the most similar embeddings.
* Send requests to the LLM API model to generate the response.
* Save the traces.
* Handle input/output exceptions.

### Embedding/Vector database

#### Loading data

We download the BOE documents and break them into small chunks of text (e.g. 2000 characters). Each text chunk is transformed into an embedding (e.g. a numerically dense vector of 768 sizes). Some additional metadata is also stored with the vectors so that we can pre- or post-filter the search results. [Check the code](https://github.com/bukosabino/ia-boe/blob/main/src/etls/etl_initial.py)

The BOE is updated every day, so we need to run an ETL job every day to retrieve the new documents, transform them into embeddings, link the metadata, and store them in the embedding database. [Check the code](https://github.com/bukosabino/ia-boe/blob/main/src/etls/etl_daily.py)

#### Reading data

It implements APIs to transform the input question into a vector, and to perform ANN (Approximate Nearest Neighbour) against all the vectors in the database. [Check the code](https://github.com/bukosabino/ia-boe/blob/main/src/service/main.py)

There are different types of search (semantic search, keyword search, or hybrid search).

There are different types of ANNs (cosine similarity, Euclidean distance, or dot product).

#### Embedding Model

The text in BOE is written in Spanish, so we need a sentence transformer model that is fine-tuned using Spanish 
datasets. We are experimenting with [these models](https://github.com/bukosabino/sbert-spanish).

More info: https://www.newsletter.swirlai.com/p/sai-notes-07-what-is-a-vector-database

### LLM API Model

It is a Large Language Model (LLM) which generates answers for the user questions based on the context, which is
the most similar documents returned by the embedding database.

Options:
* OpenAI (Third party API)
* Falcon (Own API)
* Llama2 (Own API)

# Deploy your own service

Check `deployment_guide.md` file

# Future features

* Summarize ELI5
* From QA to chat conversation (using memory)
* Add other regional and/or provincial gazettes https://www.boe.es/legislacion/otros_diarios_oficiales.php
* Generate smart questions from an article
* Use OpenAI Moderation API to filter wrong behaviours from users: https://platform.openai.com/docs/guides/moderation
* Create an OpenAI plugin

# Want to help develop the project?

You are welcome! Please, contact us to see how you can help.

* @bukosabino
* @adantart
