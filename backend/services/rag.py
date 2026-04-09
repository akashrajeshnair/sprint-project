from __future__ import annotations

import os
import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
DOCUMENTS_DIR = BASE_DIR / "documents"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 4
CONTENT_RETRIEVAL_TOOL = "content_retrieval"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

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
        top_k: int = DEFAULT_TOP_K,
    ) -> dict:
        return self.answer_with_agent_loop(
            question=question,
            role=role,
            learner_level=learner_level,
            response_mode=response_mode,
            selected_file=selected_file,
            use_rag_context=use_rag_context,
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

        docs: list[Document] = []
        tool_calls_used: list[dict] = []
        bounded_steps = max(1, min(int(max_steps or 2), 3))
        current_question = prompt

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

        if docs:
            answer = self._compose_answer_from_docs(docs=docs, response_mode=response_mode)
        else:
            llm_answer = self._llm_general_response(
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

        return {
            "answer": answer,
            "sources": sources,
            "context_used": bool(docs),
            "selected_file": selected_file,
            "use_rag_context": use_rag_context,
            "tool_calls_used": tool_calls_used,
            "agent_steps_run": len(tool_calls_used),
            "agent_loop_used": True,
        }

    def _compose_answer_from_docs(self, docs: list[Document], response_mode: str) -> str:
        clean_chunks = [doc.page_content.strip() for doc in docs if (doc.page_content or "").strip()]
        if not clean_chunks:
            return "I found context, but it was empty after cleanup."

        mode = (response_mode or "step-by-step").strip().lower()
        if mode == "short":
            return clean_chunks[0]
        return "\n\n".join(clean_chunks[: min(3, len(clean_chunks))])

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

    def _get_general_llm(self) -> ChatOpenAI | None:
        if self._general_llm is not None:
            return self._general_llm

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        model_name = os.getenv("GENERAL_LLM_MODEL", "gpt-4o-mini")
        try:
            self._general_llm = ChatOpenAI(model=model_name, temperature=0.2, api_key=api_key)
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

            chunk_docs = [doc for doc in self._splitter.split_documents(enriched_pages) if (doc.page_content or "").strip()]
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


service = RagService()


class ContentRetrievalInput(BaseModel):
    question: str = Field(min_length=1)
    role: str = Field(default="student", pattern="^(student|teacher)$")
    top_k: int = Field(default=1, ge=1, le=8)
    selected_file: str | None = None


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


def get_langchain_tools() -> list:
    """Return LangChain tools for agent/tool-calling orchestration."""
    return [content_retrieval]
