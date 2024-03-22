# https://llamahub.ai/l/readers/llama-index-readers-file?from=
# pip install llama index
# pip install llama-index-llms-ollama
# pip install llama-index-readers-file
# pip install ragas
# pip install spacy

import os
import openai

import logging
import sys
import pandas as pd

# TODO Adaptar el logging a init values
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# Llama Index imports for document handling
from llama_index.readers.file import XMLReader
from llama_index.core import SimpleDirectoryReader

# Llama Index imports for testset generation
from llama_index.core.llama_dataset.generator import RagDatasetGenerator
from llama_index.core.prompts.base import PromptTemplate
from llama_index.core.evaluation import DatasetGenerator, RelevancyEvaluator
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Response

# from llama_index.llms.openai import OpenAI

# Ollama Setup
from llama_index.llms.ollama import Ollama

# Setup variables
test_dir = os.path.join("src", "etls", "boe", "loading", "test")
llm = Ollama(
    model="solar:10.7b-instruct-v1-q5_K_M",
    request_timeout=60.0,
    base_url="http://192.168.1.220:11434",
)

# Llama Index default reader

file_extractor = {".xml": XMLReader()}
reader = SimpleDirectoryReader(test_dir, file_extractor=file_extractor)
documents = reader.load_data()

print(f"loaded {len(documents)} documents")


# Let's redefine the template to QA generation based on the original one, but for Spanish contents

spanish_text_question_generation_template = PromptTemplate(
"""    
La información de contexto está a continuación.
---------------------
{context_str}
---------------------
Dada la información de contexto y sin conocimientos previos, 
genere solo preguntas en español basadas en la siguiente consulta.
{query_str}
"""
)

spanish_text_qa_template = PromptTemplate(
"""
La información de contexto está a continuación.
---------------------
{context_str}
---------------------
Dada la información de contexto y sin conocimientos previos, 
responda en español a la siguiente consulta.
{query_str}
"""
)

spanish_question_gen_query = """
Usted es un profesor/docente hispanohablante.
Su tarea consiste en crear {num_questions_per_chunk} preguntas para un cuestionario/examen cercano.
Las preguntas deben ser de naturaleza diversa en todo el documento.
Limite las preguntas a la información contextual proporcionada.
"""

dataset_generator = RagDatasetGenerator.from_documents(
    documents,
    llm=llm,
    text_question_template=spanish_text_question_generation_template,
    text_qa_template=spanish_text_qa_template,
    question_gen_query=spanish_question_gen_query,
    num_questions_per_chunk=2,  # set the number of questions per nodes
    show_progress=True,
)


rag_dataset = dataset_generator.generate_dataset_from_nodes()

# Save it to a JSON file
rag_dataset.save_json(os.path.join(test_dir,"rag_test_justicio_dataset.json"))

# And a CSV via pandas
rag_dataset_df = rag_dataset.to_pandas()
rag_dataset_df.to_csv(os.path.join(test_dir, "rag_test_justicio_dataset.csv"), index=False)

# To reload it using rag_dataset = LabelledRagDataset.from_json("rag_dataset.json")