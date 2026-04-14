import sys
<<<<<<< HEAD
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)
import pytest

class MockLLMResponse:
    def __init__(self, content):
        self.content = content


class MockLLM:
    def invoke(self, messages):
        return MockLLMResponse(
            """1) Core idea
2) How it works step-by-step
3) Why it matters
4) Example
5) Mistakes
6) Recap"""
        )


@pytest.fixture
def mock_llm():
    return MockLLM()
=======
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
>>>>>>> 084cfb82067091d99e9e13525bb96ab25cc5113b
