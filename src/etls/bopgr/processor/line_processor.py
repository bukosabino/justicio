from re import Pattern
from abc import ABC, abstractmethod


class LineProcessor(ABC):
    """
    Abstract base class for line processors.

    :param ABC: Abstract base class.
    """

    @abstractmethod
    def test(self, line: str) -> bool:
        """
        Test if a line should be processed.

        :param str line: The line to test.

        :return: True if the line should be processed, False otherwise.
        :rtype: bool
        """
        pass


class MetadataProcessor(LineProcessor):
    """
    Abstract base class for metadata processors.

    :param LineProcessor: Inherits from LineProcessor abstract base class.
    """

    def include_line(self) -> bool:
        """
        Indicate whether to include the line.

        :return: True if the line should be included, False otherwise.
        :rtype: bool
        """
        return False

    @abstractmethod
    def get_metadata(self, line: str) -> dict:
        """
        Extract metadata from a line.

        :param str line: The line to extract metadata from.

        :return: A dictionary containing extracted metadata.
        :rtype: dict
        """
        pass


class CleanUpProcessor(LineProcessor):
    """
    Abstract base class for cleanup processors.

    :param LineProcessor: Inherits from LineProcessor abstract base class.
    """
    @abstractmethod
    def clean(self, line: str) -> str:
        """
        Clean a line.

        :param str line: The line to clean.

        :return: The cleaned line.
        :rtype: str
        """
        pass

class RegexLineProcessor(LineProcessor):
    """
    Line processor to handle regular expressions.

    :param LineProcessor: Inherits from LineProcessor abstract base class.

    :param pattern: The regular expression pattern to be used for testing lines.
    :type pattern: re.Pattern
    """
    pattern: Pattern

    def __init__(self, pattern: Pattern):
        """
        Constructor for RegexLineProcessor.

        :param re.Pattern pattern: The regular expression pattern to be used for testing lines.
        """
        self.pattern = pattern

    def test(self, line: str) -> bool:
        """
        Test if a line matches the regex.

        :param str line: The line to test.

        :return: True if the line should be processed, False otherwise.
        :rtype: bool
        """
        return bool(self.pattern.search(line))