import mteb
from sentence_transformers import SentenceTransformer


# https://github.com/embeddings-benchmark/mteb


# TODO: write results on model cards huggingface
# Define the sentence-transformers model name
# model_name = "dariolopez/roberta-base-bne-finetuned-msmarco-qa-es-mnrl-mn"
# model_name = "dariolopez/roberta-base-bne-finetuned-msmarco-qa-es"
# model_name = "PlanTL-GOB-ES/roberta-base-bne"
# model_name = "PlanTL-GOB-ES/RoBERTalex"

# model_name = "hiiamsid/sentence_similarity_spanish_es"
# model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
# model_name = "intfloat/multilingual-e5-small"
# model_name = "intfloat/multilingual-e5-base"
model_name = "intfloat/multilingual-e5-large"
# model_name = "intfloat/multilingual-e5-large-instruct"

try:
    model = SentenceTransformer(model_name, device='cuda')
    print("Loaded model embedding using GPU")
except:
    model = SentenceTransformer(model_name, device='cpu')
    print("Loaded model embedding using CPU")

tasks = mteb.get_tasks(languages=["spa"])  # Spanish
print(tasks)
evaluation = mteb.MTEB(tasks=tasks)
results = evaluation.run(model, output_folder=f"results/{model_name}")
