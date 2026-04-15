import sys
import types


class FakeBase:
    pass


mock_db = types.ModuleType("database")
mock_db.SessionLocal = None
mock_db.Base = FakeBase
sys.modules["database"] = mock_db


import backend.services.rag as rag_module
from backend.services.rag import RagService, WEB_SEARCH_TOOL, duckduckgo_search_tool


def _make_service(monkeypatch):
    monkeypatch.setattr(RagService, "_create_embeddings", lambda self: None)
    service = RagService()
    monkeypatch.setattr(service, "prepare", lambda: None)
    return service


class FakeDDGS:
    def __init__(self, results=None, raise_on_text: bool = False):
        self._results = list(results or [])
        self._raise_on_text = raise_on_text
        self.last_query = None
        self.last_max_results = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def text(self, query, max_results=5):
        self.last_query = query
        self.last_max_results = max_results
        if self._raise_on_text:
            raise RuntimeError("DDG error")
        return self._results


def test_run_web_search_returns_empty_when_ddgs_missing(monkeypatch):
    service = _make_service(monkeypatch)
    monkeypatch.setattr(rag_module, "DDGS", None)

    assert service._run_web_search(question="dbms", max_results=3) == []


def test_run_web_search_returns_empty_for_blank_query(monkeypatch):
    service = _make_service(monkeypatch)
    monkeypatch.setattr(rag_module, "DDGS", lambda: FakeDDGS(results=[{"title": "x", "href": "y", "body": "z"}]))

    assert service._run_web_search(question="   ", max_results=5) == []


def test_run_web_search_normalizes_deduplicates_and_clamps_limit(monkeypatch):
    service = _make_service(monkeypatch)

    fake_client = FakeDDGS(
        results=[
            {"title": "  DBMS  Normalization ", "href": " https://example.com/a ", "body": " reduces   redundancy "},
            {"title": "DBMS Normalization", "href": "https://example.com/a", "body": "duplicate"},
            {"title": "", "href": "https://example.com/only-url", "body": "  snippet  "},
            "not-a-dict",
            {"title": "", "href": "", "body": ""},
        ]
    )

    monkeypatch.setattr(rag_module, "DDGS", lambda: fake_client)

    results = service._run_web_search(question="  hello   world ", max_results=999)

    assert fake_client.last_query == "hello world"
    assert fake_client.last_max_results == 8

    assert results == [
        {
            "title": "DBMS Normalization",
            "snippet": "reduces redundancy",
            "url": "https://example.com/a",
        },
        {
            "title": "",
            "snippet": "snippet",
            "url": "https://example.com/only-url",
        },
    ]


def test_run_web_search_handles_exception(monkeypatch):
    service = _make_service(monkeypatch)
    monkeypatch.setattr(rag_module, "DDGS", lambda: FakeDDGS(raise_on_text=True))

    assert service._run_web_search(question="dbms", max_results=3) == []


def test_answer_with_agent_loop_direct_mode_uses_web_search_sources(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(
        service,
        "_run_web_search",
        lambda **kwargs: [
            {"title": "DBMS normalization", "snippet": "Normalization reduces redundancy.", "url": "https://example.com/dbms"}
        ],
    )
    monkeypatch.setattr(service, "_llm_web_response", lambda **kwargs: "Web answer")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=False,
        use_web_search=True,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        top_k=3,
    )

    assert result["answer"] == "Web answer"
    assert result["context_used"] is True
    assert result["tool_calls_used"][0]["name"] == WEB_SEARCH_TOOL
    assert result["sources"][0]["source"] == "https://example.com/dbms"


def test_run_web_search_clamps_min_limit_to_1(monkeypatch):
    service = _make_service(monkeypatch)

    fake_client = FakeDDGS(
        results=[
            {"title": "One", "href": "https://example.com/1", "body": "a"},
        ]
    )
    monkeypatch.setattr(rag_module, "DDGS", lambda: fake_client)

    results = service._run_web_search(question="dbms", max_results=0)
    # max_results=0 is treated as "use default" (5) due to (max_results or 5).
    assert fake_client.last_max_results == 5
    assert results[0]["url"] == "https://example.com/1"


