"""NER integration interfaces."""

from .base import BaseNERDetector
from .mock_ner import MockNERDetector

__all__ = ["BaseNERDetector", "MockNERDetector"]
