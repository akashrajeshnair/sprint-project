import sys
import types

from langchain_core.documents import Document


class FakeBase:
    pass


mock_db = types.ModuleType("database")
mock_db.SessionLocal = None
mock_db.Base = FakeBase
sys.modules["database"] = mock_db


from backend.services.rag import CONTENT_RETRIEVAL_TOOL, RagService, WEB_SEARCH_TOOL
from backend.services.rag import EXPLANATION_TOOL, USER_SCORE_TOOL


def _make_service(monkeypatch):
    monkeypatch.setattr(RagService, "_create_embeddings", lambda self: None)
    service = RagService()
    monkeypatch.setattr(service, "prepare", lambda: None)
    return service


def test_rag_tool_returns_retrieval_answer(monkeypatch):
    service = _make_service(monkeypatch)

    retrieved_docs = [
        Document(
            page_content="DBMS normalization removes redundancy and prevents update anomalies.",
            metadata={"source": "dbms_notes.pdf", "page": 2},
        )
    ]

    monkeypatch.setattr(RagService, "_run_tool", lambda self, **kwargs: retrieved_docs)
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: "Normalization keeps data consistent.")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="step-by-step",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
    )

    assert result["answer"] == "Normalization keeps data consistent."
    assert result["context_used"] is True
    assert result["tool_calls_used"][0]["name"] == CONTENT_RETRIEVAL_TOOL


def test_rag_tool_falls_back_to_general_answer(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(RagService, "_run_tool", lambda self, **kwargs: [])
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: "General DBMS answer.")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
    )

    assert result["context_used"] is False
    assert "couldn't find matching document context" in result["answer"].lower()
    assert "General DBMS answer." in result["answer"]
    assert result["tool_calls_used"][0]["name"] == CONTENT_RETRIEVAL_TOOL


def test_rag_tool_uses_web_search_when_retrieval_is_empty(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(RagService, "_run_tool", lambda self, **kwargs: [])
    monkeypatch.setattr(
        RagService,
        "_run_web_search",
        lambda self, **kwargs: [
            {"title": "DBMS normalization guide", "url": "https://example.com/dbms", "snippet": "Normalization reduces redundancy."}
        ],
    )
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: "General DBMS answer.")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="step-by-step",
        use_rag_context=True,
        use_web_search=True,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        max_steps=1,
    )

    assert "General DBMS answer." in result["answer"]
    assert result["context_used"] is True
    assert [call["name"] for call in result["tool_calls_used"]] == [CONTENT_RETRIEVAL_TOOL, WEB_SEARCH_TOOL]
    assert result["sources"][0]["source"] == "https://example.com/dbms"


def test_rag_tool_skips_retrieval_when_disabled(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(RagService, "_llm_direct_response", lambda self, **kwargs: "Direct answer without RAG.")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=False,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
    )

    assert result["answer"] == "Direct answer without RAG."
    assert result["context_used"] is False
    assert result["tool_calls_used"] == []


