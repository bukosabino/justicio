from mteb import MTEB
from sentence_transformers import SentenceTransformer


# https://github.com/embeddings-benchmark/mteb


# TODO: write results on model cards huggingface
# Define the sentence-transformers model name
# model_name = "dariolopez/roberta-base-bne-finetuned-msmarco-qa-es-mnrl-mn"
# model_name = "dariolopez/roberta-base-bne-finetuned-msmarco-qa-es"
# model_name = "PlanTL-GOB-ES/roberta-base-bne"

# model_name = "hiiamsid/sentence_similarity_spanish_es"
model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
# model_name = "intfloat/multilingual-e5-large"


model = SentenceTransformer(model_name)
evaluation = MTEB(task_langs=["es"])
results = evaluation.run(model, output_folder=f"results/{model_name}")
