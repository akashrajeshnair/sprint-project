from __future__ import annotations

import re
import os
import shutil
import importlib
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

try:
    _ddgs_module = importlib.import_module("duckduckgo_search")
    DDGS: Any | None = getattr(_ddgs_module, "DDGS", None)
except Exception:  # pragma: no cover - optional dependency guard
    DDGS = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
DOCUMENTS_DIR = BASE_DIR / "documents"
PROJECT_ENV_PATH = BASE_DIR.parent / ".env"

# Load environment variables from project root so backend picks up API keys.
load_dotenv(PROJECT_ENV_PATH)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 4
CONTENT_RETRIEVAL_TOOL = "content_retrieval"
WEB_SEARCH_TOOL = "duckduckgo_search"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
SECTION_HEADER_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+([^\n]+)")

SUPPORTED_DOC_SUFFIXES = {".pdf"}
ROLE_MAP = {"student": "students", "teacher": "teachers"}


class RagService:
    def __init__(self) -> None:
        self._embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self._general_llm: ChatOpenAI | None = None
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )
        self._prepared = False
        self._vectorstores: dict[str, Chroma | None] = {"student": None, "teacher": None}
        self._indexed_files_by_role: dict[str, list[dict]] = {"student": [], "teacher": []}

    def prepare(self) -> None:
        self._prepare_dirs()
        if not self._prepared:
            self._prepared = True
            self.sync_documents_incremental()

    def list_indexed_files(self) -> list[dict]:
        return self._flatten_indexed_files()

    def sync_documents_incremental(self) -> dict:
        self._prepare_dirs()
        processed: list[dict] = []
        failed: list[dict] = []

        for role in ("student", "teacher"):
            try:
                role_processed = self._build_role_store(role)
                processed.extend(role_processed)
            except Exception as exc:
                failed.append({"file_name": f"{role}_documents", "error": str(exc)})

        return {
            "processed": processed,
            "skipped": [],
            "failed": failed,
            "indexed_files": self._flatten_indexed_files(),
        }

    # Backward compatibility.
    def sync_uploads_incremental(self) -> dict:
        return self.sync_documents_incremental()

    def build_index(self) -> int:
        result = self.sync_documents_incremental()
        return sum(int(item.get("chunks", 0)) for item in result["processed"])

    def answer_question(
        self,
        question: str,
        role: str = "student",
        learner_level: str = "beginner",
        response_mode: str = "step-by-step",
        selected_file: str | None = None,
        use_rag_context: bool = True,
        use_web_search: bool = False,
        top_k: int = DEFAULT_TOP_K,
    ) -> dict:
        return self.answer_with_agent_loop(
            question=question,
            role=role,
            learner_level=learner_level,
            response_mode=response_mode,
            selected_file=selected_file,
            use_rag_context=use_rag_context,
            use_web_search=use_web_search,
            top_k=top_k,
            max_steps=2,
        )

    def answer_with_agent_loop(
        self,
        question: str,
        role: str = "student",
        learner_level: str = "beginner",
        response_mode: str = "step-by-step",
        selected_file: str | None = None,
        use_rag_context: bool = True,
        use_web_search: bool = False,
        top_k: int = DEFAULT_TOP_K,
        max_steps: int = 2,
    ) -> dict:
        self.prepare()
        normalized_role = (role or "student").strip().lower()
        if normalized_role not in ROLE_MAP:
            normalized_role = "student"

        prompt = (question or "").strip()
        if not prompt:
            return {
                "answer": "Please ask a clear question.",
                "sources": [],
                "context_used": False,
                "tool_calls_used": [],
            }

        # In non-RAG mode, bypass retrieval entirely and send the raw question
        # directly to the configured LLM API.
        if not use_rag_context:
            tool_calls_used: list[dict] = []
            web_results: list[dict[str, str]] = []
            if use_web_search:
                web_results = self._run_web_search(question=prompt, max_results=max(3, min(int(top_k or 3) + 1, 8)))
                tool_calls_used.append(
                    {
                        "name": WEB_SEARCH_TOOL,
                        "arguments": {
                            "question": prompt,
                            "max_results": max(3, min(int(top_k or 3) + 1, 8)),
                        },
                        "result_count": len(web_results),
                        "step": 1,
                    }
                )

            web_answer = self._llm_web_response(
                question=prompt,
                response_mode=response_mode,
                web_results=web_results,
            )
            if web_answer:
                return {
                    "answer": web_answer,
                    "sources": self._web_sources(web_results),
                    "context_used": bool(web_results),
                    "selected_file": selected_file,
                    "use_rag_context": use_rag_context,
                    "use_web_search": use_web_search,
                    "tool_calls_used": tool_calls_used,
                    "agent_steps_run": len(tool_calls_used),
                    "agent_loop_used": True,
                }

            direct_answer = self._llm_direct_response(
                question=prompt,
                role=normalized_role,
                learner_level=learner_level,
                response_mode=response_mode,
            )
            if not direct_answer:
                direct_answer = (
                    "Direct LLM mode is enabled, but no LLM API key is available. "
                    "Set GROQ_API_KEY (or OPENAI_API_KEY) and try again."
                )
            return {
                "answer": direct_answer,
                "sources": self._web_sources(web_results),
                "context_used": bool(web_results),
                "selected_file": selected_file,
                "use_rag_context": use_rag_context,
                "use_web_search": use_web_search,
                "tool_calls_used": tool_calls_used,
                "agent_steps_run": len(tool_calls_used),
                "agent_loop_used": bool(tool_calls_used),
            }

        docs: list[Document] = []
        web_results: list[dict[str, str]] = []
        tool_calls_used: list[dict] = []
        bounded_steps = max(1, min(int(max_steps or 2), 3))
        current_question = prompt

        if self._is_question_request(prompt):
            qb_file = self._question_bank_file_for_role(normalized_role)
            if qb_file:
                selected_file = qb_file
                current_question = f"{normalized_role} question bank questions dbms quiz practice questions"

        for step in range(1, bounded_steps + 1):
            if not use_rag_context:
                break

            step_docs = self._run_tool(
                tool_name=CONTENT_RETRIEVAL_TOOL,
                question=current_question,
                role=normalized_role,
                selected_file=selected_file,
                top_k=top_k,
            )
            step_docs = self._deduplicate_docs(step_docs)
            tool_calls_used.append(
                {
                    "name": CONTENT_RETRIEVAL_TOOL,
                    "arguments": {
                        "question": current_question,
                        "role": normalized_role,
                        "selected_file": selected_file,
                        "top_k": int(top_k or DEFAULT_TOP_K),
                    },
                    "result_count": len(step_docs),
                    "step": step,
                }
            )

            if step_docs:
                docs = step_docs
                break

            if step < bounded_steps:
                current_question = self._refine_question_for_retry(prompt, step)

        if not docs and use_web_search:
            web_result_limit = max(3, min(int(top_k or 3) + 1, 8))
            web_results = self._run_web_search(question=prompt, max_results=web_result_limit)
            tool_calls_used.append(
                {
                    "name": WEB_SEARCH_TOOL,
                    "arguments": {
                        "question": prompt,
                        "max_results": web_result_limit,
                    },
                    "result_count": len(web_results),
                    "step": len(tool_calls_used) + 1,
                }
            )

        if docs:
            rag_answer = self._select_relevant_rag_answer(
                docs=docs,
                question=prompt,
                response_mode=response_mode,
                question_request=self._is_question_request(prompt),
            )
            if rag_answer is not None:
                answer = rag_answer
            else:
                llm_answer = self._llm_general_response(
                    question=prompt,
                    role=normalized_role,
                    learner_level=learner_level,
                    response_mode=response_mode,
                )
                if llm_answer:
                    answer = (
                        "no relevant chunks found in notes, falling back to general answer\n\n"
                        f"{llm_answer}"
                    )
                else:
                    general = self._general_response(
                        question=prompt,
                        role=normalized_role,
                        learner_level=learner_level,
                        response_mode=response_mode,
                    )
                    answer = (
                        "no relevant chunks found in notes, falling back to general answer\n\n"
                        f"{general}"
                    )
                docs = []
        else:
            llm_answer = self._llm_web_response(
                question=prompt,
                response_mode=response_mode,
                web_results=web_results,
            ) or self._llm_general_response(
                question=prompt,
                role=normalized_role,
                learner_level=learner_level,
                response_mode=response_mode,
            )
            if use_rag_context:
                if llm_answer:
                    answer = f"I couldn't find matching document context. Here's a general answer:\n\n{llm_answer}"
                else:
                    general = self._general_response(
                        question=prompt,
                        role=normalized_role,
                        learner_level=learner_level,
                        response_mode=response_mode,
                    )
                    answer = f"I couldn't find matching document context. Here's a general answer:\n\n{general}"
            else:
                answer = llm_answer or self._general_response(
                    question=prompt,
                    role=normalized_role,
                    learner_level=learner_level,
                    response_mode=response_mode,
                )
        sources = [
            {
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page"),
                "snippet": (doc.page_content or "")[:220],
            }
            for doc in docs
        ]
        if not sources and web_results:
            sources = self._web_sources(web_results)

        return {
            "answer": answer,
            "sources": sources,
            "context_used": bool(docs) or bool(web_results),
            "selected_file": selected_file,
            "use_rag_context": use_rag_context,
            "use_web_search": use_web_search,
            "tool_calls_used": tool_calls_used,
            "agent_steps_run": len(tool_calls_used),
            "agent_loop_used": True,
        }

    def _run_web_search(self, question: str, max_results: int = 5) -> list[dict[str, str]]:
        if DDGS is None:
            return []

        query = " ".join((question or "").split()).strip()
        if not query:
            return []

        limit = max(1, min(int(max_results or 5), 8))
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=limit))
        except Exception:
            return []

        seen: set[str] = set()
        normalized: list[dict[str, str]] = []
        for row in raw_results:
            if not isinstance(row, dict):
                continue
            title = " ".join(str(row.get("title", "")).split()).strip()
            snippet = " ".join(str(row.get("body", "")).split()).strip()
            url = " ".join(str(row.get("href", "")).split()).strip()
            key = f"{title}|{url}".lower()
            if not key.strip("|") or key in seen:
                continue
            seen.add(key)
            normalized.append({"title": title, "snippet": snippet, "url": url})
        return normalized

    def _web_sources(self, web_results: list[dict[str, str]]) -> list[dict]:
        return [
            {
                "source": item.get("url") or item.get("title") or "web",
                "page": None,
                "snippet": item.get("snippet", "")[:220],
            }
            for item in web_results
        ]

    def _llm_web_response(
        self,
        question: str,
        response_mode: str,
        web_results: list[dict[str, str]],
    ) -> str | None:
        if not web_results:
            return None

        llm = self._get_general_llm()
        if llm is None:
            fallback_lines: list[str] = []
            for idx, item in enumerate(web_results[:5], start=1):
                title = item.get("title") or "Untitled"
                snippet = item.get("snippet") or ""
                fallback_lines.append(f"{idx}. {title}: {snippet}")
            if not fallback_lines:
                return None
            return "Web summary (LLM unavailable):\n" + "\n".join(fallback_lines)

        mode = (response_mode or "step-by-step").strip().lower()
        if mode not in {"short", "step-by-step"}:
            mode = "step-by-step"

        web_context = "\n".join(
            f"[{idx}] {item.get('title', 'Untitled')} | {item.get('url', '')}\n{item.get('snippet', '')}"
            for idx, item in enumerate(web_results, start=1)
        )
        system_prompt = (
            "You are a helpful assistant that answers using web search snippets only. "
            "Use only facts present in snippets. If snippets are insufficient, say so clearly. "
            "Do not invent URLs or unsupported claims."
        )
        user_prompt = (
            f"Question: {question}\n"
            f"Response mode: {mode}\n"
            "Use the snippets below to answer accurately and concisely.\n\n"
            f"{web_context}"
        )

        try:
            result = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        except Exception:
            return None

        content = getattr(result, "content", "")
        if isinstance(content, list):
            content = " ".join(str(part) for part in content)
        if not isinstance(content, str):
            return None

        text = content.strip()
        return text or None

    def _select_relevant_rag_answer(
        self,
        docs: list[Document],
        question: str,
        response_mode: str,
        question_request: bool = False,
    ) -> str | None:
        llm = self._get_general_llm()
        clean_docs = [doc for doc in docs if (doc.page_content or "").strip()]
        if not clean_docs or llm is None:
            return None

        chunk_lines = []
        for idx, doc in enumerate(clean_docs, start=1):
            source = " ".join(str(doc.metadata.get("source", "unknown")).split())
            page = doc.metadata.get("page")
            page_label = f"page {page}" if page is not None else "unknown page"
            text = " ".join((doc.page_content or "").split())
            if not text:
                continue
            chunk_lines.append(f"Chunk {idx} [{source}, {page_label}]: {text}")

        if not chunk_lines:
            return None

        mode = (response_mode or "step-by-step").strip().lower()
        if mode not in {"short", "step-by-step"}:
            mode = "step-by-step"

        system_prompt = (
            "You answer using retrieved RAG chunks only. "
            "You may combine the most relevant parts from multiple chunks and order them naturally. "
            "Do not mention sources or chunk numbers in the final answer. "
            "If the chunks are unrelated or do not answer the question, return NONE. "
            + (
                "If the user is asking for questions, return only the questions from the chunks, and do not include explanatory text."
                if question_request
                else ""
            )
        )
        user_prompt = (
            f"Question: {question}\n"
            f"Response mode: {mode}\n"
            "Use only the chunks below. If some chunks are irrelevant, ignore them completely. "
            "If the chunks are not related enough to answer, return NONE. "
            + (
                "When the user asks for questions, extract only the question statements from the question-bank chunks. "
                "Do not include explanations, answers, or extra content."
                if question_request
                else ""
            )
            + "\n\n"
            + "\n".join(chunk_lines)
        )

        try:
            result = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        except Exception:
            return None

        content = getattr(result, "content", "")
        if isinstance(content, list):
            content = " ".join(str(part) for part in content)

        if not isinstance(content, str):
            return None

        raw_text = content.strip()
        if not raw_text or raw_text.upper() == "NONE":
            return None

        return raw_text

    def _is_question_request(self, prompt: str) -> bool:
        text = (prompt or "").strip().lower()
        if not text:
            return False

        markers = (
            "give questions",
            "generate questions",
            "create questions",
            "show questions",
            "question bank",
            "quiz questions",
            "practice questions",
        )
        return any(marker in text for marker in markers)

    def _question_bank_file_for_role(self, role: str) -> str | None:
        normalized_role = (role or "student").strip().lower()
        if normalized_role == "teacher":
            return "db_qb_teacher.pdf"
        return "db_qb_student.pdf"

    def _refine_question_for_retry(self, question: str, step: int) -> str:
        base = " ".join((question or "").split()).strip()
        if not base:
            return question
        if step == 1:
            return f"{base} fundamentals key concepts"
        return base

    def retrieve(
        self,
        question: str,
        role: str = "student",
        selected_file: str | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[Document]:
        self.prepare()
        normalized_role = (role or "student").strip().lower()
        if normalized_role not in ROLE_MAP:
            normalized_role = "student"

        store = self._vectorstores.get(normalized_role)
        if store is None:
            return []

        k = max(1, int(top_k or DEFAULT_TOP_K))
        try:
            docs = self._search_store(store=store, question=question, k=k)
        except Exception as exc:
            if self._is_chroma_schema_error(exc):
                self._recover_role_store(normalized_role)
                recovered_store = self._vectorstores.get(normalized_role)
                if recovered_store is None:
                    return []
                try:
                    docs = self._search_store(store=recovered_store, question=question, k=k)
                except Exception:
                    return []
            else:
                return []

        if selected_file:
            selected = selected_file.strip().lower()
            docs = [d for d in docs if str(d.metadata.get("source", "")).lower() == selected]

        docs = self._deduplicate_docs(docs)
        return docs[:k]

    def _search_store(self, store: Chroma, question: str, k: int) -> list[Document]:
        try:
            return store.max_marginal_relevance_search(
                question,
                k=k,
                fetch_k=max(10, k * 4),
            )
        except Exception:
            return store.similarity_search(question, k=max(10, k * 4))

    def _is_chroma_schema_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return "no such table: collections" in msg or (
            "chromadb.errors.internalerror" in msg and "collections" in msg and "no such table" in msg
        )

    def _recover_role_store(self, role: str) -> None:
        try:
            self._build_role_store(role)
        except Exception:
            self._vectorstores[role] = None

    def _deduplicate_docs(self, docs: list[Document]) -> list[Document]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[Document] = []
        for doc in docs:
            metadata = doc.metadata or {}
            source = str(metadata.get("source", "unknown"))
            page = str(metadata.get("page", metadata.get("page_number", "")))
            text = " ".join((doc.page_content or "").split()).strip().lower()
            if not text:
                continue
            key = (source, page, text)
            if key in seen:
                continue
            seen.add(key)
            unique.append(doc)
        return unique

    def _run_tool(
        self,
        tool_name: str,
        question: str,
        role: str,
        selected_file: str | None,
        top_k: int,
    ) -> list[Document]:
        if tool_name != CONTENT_RETRIEVAL_TOOL:
            return []
        return self.retrieve(
            question=question,
            role=role,
            selected_file=selected_file,
            top_k=top_k,
        )

    def _general_response(
        self,
        question: str,
        role: str,
        learner_level: str,
        response_mode: str,
    ) -> str:
        clean_q = " ".join((question or "").split()).strip()
        level = (learner_level or "beginner").strip().lower()
        mode = (response_mode or "step-by-step").strip().lower()

        if mode == "short":
            return (
                f"General explanation for {role} ({level}): {clean_q}. "
                "Break the topic into definition, core concepts, and one practical example."
            )

        return (
            f"General explanation for {role} ({level}) on: {clean_q}\n"
            "1. Start with a clear definition and why it matters.\n"
            "2. Cover core concepts and how they relate.\n"
            "3. Walk through one concrete example.\n"
            "4. Summarize key takeaways and common mistakes.\n"
            "5. End with a quick self-check question to reinforce learning."
        )

    def _llm_general_response(
        self,
        question: str,
        role: str,
        learner_level: str,
        response_mode: str,
    ) -> str | None:
        llm = self._get_general_llm()
        if llm is None:
            return None

        style = "brief" if (response_mode or "").strip().lower() == "short" else "step-by-step"
        system_prompt = (
            "You are a helpful education assistant. "
            "Answer clearly and safely. Avoid markdown tables unless needed. "
            "Keep examples practical and correct."
        )
        user_prompt = (
            f"Role: {role}\n"
            f"Learner level: {learner_level}\n"
            f"Style: {style}\n"
            f"Question: {question}\n"
            "Provide a direct, understandable answer."
        )

        try:
            result = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        except Exception:
            return None

        content = getattr(result, "content", "")
        if isinstance(content, str):
            text = content.strip()
            return text or None
        if isinstance(content, list):
            merged = " ".join(str(part) for part in content).strip()
            return merged or None
        return None

    def _llm_direct_response(
        self,
        question: str,
        role: str,
        learner_level: str,
        response_mode: str,
    ) -> str | None:
        llm = self._get_general_llm()
        if llm is None:
            return None

        level = (learner_level or "beginner").strip().lower()
        if level not in {"beginner", "intermediate", "advanced"}:
            level = "beginner"

        mode = (response_mode or "step-by-step").strip().lower()
        if mode not in {"step-by-step", "short"}:
            mode = "step-by-step"

        if mode == "short":
            if level == "beginner":
                length_rule = "Keep the response around 70-110 words with very simple language."
                complexity_rule = "Use one clear concept and one tiny example."
                max_tokens = 180
                max_words = 130
            elif level == "intermediate":
                length_rule = "Keep the response around 60-90 words."
                complexity_rule = "Use concise explanation with one practical detail."
                max_tokens = 150
                max_words = 110
            else:
                length_rule = "Keep the response tight: around 40-70 words maximum."
                complexity_rule = "Use precise technical wording and avoid extra explanation."
                max_tokens = 120
                max_words = 85
        else:
            if level == "beginner":
                length_rule = "Provide a fuller explanation in about 180-260 words."
                complexity_rule = "Use simple language, include 4-6 numbered steps, and one clear example."
                max_tokens = 420
                max_words = 300
            elif level == "intermediate":
                length_rule = "Provide a medium explanation in about 120-180 words."
                complexity_rule = "Use 3-5 numbered steps, practical terminology, and one concise example."
                max_tokens = 320
                max_words = 220
            else:
                length_rule = "Keep it compact even in step-by-step mode: about 80-120 words."
                complexity_rule = (
                    "Use 2-4 concise numbered steps with higher-level technical clarity, "
                    "and avoid long explanations."
                )
                max_tokens = 220
                max_words = 150

        system_prompt = (
            "You are a helpful education assistant. "
            "Follow format, length, and complexity instructions exactly. "
            "Do not include retrieval sources or mention RAG. "
            "Do not use markdown headings, markdown tables, or decorative formatting."
        )
        user_prompt = (
            f"Role: {role}\n"
            f"Learner level: {level}\n"
            f"Response mode: {mode}\n"
            f"Length rule: {length_rule}\n"
            f"Complexity rule: {complexity_rule}\n"
            "Output rules:\n"
            "- If response mode is step-by-step, return numbered points.\n"
            "- If response mode is short, return one compact paragraph.\n"
            "- Keep the answer directly focused on the question.\n"
            "- Keep within the requested size limits.\n"
            f"Question: {question}"
        )

        try:
            llm_client = llm
            try:
                llm_client = llm.bind(max_tokens=max_tokens)
            except Exception:
                llm_client = llm
            result = llm_client.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        except Exception:
            return None

        content = getattr(result, "content", "")
        if isinstance(content, str):
            text = " ".join(content.strip().split())
            if len(text.split()) > max_words:
                text = " ".join(text.split()[:max_words]).rstrip(" ,.;:") + "."
            return text or None
        if isinstance(content, list):
            merged = " ".join(str(part) for part in content).strip()
            merged = " ".join(merged.split())
            if len(merged.split()) > max_words:
                merged = " ".join(merged.split()[:max_words]).rstrip(" ,.;:") + "."
            return merged or None
        return None

    def _get_general_llm(self) -> ChatOpenAI | None:
        if self._general_llm is not None:
            return self._general_llm

        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            model_name = os.getenv(
                "GROQ_LLM_MODEL",
                os.getenv("GENERAL_LLM_MODEL", "llama-3.3-70b-versatile"),
            )
            base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
            try:
                self._general_llm = ChatOpenAI(
                    model=model_name,
                    temperature=0.2,
                    api_key=groq_api_key,
                    base_url=base_url,
                )
                return self._general_llm
            except Exception:
                self._general_llm = None

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return None

        model_name = os.getenv("GENERAL_LLM_MODEL", "gpt-4o-mini")
        try:
            self._general_llm = ChatOpenAI(model=model_name, temperature=0.2, api_key=openai_api_key)
        except Exception:
            return None
        return self._general_llm

    def _prepare_dirs(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        (DOCUMENTS_DIR / "students").mkdir(parents=True, exist_ok=True)
        (DOCUMENTS_DIR / "teachers").mkdir(parents=True, exist_ok=True)

    def _flatten_indexed_files(self) -> list[dict]:
        files: list[dict] = []
        for role, entries in self._indexed_files_by_role.items():
            for item in entries:
                files.append({**item, "role": role})
        return files

    def _build_role_store(self, role: str) -> list[dict]:
        file_paths = self._get_role_pdfs(role)
        all_docs: list[Document] = []
        processed: list[dict] = []

        for pdf_path in file_paths:
            page_docs = PyPDFLoader(str(pdf_path)).load()
            enriched_pages: list[Document] = []
            for page in page_docs:
                text = (page.page_content or "").strip()
                if not text:
                    continue
                metadata = dict(page.metadata or {})
                metadata["source"] = pdf_path.name
                metadata["role"] = role
                enriched_pages.append(Document(page_content=text, metadata=metadata))

            chunk_docs = self._chunk_pdf_documents(
                pdf_path=pdf_path,
                role=role,
                enriched_pages=enriched_pages,
            )
            if chunk_docs:
                all_docs.extend(chunk_docs)
                processed.append({"file_name": pdf_path.name, "chunks": len(chunk_docs), "role": role})

        role_collection = ROLE_MAP[role]
        role_dir = CHROMA_DIR / role_collection
        if role_dir.exists():
            shutil.rmtree(role_dir)
        role_dir.mkdir(parents=True, exist_ok=True)

        # rebuild collection every sync (simple and deterministic)
        if all_docs:
            self._vectorstores[role] = Chroma.from_documents(
                documents=all_docs,
                embedding=self._embeddings,
                collection_name=role_collection,
                persist_directory=str(role_dir),
            )
        else:
            self._vectorstores[role] = None

        by_name: dict[str, int] = {}
        for item in processed:
            by_name[item["file_name"]] = by_name.get(item["file_name"], 0) + int(item["chunks"])

        self._indexed_files_by_role[role] = [
            {
                "file_name": name,
                "chunks": chunks,
                "collection": role_collection,
                "indexed_at": "",
            }
            for name, chunks in sorted(by_name.items())
        ]
        return processed

    def _get_role_pdfs(self, role: str) -> list[Path]:
        folder_plural = DOCUMENTS_DIR / ROLE_MAP[role]
        folder_singular = DOCUMENTS_DIR / role
        base_folder = folder_plural if folder_plural.exists() else folder_singular
        if not base_folder.exists():
            return []
        return sorted(
            [
                path
                for path in base_folder.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_DOC_SUFFIXES
            ]
        )

    def _chunk_pdf_documents(self, pdf_path: Path, role: str, enriched_pages: list[Document]) -> list[Document]:
        if not enriched_pages:
            return []

        if self._should_use_section_chunking(pdf_path=pdf_path, pages=enriched_pages):
            section_docs = self._build_section_chunks(pdf_path=pdf_path, role=role, pages=enriched_pages)
            if section_docs:
                return section_docs

        return [doc for doc in self._splitter.split_documents(enriched_pages) if (doc.page_content or "").strip()]

    def _should_use_section_chunking(self, pdf_path: Path, pages: list[Document]) -> bool:
        _ = pages  # reserved for potential future rule expansion
        file_name = pdf_path.stem.strip().lower()
        return file_name.startswith("comparison")

    def _extract_numbered_sections(self, text: str) -> list[tuple[str, str, str]]:
        normalized = (text or "").strip()
        if not normalized:
            return []

        matches = list(SECTION_HEADER_RE.finditer(normalized))
        if not matches:
            return []

        sections: list[tuple[str, str, str]] = []
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(normalized)
            section_number = (match.group(1) or "").strip()
            section_title = (match.group(2) or "").strip().rstrip(":")
            section_text = normalized[start:end].strip()
            if section_text:
                sections.append((section_number, section_title, section_text))
        return sections

    def _build_section_chunks(self, pdf_path: Path, role: str, pages: list[Document]) -> list[Document]:
        section_docs: list[Document] = []

        for page in pages:
            base_metadata = dict(page.metadata or {})
            text = (page.page_content or "").strip()
            if not text:
                continue

            page_sections = self._extract_numbered_sections(text)
            if not page_sections:
                page_fallback_docs = self._splitter.split_documents([page])
                for doc in page_fallback_docs:
                    if not (doc.page_content or "").strip():
                        continue
                    fallback_meta = dict(doc.metadata or {})
                    fallback_meta["chunk_type"] = "default_recursive"
                    fallback_meta["source"] = pdf_path.name
                    fallback_meta["role"] = role
                    section_docs.append(Document(page_content=doc.page_content, metadata=fallback_meta))
                continue

            for section_number, section_title, section_text in page_sections:
                lowered = section_text.lower()
                chunk_type = "criterion_comparison" if ("java" in lowered and "python" in lowered) else "section"
                metadata = dict(base_metadata)
                metadata.update(
                    {
                        "source": pdf_path.name,
                        "role": role,
                        "section_number": section_number,
                        "section_title": section_title,
                        "chunk_type": chunk_type,
                        "comparison_topics": "java,python" if chunk_type == "criterion_comparison" else "",
                    }
                )
                section_docs.append(Document(page_content=section_text, metadata=metadata))

        return [doc for doc in section_docs if (doc.page_content or "").strip()]


service = RagService()


class ContentRetrievalInput(BaseModel):
    question: str = Field(min_length=1)
    role: str = Field(default="student", pattern="^(student|teacher)$")
    top_k: int = Field(default=1, ge=1, le=8)
    selected_file: str | None = None


class WebSearchInput(BaseModel):
    question: str = Field(min_length=1)
    max_results: int = Field(default=5, ge=1, le=8)


@tool(CONTENT_RETRIEVAL_TOOL, args_schema=ContentRetrievalInput)
def content_retrieval(
    question: str,
    role: str = "student",
    top_k: int = 1,
    selected_file: str | None = None,
) -> str:
    """Retrieve relevant role-scoped content from indexed PDFs."""
    docs = service.retrieve(
        question=question,
        role=role,
        selected_file=selected_file,
        top_k=top_k,
    )
    if not docs:
        return "No relevant content found for this role."
    return "\n".join(
        f"[{idx}] ({doc.metadata.get('source', 'unknown')}) {doc.page_content}"
        for idx, doc in enumerate(docs, start=1)
    )


@tool(WEB_SEARCH_TOOL, args_schema=WebSearchInput)
def duckduckgo_search_tool(question: str, max_results: int = 5) -> str:
    """Run DuckDuckGo web search and return concise snippets."""
    results = service._run_web_search(question=question, max_results=max_results)
    if not results:
        return "No relevant web results found."

    return "\n".join(
        f"[{idx}] {item.get('title', 'Untitled')} ({item.get('url', '')}) - {item.get('snippet', '')}"
        for idx, item in enumerate(results, start=1)
    )


def get_langchain_tools() -> list:
    """Return LangChain tools for agent/tool-calling orchestration."""
    return [content_retrieval, duckduckgo_search_tool]
