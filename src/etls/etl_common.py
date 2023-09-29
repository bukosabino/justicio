import logging as lg
import os
import typing as tp

import pinecone
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from retry import retry

from src.etls.utils import BOEMetadataDocument, BOETextLoader
from src.initialize import initialize_logging

initialize_logging()


class ETL:
    def __init__(self, config_loader, vector_store):
        self._config_loader = config_loader
        self._vector_store = vector_store

    def run(self, docs: tp.List[BOEMetadataDocument]):
        chunks = self._split_documents(docs)
        self._load_database(chunks)
        # self._log_database_stats()

    def _split_documents(self, docs: tp.List[BOEMetadataDocument]) -> tp.List[Document]:
        """Split documents by chunks

        :param docs:
        :return:
        """
        logger = lg.getLogger(self._split_documents.__name__)
        logger.info("Splitting in chunks %s documents", len(docs))
        docs_chunks = []
        for doc in docs:
            loader = BOETextLoader(file_path=doc.filepath, metadata=doc.dict())
            documents = loader.load()
            text_splitter = CharacterTextSplitter(
                separator=self._config_loader["separator"],
                chunk_size=self._config_loader["chunk_size"],
                chunk_overlap=self._config_loader["chunk_overlap"],
            )
            docs_chunks += text_splitter.split_documents(documents)
        if doc:
            logger.info("Removing file %s", doc.filepath)
            os.remove(doc.filepath)
        logger.info("Splitted %s documents in %s chunks", len(docs), len(docs_chunks))
        return docs_chunks

    @retry(tries=3, delay=2)
    def _load_database(self, docs_chunks: tp.List[Document]) -> None:
        logger = lg.getLogger(self._load_database.__name__)
        logger.info("Loading %s embeddings to database", len(docs_chunks))
        self._vector_store.add_documents(docs_chunks)
        logger.info("Loaded %s embeddings to database", len(docs_chunks))

    def _log_database_stats(self) -> None:
        logger = lg.getLogger(self._log_database_stats.__name__)
        index_name = self._config_loader["vector_store_index_name"]
        logger.info(pinecone.describe_index(index_name))
        index = pinecone.Index(index_name)
        logger.info(index.describe_index_stats())
