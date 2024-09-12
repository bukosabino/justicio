from llama_index.core.llama_dataset.generator import RagDatasetGenerator
from llama_index.core.llama_dataset import LabelledRagDataset

import os
import pandas as pd

test_dir = os.path.join("src", "etls", "boe", "loading", "test")

rag_dataset = LabelledRagDataset.from_json(os.path.join(test_dir,"rag_test_justicio_dataset.json"))

rag_dataset_df = rag_dataset.to_pandas()
rag_dataset_df.to_csv(os.path.join(test_dir, "rag_test_justicio_dataset.csv"), index=False)

