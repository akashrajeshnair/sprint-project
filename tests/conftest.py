import sys
from pathlib import Path

# ✅ Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest


# =========================
# MOCK LLM FOR TESTING
# =========================

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


# =========================
# FIXTURE
# =========================

@pytest.fixture
def mock_llm():
    return MockLLM()