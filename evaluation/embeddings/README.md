We want to evaluate some parameters for the system:

* chunk_size (600, 1200, 1800)
* chunk_overlap (50, 100)
* k number of chunks as context (4, 6, 8)
* Search params
  * https://qdrant.tech/documentation/concepts/search/
  * https://qdrant.tech/documentation/tutorials/optimize/


More info: https://www.anyscale.com/blog/a-comprehensive-guide-for-building-rag-based-llm-applications-part-1

*********************************************

We load a subset (`defs.py`) of BOE documents into different Qdrant databases (tier-free) and run `eval.py` against them.

