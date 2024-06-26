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
# model_name = "intfloat/multilingual-e5-large"
# model_name = "intfloat/multilingual-e5-large-instruct"
model_name = "BAAI/bge-m3"

try:
    model = SentenceTransformer(model_name, device='cuda')
    print("Loaded model embedding using GPU")
except:
    model = SentenceTransformer(model_name, device='cpu')
    print("Loaded model embedding using CPU")


TASK_LIST_BITEXT_MINING = [
    "BibleNLPBitextMining",
    # "FloresBitextMining", s2s, crosslingual 406 / 41412 pairs
    # "NTREXBitextMining", s2s, crosslingual 62 / 1916 pairs
    "Tatoeba",
]

TASK_LIST_PAIR_CLASSIFICATION = [
    "PawsX",
    "XNLI"
]

TASK_LIST_MULTI_LABEL_CLASSIFICATION = [
    ## "MultiEURLEXMultilabelClassification"
]

TASK_LIST_RETRIEVAL = [
    # "BelebeleRetrieval",
    "MintakaRetrieval",
    ## "MIRACLRetrieval",
    # "MLQARetrieval",
    # "MultiLongDocRetrieval",
    "PublicHealthQA",
    # "XMarket",
    "XPQARetrieval",
    "XQuADRetrieval",
    ## "SpanishPassageRetrievalS2P",
    "SpanishPassageRetrievalS2S"
]

TASK_LIST_CLASSIFICATION = [
    "AmazonReviewsClassification",
    "CataloniaTweetClassification",
    # "LanguageClassification",
    "MassiveIntentClassification",
    "MassiveScenarioClassification",
    "MTOPDomainClassification",
    "MTOPIntentClassification",
    "MultiHateClassification",
    # "MultilingualSentimentClassification",
    "SIB200Classification",
    "TweetSentimentClassification",
    ## "SpanishNewsClassification",
    "SpanishSentimentClassification"
]

TASK_LIST_CLUSTERING = [
    # "MLSUMClusteringP2P.v2",
    ## "SpanishNewsClusteringP2P",
    ## "MLSUMClusteringS2S.v2",
    "SIB200ClusteringS2S"
]

TASK_LIST_RERANKING = [
    # "MIRACLReranking"
]

TASK_LIST_STS = [
    "STS17",
    ## "STS22",
    "STSBenchmarkMultilingualSTS",
    "STSES"
]

TASK_LIST = (
    TASK_LIST_BITEXT_MINING
    + TASK_LIST_PAIR_CLASSIFICATION
    + TASK_LIST_MULTI_LABEL_CLASSIFICATION
    + TASK_LIST_RETRIEVAL
    + TASK_LIST_CLASSIFICATION
    + TASK_LIST_CLUSTERING
    + TASK_LIST_RERANKING
    + TASK_LIST_STS
)


tasks = mteb.get_tasks(languages=["spa"])  # Spanish
print(tasks)
print(TASK_LIST)
tasks = mteb.get_tasks(tasks=TASK_LIST, languages=["spa"])  # Spanish filtered
evaluation = mteb.MTEB(tasks=tasks)
# evaluation = mteb.MTEB(tasks=tasks, task_langs=["es"])
results = evaluation.run(model, output_folder=f"results/{model_name}")
