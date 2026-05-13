"""NER integration interfaces."""

from .base import BaseNERDetector
from .finetuned_wrapper import FinetunedNERDetector, NERDependencyError
from .mock_ner import MockNERDetector

__all__ = ["BaseNERDetector", "FinetunedNERDetector", "MockNERDetector", "NERDependencyError"]
