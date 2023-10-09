from evaluation.embeddings.questions import QUERIES
from src.initialize import initialize_app


INIT_OBJECTS = initialize_app()


success = 0
for boe_id, question in QUERIES:
    docs = INIT_OBJECTS.vector_store.similarity_search_with_score(
        query=question, k=INIT_OBJECTS.config_loader["top_k_results"]
    )
    for doc in docs:

        if doc[0].metadata['identificador'] == boe_id:
            success += 1
            # break


print(f"Len queries: {len(QUERIES)}")
print(f"Success answers: {success}")
