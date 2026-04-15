import sys
import types

from langchain_core.documents import Document


class FakeBase:
    pass


# ✅ MOCK DATABASE (keeps import path stable for service module)
mock_db = types.ModuleType("database")
mock_db.SessionLocal = None
mock_db.Base = FakeBase
sys.modules["database"] = mock_db

import pytest

from backend.services.rag import CONTENT_RETRIEVAL_TOOL, RagService


@pytest.fixture
def rag():
    return RagService()


# check file name prefix detection for comparison pdfs

def test_comparison_prefix_detected(rag):
    assert rag._should_use_section_chunking(pdf_path=__import__("pathlib").Path("comparison_java_python.pdf"), pages=[]) is True


def test_non_comparison_prefix_uses_default_splitter(rag):
    assert rag._should_use_section_chunking(pdf_path=__import__("pathlib").Path("notes_dbms.pdf"), pages=[]) is False


# test section extraction

def test_extract_numbered_sections_success(rag):
    text = "1. Syntax\nJava is verbose. Python is concise.\n2. Performance\nJava often runs faster."
    sections = rag._extract_numbered_sections(text)

    assert len(sections) == 2
    assert sections[0][0] == "1"
    assert sections[0][1] == "Syntax"
    assert "Java is verbose" in sections[0][2]


def test_extract_numbered_sections_none(rag):
    sections = rag._extract_numbered_sections("Java and Python are popular languages.")
    assert sections == []

# test section chunk metadata creation

def test_build_section_chunks_sets_comparison_metadata(rag):
    page = Document(
        page_content=(
            "1. Performance\n"
            "Java has JIT optimizations while Python emphasizes rapid development."
        ),
        metadata={"page": 1},
    )

    chunks = rag._build_section_chunks(
        pdf_path=__import__("pathlib").Path("comparison_javapython.pdf"),
        role="student",
        pages=[page],
    )

    assert len(chunks) == 1
    metadata = chunks[0].metadata
    assert metadata["source"] == "comparison_javapython.pdf"
    assert metadata["role"] == "student"
    assert metadata["section_number"] == "1"
    assert metadata["section_title"] == "Performance"
    assert metadata["chunk_type"] == "criterion_comparison"
    assert metadata["comparison_topics"] == "java,python"


# check fallback to recursive chunking when no sections found

def test_build_section_chunks_falls_back_to_recursive(monkeypatch, rag):
    page = Document(page_content="No numbered headings here", metadata={"page": 2})

    class DummySplitter:
        @staticmethod
        def split_documents(docs):
            return [Document(page_content="fallback chunk", metadata={"page": 2})]

    monkeypatch.setattr(rag, "_splitter", DummySplitter())

    chunks = rag._build_section_chunks(
        pdf_path=__import__("pathlib").Path("comparison_misc.pdf"),
        role="student",
        pages=[page],
    )

    assert len(chunks) == 1
    assert chunks[0].page_content == "fallback chunk"
    assert chunks[0].metadata["chunk_type"] == "default_recursive"
    assert chunks[0].metadata["source"] == "comparison_misc.pdf"


# check section builder for comparison pdf's


def test_chunk_pdf_documents_uses_section_builder_for_comparison(monkeypatch, rag):
    page = Document(page_content="1. Intro\nJava vs Python", metadata={"page": 1})

    expected = [Document(page_content="section chunk", metadata={"source": "comparison_java.pdf"})]
    monkeypatch.setattr(rag, "_build_section_chunks", lambda **kwargs: expected)

    out = rag._chunk_pdf_documents(
        pdf_path=__import__("pathlib").Path("comparison_java.pdf"),
        role="student",
        enriched_pages=[page],
    )

    assert out == expected


# comparsison tool full flow


def test_full_comparison_flow_uses_retrieval_tool(monkeypatch, rag):
    docs = [
        Document(
            page_content="Java startup is slower but long-running throughput is strong; Python is faster to prototype.",
            metadata={"source": "comparison_javapython.pdf", "page": 1},
        )
    ]

    monkeypatch.setattr(rag, "prepare", lambda: None)
    monkeypatch.setattr(rag, "_is_explanation_request", lambda _q: False)
    monkeypatch.setattr(rag, "_is_score_request", lambda _q: False)
    monkeypatch.setattr(rag, "_is_question_request", lambda _q: False)
    monkeypatch.setattr(rag, "_run_tool", lambda **kwargs: docs)
    monkeypatch.setattr(rag, "_deduplicate_docs", lambda values: values)
    monkeypatch.setattr(rag, "_llm_general_response", lambda **kwargs: "Java and Python differ in runtime and productivity trade-offs.")

    result = rag.answer_with_agent_loop(
        question="Compare Java and Python performance",
        role="student",
        selected_file="comparison_javapython.pdf",
        use_rag_context=True,
        use_web_search=False,
        use_score_tool=False,
        use_explanation_tool=False,
        user_id=1,
        top_k=3,
    )

    assert "differ" in result["answer"].lower()
    assert result["context_used"] is True
    assert len(result["tool_calls_used"]) >= 1
    assert result["tool_calls_used"][0]["name"] == CONTENT_RETRIEVAL_TOOL
    assert result["sources"][0]["source"] == "comparison_javapython.pdf"
