# https://llamahub.ai/l/readers/llama-index-readers-file?from=
# pip install llama index
# pip install llama-index-readers-file
# pip install ragas

import os
import openai

# Llama Index imports
from llama_index.readers.file import XMLReader
from llama_index.core import SimpleDirectoryReader

# Ragas imports
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

# Setup variables
test_dir = os.path.join("src", "etls", "boe", "loading", "test")
openai.api_key = os.environ["OPENAI_API_KEY"]

# Llama Index default reader
reader = SimpleDirectoryReader(test_dir)

documents = reader.load_data()
print(f"loaded {len(documents)} documents")

generator = TestsetGenerator.with_openai()

# Change resulting question type distribution
distributions = {simple: 0.5, multi_context: 0.4, reasoning: 0.1}

# use generator.generate_with_llamaindex_docs if you use llama-index as document loader
testset = generator.generate_with_llamaindex_docs(documents, 10, distributions)
testset_df = testset.to_pandas()
testset_df.head()
testset_df.to_csv("testset.csv", index=False)
