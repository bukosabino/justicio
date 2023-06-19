from datetime import datetime, date
import logging

from utils import BOEMetadataDocument, BOETextLoader
from langchain.text_splitter import CharacterTextSplitter
import pinecone

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger('boelogger')


class ETL:
    def __init__(self, config_loader, vector_store):
        self._config_loader = config_loader
        self._vector_store = vector_store

        self.start_date = datetime.strptime(self._config_loader['start_date'], '%Y/%m/%d')
        self.end_date = date.today()

    # @timeit
    def run(self, docs):
        chunks = self._split_documents(docs)
        self._load_database(chunks)
        self._log_database_stats()

    def _split_documents(self, docs):
        """Split documents by chunks

        :param docs:
        :return:
        """
        logger.info("Splitting in chunks %s documents", len(docs))
        docs_chunks = []
        for doc in docs:
            loader = BOETextLoader(file_path=doc.filepath, metadata=doc.load_metadata())
            documents = loader.load()
            text_splitter = CharacterTextSplitter(
                separator=self._config_loader['separator'],
                chunk_size=self._config_loader['chunk_size'],
                chunk_overlap=self._config_loader['chunk_overlap']
            )
            docs_chunks += text_splitter.split_documents(documents)
        logger.info("Splitted %s documents in %s chunks", len(docs), len(docs_chunks))
        return docs_chunks

    def _load_database(self, docs_chunks):
        logger.info("Loading %s embeddings to database", len(docs_chunks))
        self._vector_store.add_documents(docs_chunks)
        logger.info("Loaded %s embeddings to database", len(docs_chunks))

    def _log_database_stats(self):
        index_name = self._config_loader['vector_store_index_name']
        index = pinecone.Index(index_name)
        logger.info(pinecone.describe_index(index_name))
        logger.info(index.describe_index_stats())
