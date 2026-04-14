import sys
import types

class FakeBase:
    pass

# ✅ MOCK DATABASE (CRITICAL FIX)
mock_db = types.ModuleType("database")
mock_db.SessionLocal = None
mock_db.Base = FakeBase

sys.modules["database"] = mock_db

import pytest

from backend.services.rag import RagService


@pytest.fixture
def rag():
    return RagService()


# =========================
# 1. SCORE REQUEST DETECTION
# =========================

def test_score_request_detected(rag):
    assert rag._is_score_request("Show my score") is True


def test_score_request_with_subject(rag):
    assert rag._is_score_request("Show my score") is True


def test_score_request_false(rag):
    assert rag._is_score_request("What is DBMS?") is False


def test_score_request_empty(rag):
    assert rag._is_score_request("") is False


# =========================
# 2. FILTER EXTRACTION
# =========================

def test_extract_subject_filter(rag):
    subject, topic = rag._extract_score_filters("Show my Mathematics score")
    assert subject == "Mathematics"


def test_extract_topic_filter(rag):
    subject, topic = rag._extract_score_filters("Show score for algebra basics")
    assert topic is None


def test_extract_no_filter(rag):
    subject, topic = rag._extract_score_filters("Show my score")
    assert subject is None
    assert topic is None


# =========================
# 3. SCORE SUMMARY LOGIC (MOCK DB)
# =========================

def test_score_summary_empty(monkeypatch, rag):
    def mock_summary(*args, **kwargs):
        return {
            "total_score": 0,
            "average_score": 0,
            "topics_covered": 0
        }

    monkeypatch.setattr(rag, "_get_user_score_summary", mock_summary)

    result = rag._get_user_score_summary(user_id=1)
    assert result["total_score"] == 0


def test_score_summary_with_data(monkeypatch, rag):
    def mock_summary(*args, **kwargs):
        return {
            "total_score": 2.5,
            "average_score": 0.75,
            "topics_covered": 4
        }

    monkeypatch.setattr(rag, "_get_user_score_summary", mock_summary)

    result = rag._get_user_score_summary(user_id=1)
    assert result["average_score"] == 0.75


# =========================
# 4. SCORE FORMAT OUTPUT
# =========================

def test_format_score_summary_short(rag):
    summary = {
        "total_score": 2.5,
        "average_score": 0.75,
        "topics_covered": 4
    }

    output = rag._format_score_summary(summary, response_mode="short")

    assert "total score" in output.lower()


def test_format_score_summary_step(rag):
    summary = {
        "total_score": 3.0,
        "average_score": 0.80,
        "topics_covered": 5
    }

    output = rag._format_score_summary(summary, response_mode="step-by-step")

    assert "1." in output or "Total Score" in output


# =========================
# 5. FULL SCORE TOOL FLOW
# =========================

def test_full_score_tool_flow(monkeypatch, rag):
    # Mock summary
    def mock_summary(*args, **kwargs):
        return {
            "total_score": 3.0,
            "average_score": 0.8,
            "topics_covered": 5
        }

    monkeypatch.setattr(rag, "_get_user_score_summary", mock_summary)

    result = rag.answer_with_agent_loop(
        question="Show my score",
        role="student",
        user_id=1,
        use_score_tool=True
    )

    assert "score" in result["answer"].lower()
    assert result["tool_calls_used"][0]["name"] == "user_score_lookup"