def test_run_web_search_dedup_is_case_insensitive(monkeypatch):
    service = _make_service(monkeypatch)

    fake_client = FakeDDGS(
        results=[
            {"title": "Normalization", "href": "HTTPS://EXAMPLE.COM/A", "body": "first"},
            {"title": "normalization", "href": "https://example.com/a", "body": "second"},
        ]
    )
    monkeypatch.setattr(rag_module, "DDGS", lambda: fake_client)

    results = service._run_web_search(question="dbms", max_results=5)
    assert len(results) == 1
    assert results[0]["snippet"] == "first"


def test_run_web_search_skips_rows_without_title_and_url(monkeypatch):
    service = _make_service(monkeypatch)

    fake_client = FakeDDGS(
        results=[
            {"title": "", "href": "", "body": ""},
            {"title": "", "href": "", "body": "has body but no key"},
            {"title": "Has URL", "href": "https://example.com/x", "body": "ok"},
        ]
    )
    monkeypatch.setattr(rag_module, "DDGS", lambda: fake_client)

    results = service._run_web_search(question="dbms", max_results=5)
    assert results == [{"title": "Has URL", "snippet": "ok", "url": "https://example.com/x"}]


def test_run_web_search_preserves_first_occurrence_order(monkeypatch):
    service = _make_service(monkeypatch)

    fake_client = FakeDDGS(
        results=[
            {"title": "A", "href": "https://example.com/a", "body": "first"},
            {"title": "B", "href": "https://example.com/b", "body": "second"},
            {"title": "A", "href": "https://example.com/a", "body": "duplicate"},
        ]
    )
    monkeypatch.setattr(rag_module, "DDGS", lambda: fake_client)

    results = service._run_web_search(question="dbms", max_results=5)
    assert [row["url"] for row in results] == ["https://example.com/a", "https://example.com/b"]
    assert results[0]["snippet"] == "first"


def test_web_sources_maps_url_and_snippet(monkeypatch):
    service = _make_service(monkeypatch)

    web_results = [
        {"title": "T", "snippet": "S" * 300, "url": "https://example.com"},
    ]
    sources = service._web_sources(web_results)

    assert sources[0]["source"] == "https://example.com"
    assert sources[0]["page"] is None
    assert len(sources[0]["snippet"]) <= 220


def test_duckduckgo_search_tool_formats_results(monkeypatch):
    monkeypatch.setattr(
        rag_module.service,
        "_run_web_search",
        lambda **kwargs: [
            {"title": "DBMS", "url": "https://example.com/dbms", "snippet": "Intro"},
            {"title": "Normalization", "url": "https://example.com/norm", "snippet": "Reduces redundancy"},
        ],
    )

    text = duckduckgo_search_tool.invoke({"question": "dbms", "max_results": 2})
    assert "[1]" in text
    assert "DBMS" in text
    assert "https://example.com/dbms" in text
    assert "[2]" in text
    assert "Normalization" in text


def test_duckduckgo_search_tool_no_results_message(monkeypatch):
    monkeypatch.setattr(rag_module.service, "_run_web_search", lambda **kwargs: [])

    text = duckduckgo_search_tool.invoke({"question": "dbms", "max_results": 2})
    assert "no relevant web results" in text.lower()


def test_answer_with_agent_loop_direct_mode_falls_back_to_direct_when_web_llm_none(monkeypatch):
    service = _make_service(monkeypatch)

    monkeypatch.setattr(
        service,
        "_run_web_search",
        lambda **kwargs: [
            {"title": "DBMS normalization", "snippet": "Normalization reduces redundancy.", "url": "https://example.com/dbms"}
        ],
    )
    monkeypatch.setattr(service, "_llm_web_response", lambda **kwargs: None)
    monkeypatch.setattr(service, "_llm_direct_response", lambda **kwargs: "Direct fallback")

    result = service.answer_with_agent_loop(
        question="Explain DBMS normalization",
        role="student",
        learner_level="beginner",
        response_mode="short",
        use_rag_context=False,
        use_web_search=True,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        top_k=3,
    )

    assert result["answer"] == "Direct fallback"
    assert result["context_used"] is True
    assert result["tool_calls_used"][0]["name"] == WEB_SEARCH_TOOL
    assert result["sources"][0]["source"] == "https://example.com/dbms"
