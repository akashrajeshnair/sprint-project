import sys
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