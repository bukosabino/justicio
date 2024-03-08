import typing as tp
from requests.exceptions import Timeout
import random
import requests
from bs4 import BeautifulSoup

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


class TextLoader(BaseLoader):
    """Load text files."""

    def __init__(
        self,
        file_path: str,
        encoding: tp.Optional[str] = None,
        metadata: tp.Optional[dict] = None,
    ):
        """Initialize with file path."""
        self.file_path = file_path
        self.encoding = encoding
        self.metadata = metadata

    def load(self) -> tp.List[Document]:
        """Load from file path."""
        with open(self.file_path, encoding=self.encoding) as f:
            text = f.read()
        return [Document(page_content=text, metadata=self.metadata)]


class ScrapperError(Exception):
    """
    Custom exception for scraping errors.
    """

    def __init__(self, message="Error durante el proceso de scraping", *args, **kwargs):
        """
        Initializes the exception with a custom error message.

        :param message: Error message describing the failure.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(message, *args, **kwargs)
        self.message = message

    def __str__(self):
        """
        Returns a string representation of the exception, including the error message.
        """
        return f"ScrapperError: {self.message}"


class HTTPRequestException(Exception):
    """
    Exception for errors occurring during HTTP requests made by HTTPRequester.
    """
    def __init__(self, message="HTTP request error", *args):
        super().__init__(message, *args)


class HTTPRequester:
    user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
        ]

    default_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    @classmethod
    def get_random_user_agent(cls):
        """
        Selects and returns a random User-Agent from the list of user_agents.
        """
        return random.choice(cls.user_agents)

    @classmethod
    def get_headers(cls):
        """
        Generates and returns headers including a random User-Agent.
        """
        headers = cls.default_headers.copy()
        headers["User-Agent"] = cls.get_random_user_agent()
        return headers

    @staticmethod
    def get_soup(url, timeout=30, markup='html.parser'):
        """
        Performs an HTTP GET request to the provided URL, using random headers, and returns a BeautifulSoup
        object if the response is successful. If there is an error or timeout, it throws HTTPRequestException.
        """
        headers = HTTPRequester.get_headers()
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, markup)
        except Timeout as e:
            raise HTTPRequestException(f"HTTP request timed out: {e}")
        except requests.RequestException as e:
            raise HTTPRequestException(f"HTTP request failed: {e}")
