# Justicio

Justicio is a Question/Answering Assistant that generates answers from user questions about the official state gazette of Spain: 
Boletín Oficial del Estado (BOE).

[Spanish link](https://www.boe.es)

[English link](https://www.boe.es/index.php?lang=en)

**TL;DR:** All BOE articles are embedded in vectors and stored in a vector database. When a question is asked, the question 
is embedded in the same latent space and the most relevant text is retrieved from the vector database by performing a 
query using the embedded question. The retrieved pieces of text are then sent to the LLM to construct an answer.

# Service

At this moment we are running a user-free service: [Justicio](https://justicio.es/)

You can test it without charge! Please, give us your feedback if you have!

# How it works under the hood

![image (4)](https://github.com/bukosabino/ia-boe/assets/4375209/bb2ad4ce-f90a-40bf-a77f-bc1443b9896e)

## Flow

0. All BOE articles are embedded as embeddings and stored in an embedding database. This process is run at startup and every day.
1. The user writes (using natural language) any question related to the BOE as input to the system.
2. The backend service processes the input request (user question), transforms the question into an embedding, and sends the generated embedding as a query to the embedding database.
3. The embedding database returns documents that most closely match the query.
4. The most similar documents returned by the embedding database are added to the input query as context. Then a request with all the information is sent to the LLM API model.
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

We download the BOE documents and break them into small chunks of text (e.g. 1200 characters). Each text chunk is transformed into an embedding (e.g. a numerically dense vector of 768 sizes). Some additional metadata is also stored with the vectors so that we can pre- or post-filter the search results. [Check the code](https://github.com/bukosabino/ia-boe/blob/main/src/etls/boe/load.py)

The BOE is updated every day, so we need to run an ETL job every day to retrieve the new documents, transform them into embeddings, link the metadata, and store them in the embedding database. [Check the code](https://github.com/bukosabino/ia-boe/blob/main/src/etls/boe/load.py)

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

## Tools

- Langchain
- FastAPI
- Qdrant
- [Fine tuned Spanish SBert model](https://github.com/bukosabino/sbert-spanish)
- BeautifulSoup

# Deploy your own service

Check [doc/deployment_guide.md](https://github.com/bukosabino/justicio/blob/main/doc/deployment_guide.md) file

# Want to help develop the project?

You are welcome! Please, contact us to see how you can help.

* [Darío López](https://www.linkedin.com/in/dar%C3%ADo-l%C3%B3pez-padial-45269150/) 
* [Alex Dantart](https://www.linkedin.com/in/dantart/)
* [Jorge Iliarte](https://www.linkedin.com/in/jorge-iliarte-llop/)
* [Jorge Barrachina](https://www.linkedin.com/in/jorgebarrachina/)
