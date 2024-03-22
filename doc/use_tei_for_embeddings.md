# Use Text Embeddings Inference (TEI) support

TEI is an optimized tooklit for deploying and serving text embeddings and sequence classification models.

See more information in the [TEI documentation](https://huggingface.co/docs/text-embeddings-inference/index)

**Current limitation:** The `chunk_size` option must be 510 or lower to work. I was not able to configure a higher size.

## How to use

It is simple, just run a docker image suitable to your [compatible hardware](https://huggingface.co/docs/text-embeddings-inference/supported_models) like the following:

```shell
docker run --gpus all -e HUGGING_FACE_HUB_TOKEN=<your-hf-token> -p 8080:80 -v <your-tei-local-data>:/data ghcr.io/huggingface/text-embeddings-inference:turing-1.1 --model-id dariolopez/roberta-base-bne-finetuned-msmarco-qa-es-mnrl-mn --max-client-batch-size 64
```

The previous command will start a new service with the model `dariolopez/roberta-base-bne-finetuned-msmarco-qa-es-mnrl-mn` ready to generate embeddings.

In justicio's configuration, limit `chunk_size` to 510 and change the `embeddings_model_name` to the URL where TEI service is running and listening, like *http://localhost:8080*.

You will need to have an environment variable where justicio is running to provide the HF token.

```shell
HUGGINGFACEHUB_API_TOKEN=<your-hf-token> python -m src.etls.boja.load dates 2024/01/01 2024/01/31
```

Embeddings will be generated using TEI and embedded into the configured vector database (only tested with Qdrant). 