def test_explanation_tool_path(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(RagService, "_is_explanation_request", lambda self, prompt: True)
    monkeypatch.setattr(RagService, "_llm_explanation_response", lambda self, **kwargs: "Detailed explanation.")

    result = service.answer_with_agent_loop(
        question="Explain normalization in detail",
        role="student",
        learner_level="beginner",
        response_mode="step-by-step",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=True,
        user_id=1,
    )

    assert result["answer"] == "Detailed explanation."
    assert result["context_used"] is False
    assert result["tool_calls_used"][0]["name"] == EXPLANATION_TOOL


def test_explanation_tool_fallback_when_llm_returns_none(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(RagService, "_is_explanation_request", lambda self, prompt: True)
    monkeypatch.setattr(RagService, "_llm_explanation_response", lambda self, **kwargs: None)
    monkeypatch.setattr(RagService, "_build_explanation_fallback", lambda self, **kwargs: "Fallback explanation.")

    result = service.answer_with_agent_loop(
        question="Explain normalization",
        role="student",
        learner_level="beginner",
        response_mode="step-by-step",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=True,
        user_id=1,
    )

    assert result["answer"] == "Fallback explanation."
    assert result["tool_calls_used"][0]["name"] == EXPLANATION_TOOL


def test_score_tool_path_with_filters(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(RagService, "_is_score_request", lambda self, prompt: True)
    monkeypatch.setattr(RagService, "_extract_score_filters", lambda self, prompt: ("dbms", "normalization"))
    monkeypatch.setattr(
        RagService,
        "_get_user_score_summary",
        lambda self, **kwargs: {"topics_covered": 2, "subject": "dbms", "topic": "normalization"},
    )
    monkeypatch.setattr(RagService, "_format_score_summary", lambda self, **kwargs: "Score summary answer.")

    result = service.answer_with_agent_loop(
        question="What's my score in DBMS normalization?",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=True,
        use_explanation_tool=False,
        user_id=123,
    )

    assert result["answer"] == "Score summary answer."
    assert result["context_used"] is True
    assert result["tool_calls_used"][0]["name"] == USER_SCORE_TOOL
    assert result["tool_calls_used"][0]["arguments"]["user_id"] == 123
    assert result["tool_calls_used"][0]["arguments"]["subject"] == "dbms"
    assert result["tool_calls_used"][0]["arguments"]["topic"] == "normalization"


def test_rag_retries_and_refines_question(monkeypatch):
    service = _make_service(monkeypatch)

    calls: list[dict] = []
    retrieved_docs = [
        Document(
            page_content="Normalization reduces redundancy.",
            metadata={"source": "dbms_notes.pdf", "page": 1},
        )
    ]

    def _run_tool(self, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return []
        return retrieved_docs

    monkeypatch.setattr(RagService, "_run_tool", _run_tool)
    monkeypatch.setattr(RagService, "_refine_question_for_retry", lambda self, prompt, step: "refined question")
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: "Answer after retry.")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        max_steps=2,
    )

    assert result["answer"] == "Answer after retry."
    assert len(result["tool_calls_used"]) == 2
    assert result["tool_calls_used"][0]["step"] == 1
    assert result["tool_calls_used"][1]["step"] == 2
    assert calls[0]["question"] != calls[1]["question"]
    assert calls[1]["question"] == "refined question"


def test_question_bank_request_sets_selected_file(monkeypatch):
    service = _make_service(monkeypatch)

    retrieved_docs = [
        Document(
            page_content="Question bank chunk.",
            metadata={"source": "qb.pdf", "page": 1},
        )
    ]

    captured: dict = {}

    monkeypatch.setattr(RagService, "_is_question_request", lambda self, prompt: True)
    monkeypatch.setattr(RagService, "_question_bank_file_for_role", lambda self, role: "question_bank.pdf")

    def _run_tool(self, **kwargs):
        captured.update(kwargs)
        return retrieved_docs

    monkeypatch.setattr(RagService, "_run_tool", _run_tool)
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: "QB answer")

    result = service.answer_with_agent_loop(
        question="Give me a question",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
    )

    assert result["selected_file"] == "question_bank.pdf"
    assert captured["selected_file"] == "question_bank.pdf"
    assert "question bank questions" in captured["question"].lower()


def test_empty_question_returns_prompt(monkeypatch):
    service = _make_service(monkeypatch)

    result = service.answer_with_agent_loop(
        question="   ",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
    )

    assert result["answer"].lower().startswith("please ask")
    assert result["context_used"] is False
    assert result["tool_calls_used"] == []


def test_invalid_role_defaults_to_student(monkeypatch):
    service = _make_service(monkeypatch)

    captured: dict = {}

    def _run_tool(self, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(RagService, "_run_tool", _run_tool)
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: "General answer")

    service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="admin",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        max_steps=1,
    )

    assert captured["role"] == "student"


def test_rag_context_falls_back_to_context_text_when_llm_none(monkeypatch):
    service = _make_service(monkeypatch)

    long_text = "A" * 1300
    retrieved_docs = [
        Document(page_content=long_text, metadata={"source": "dbms_notes.pdf", "page": 1}),
    ]

    monkeypatch.setattr(RagService, "_run_tool", lambda self, **kwargs: retrieved_docs)
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: None)

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        max_steps=1,
    )

    assert result["context_used"] is True
    assert len(result["answer"]) == 1200
    assert set(result["answer"]) == {"A"}


def test_rag_deduplication_affects_tool_result_count(monkeypatch):
    service = _make_service(monkeypatch)

    docs = [
        Document(page_content="Same", metadata={"source": "x.pdf", "page": 1}),
        Document(page_content="Same", metadata={"source": "x.pdf", "page": 1}),
    ]

    monkeypatch.setattr(RagService, "_run_tool", lambda self, **kwargs: docs)
    monkeypatch.setattr(RagService, "_deduplicate_docs", lambda self, values: values[:1])
    monkeypatch.setattr(RagService, "_llm_general_response", lambda self, **kwargs: "Answer")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        max_steps=1,
    )

    assert result["tool_calls_used"][0]["name"] == CONTENT_RETRIEVAL_TOOL
    assert result["tool_calls_used"][0]["result_count"] == 1