# Fine-tuning bge-m3-es-legal

### Introduction

Customize the embedding model (BAAI/bge-m3) for a specific domain (Legal) and language (Spanish).

### Steps

1. Create a dataset to fine-tuning
2. Fine-tuning the model using `BAAI/bge-m3` as baseline.

### Notes

Run in Runpod with 1 x RTX A6000. About 90 seconds per epoch. So, about 6 epochs -> 10 minutes.

### Based on:

- https://www.philschmid.de/sagemaker-train-deploy-embedding-models
- https://github.com/virattt/financial-datasets/
- https://github.com/virattt/financial-datasets/blob/main/financial_datasets/prompts.py

### Results

- Dataset: https://huggingface.co/datasets/dariolopez/justicio-rag-embedding-qa
- Model: https://huggingface.co/datasets/dariolopez/bge-m3-es-legal
