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
from backend.services.rag import detailed_explanation, service


# ✅ 1. Basic explanation test
def test_basic_explanation(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "Explain DBMS",
        "role": "student",
        "learner_level": "beginner"
    })

    assert "Core idea" in result
    assert "How it works" in result


# ✅ 2. Explanation fallback when LLM fails
def test_explanation_fallback(monkeypatch):
    service._general_llm = None  # simulate failure
    monkeypatch.setattr(service, "_get_general_llm", lambda: None)

    result = detailed_explanation.invoke({
        "question": "Explain AI",
        "role": "student",
        "learner_level": "beginner"
    })

    assert "Detailed explanation" in result
    assert "1. Core idea" in result


# ✅ 3. Advanced level explanation
def test_advanced_level_explanation(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "Explain distributed systems",
        "role": "student",
        "learner_level": "advanced"
    })

    assert isinstance(result, str)
    assert len(result) > 20


# ✅ 4. Teacher role explanation
def test_teacher_role_explanation(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "Explain OS",
        "role": "teacher",
        "learner_level": "advanced"
    })

    assert "Core idea" in result


# ✅ 5. Empty question edge case
def test_empty_question():
    with pytest.raises(Exception):
        detailed_explanation.invoke({
            "question": "",
            "role": "student",
            "learner_level": "beginner"
        })


# ✅ 6. Long question handling
def test_long_question(mock_llm):
    service._general_llm = mock_llm

    long_q = "Explain " + "machine learning " * 50

    result = detailed_explanation.invoke({
        "question": long_q,
        "role": "student",
        "learner_level": "beginner"
    })

    assert len(result) > 50


# ================= ADDITIONAL TEST CASES (7–18) =================

# ✅ 7. Intermediate level explanation
def test_intermediate_level_explanation(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "Explain normalization",
        "role": "student",
        "learner_level": "intermediate"
    })

    assert isinstance(result, str)
    assert "Core idea" in result


# ✅ 8. Invalid learner level (should not crash)
def test_invalid_learner_level(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "Explain DBMS",
        "role": "student",
        "learner_level": "expert"   # invalid
    })

    assert isinstance(result, str)
    assert len(result) > 0

# ✅ 9. Special characters in question
def test_special_characters_question(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "Explain DBMS!!! @@##$$",
        "role": "student",
        "learner_level": "beginner"
    })

    assert "Core idea" in result


# ✅ 10. Numeric question input
def test_numeric_question(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "12345",
        "role": "student",
        "learner_level": "beginner"
    })

    assert isinstance(result, str)


# ✅ 11. Very short question
def test_short_question(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "DBMS?",
        "role": "student",
        "learner_level": "beginner"
    })

    assert isinstance(result, str)


# ✅ 12. LLM returns empty response → fallback
class EmptyLLM:
    def invoke(self, messages):
        class R:
            content = ""
        return R()

def test_llm_empty_response_fallback():
    service._general_llm = EmptyLLM()

    result = detailed_explanation.invoke({
        "question": "Explain AI",
        "role": "student",
        "learner_level": "beginner"
    })

    assert "Detailed explanation" in result


# ✅ 13. LLM returns list instead of string
class ListLLM:
    def invoke(self, messages):
        class R:
            content = ["Core idea", "How it works"]
        return R()

def test_llm_list_response():
    service._general_llm = ListLLM()

    result = detailed_explanation.invoke({
        "question": "Explain ML",
        "role": "student",
        "learner_level": "beginner"
    })

    assert isinstance(result, str)


# ✅ 14. Ensure structured format always exists
def test_output_structure(mock_llm):
    service._general_llm = mock_llm

    result = detailed_explanation.invoke({
        "question": "Explain OS",
        "role": "student",
        "learner_level": "beginner"
    })

    expected_sections = [
        "Core idea",
        "How it works",
        "Why it matters",
        "example",
        "mistakes",
        "recap"
    ]

    for section in expected_sections:
        assert section.lower() in result.lower()


# ✅ 15. Stress test (multiple calls)
def test_multiple_calls(mock_llm):
    service._general_llm = mock_llm

    for _ in range(5):
        result = detailed_explanation.invoke({
            "question": "Explain DBMS",
            "role": "student",
            "learner_level": "beginner"
        })
        assert "Core idea" in result



