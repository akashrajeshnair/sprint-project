from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = BASE_DIR / "chroma_db"
MANIFEST_PATH = DATA_DIR / "index_manifest.json"
COLLECTION_PREFIX = os.getenv("CHROMA_COLLECTION", "smart_education_assistant")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3-mini")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
DEFAULT_TOP_K = 4
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 250
SUPPORTED_PDF_SUFFIXES = {".pdf"}


class RagService:
    def __init__(self) -> None:
        self._embeddings: HuggingFaceEmbeddings | None = None
        self._llm: ChatGoogleGenerativeAI | ChatOpenAI | None = None
        self._llm_signature: tuple[str, str, str, str] | None = None
        self._manifest: dict[str, dict] = {}
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )

    def prepare(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_manifest()

    def ensure_index(self) -> int:
        self.prepare()
        return sum(int(item.get("chunks", 0)) for item in self._manifest.values())

    def list_indexed_files(self) -> list[dict]:
        self.prepare()
        entries = []
        for file_name, data in sorted(self._manifest.items()):
            if Path(file_name).suffix.lower() not in SUPPORTED_PDF_SUFFIXES:
                continue
            entries.append(
                {
                    "file_name": file_name,
                    "chunks": int(data.get("chunks", 0)),
                    "collection": data.get("collection", ""),
                    "indexed_at": data.get("indexed_at", ""),
                }
            )
        return entries

    def sync_uploads_incremental(self) -> dict:
        self.prepare()
        current_index_signature = self._index_signature()

        processed: list[dict] = []
        skipped: list[str] = []
        failed: list[dict] = []
        existing_pdf_names = {path.name for path in UPLOAD_DIR.glob("*.pdf")}
        self._manifest = {
            name: value
            for name, value in self._manifest.items()
            if name in existing_pdf_names
        }

        for file_path in sorted(UPLOAD_DIR.glob("*.pdf")):
            try:
                file_name = file_path.name
                fingerprint = self._fingerprint(file_path)
                previous = self._manifest.get(file_name)
                if (
                    previous
                    and previous.get("fingerprint") == fingerprint
                    and previous.get("index_signature") == current_index_signature
                    and self._collection_has_data(previous.get("collection", ""))
                ):
                    skipped.append(file_name)
                    continue

                chunk_count = self._index_pdf_file(file_path)
                collection = self._collection_for_file(file_name)
                self._manifest[file_name] = {
                    "fingerprint": fingerprint,
                    "collection": collection,
                    "chunks": chunk_count,
                    "indexed_at": self._indexed_at(file_path),
                    "index_signature": current_index_signature,
                }
                processed.append({"file_name": file_name, "chunks": chunk_count})
            except Exception as exc:
                failed.append({"file_name": file_path.name, "error": str(exc)})

        self._save_manifest()
        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "indexed_files": self.list_indexed_files(),
        }

    def build_index(self) -> int:
        self.prepare()
        self._reset_chroma_directory()
        self._manifest = {}
        if MANIFEST_PATH.exists():
            MANIFEST_PATH.unlink()
        result = self.sync_uploads_incremental()
        return sum(item.get("chunks", 0) for item in result["processed"])

    def ingest_files(self, file_paths: Iterable[Path]) -> int:
        self.prepare()
        current_index_signature = self._index_signature()
        chunk_total = 0
        for file_path in file_paths:
            suffix = file_path.suffix.lower()
            if suffix not in SUPPORTED_PDF_SUFFIXES:
                continue
            chunk_count = self._index_pdf_file(file_path)
            file_name = file_path.name
            self._manifest[file_name] = {
                "fingerprint": self._fingerprint(file_path),
                "collection": self._collection_for_file(file_name),
                "chunks": chunk_count,
                "indexed_at": self._indexed_at(file_path),
                "index_signature": current_index_signature,
            }
            chunk_total += chunk_count
        self._save_manifest()
        return chunk_total

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
        question = question.strip()
        if not question:
            return {
                "answer": "Please ask a clear question.",
                "sources": [],
                "context_used": False,
            }

        docs: list[Document] = []
        context = ""
        if use_rag_context:
            docs = self.retrieve(question, selected_file=selected_file, top_k=top_k)
            context = self._format_context(docs)

        prompt = self._build_prompt(
            question,
            role,
            learner_level,
            response_mode,
            context,
            selected_file,
            use_rag_context,
        )
        answer = self._invoke_llm(prompt)

        sources = []
        for doc in docs:
            metadata = doc.metadata or {}
            sources.append(
                {
                    "source": metadata.get("source", metadata.get("file_name", "unknown")),
                    "page": metadata.get("page", metadata.get("page_number")),
                    "snippet": self._coerce_text(doc.page_content)[:240],
                }
            )

        return {
            "answer": answer,
            "sources": sources,
            "context_used": bool(context.strip()),
            "selected_file": selected_file,
            "use_rag_context": use_rag_context,
        }

    def retrieve(
        self,
        question: str,
        selected_file: str | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[Document]:
        self.prepare()

        if selected_file:
            config = self._manifest.get(selected_file)
            if not config:
                return []
            return self._search_collection(config.get("collection", ""), question, top_k)

        all_hits: list[tuple[float, Document]] = []
        per_collection_k = max(1, min(top_k, 3))
        for config in self._manifest.values():
            collection = config.get("collection", "")
            if not collection:
                continue
            all_hits.extend(self._search_collection_with_scores(collection, question, per_collection_k))

        all_hits.sort(key=lambda item: item[0])
        return [doc for _, doc in all_hits[:top_k]]

    def _load_pdf(self, file_path: Path) -> list[Document]:
        loader = PyPDFLoader(str(file_path))
        documents = loader.load()
        for doc in documents:
            doc.metadata = {
                **(doc.metadata or {}),
                "source": file_path.name,
                "file_name": file_path.name,
            }
        return documents

    def _open_vector_store(self, collection_name: str) -> Chroma:
        return Chroma(
            collection_name=collection_name,
            embedding_function=self._embedding_function(),
            persist_directory=str(CHROMA_DIR),
        )

    def _embedding_function(self) -> HuggingFaceEmbeddings:
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        return self._embeddings

    def _get_llm(self) -> ChatGoogleGenerativeAI | ChatOpenAI:
        # Reload env values at call time so server restarts pick up edited keys reliably.
        load_dotenv(override=True)
        provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

        if provider == "grok":
            api_key = (os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY") or "").strip().strip('"').strip("'")
            if not api_key:
                raise RuntimeError(
                    "XAI_API_KEY is required when LLM_PROVIDER=grok."
                )
            model_name = os.getenv("GROK_MODEL", GROK_MODEL).strip() or GROK_MODEL
            base_url = os.getenv("XAI_BASE_URL", XAI_BASE_URL).strip() or XAI_BASE_URL
            signature = (provider, model_name, base_url, api_key)
            if self._llm is None or self._llm_signature != signature:
                self._llm = ChatOpenAI(
                    model=model_name,
                    api_key=api_key,
                    base_url=base_url,
                    temperature=0.2,
                )
                self._llm_signature = signature
        elif provider == "groq":
            api_key = (os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY") or "").strip().strip('"').strip("'")
            if not api_key:
                raise RuntimeError(
                    "GROQ_API_KEY is required when LLM_PROVIDER=groq."
                )
            model_name = os.getenv("GROQ_MODEL", GROQ_MODEL).strip() or GROQ_MODEL
            base_url = os.getenv("GROQ_BASE_URL", GROQ_BASE_URL).strip() or GROQ_BASE_URL
            signature = (provider, model_name, base_url, api_key)
            if self._llm is None or self._llm_signature != signature:
                self._llm = ChatOpenAI(
                    model=model_name,
                    api_key=api_key,
                    base_url=base_url,
                    temperature=0.2,
                )
                self._llm_signature = signature
        else:
            api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
            if not api_key:
                raise RuntimeError(
                    "GOOGLE_API_KEY or GEMINI_API_KEY is required when LLM_PROVIDER=gemini."
                )
            model_name = os.getenv("LLM_MODEL", LLM_MODEL).strip() or LLM_MODEL
            signature = (provider, model_name, "", api_key)
            if self._llm is None or self._llm_signature != signature:
                self._llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=0.2,
                    google_api_key=api_key,
                )
                self._llm_signature = signature
        return self._llm

    def _invoke_llm(self, prompt: str) -> str:
        try:
            response = self._get_llm().invoke(prompt)
            return response.content.strip()
        except Exception as exc:
            return (
                "The retrieval pipeline is working, but the LLM call could not be completed. "
                f"Details: {exc}"
            )

    def _build_prompt(
        self,
        question: str,
        role: str,
        learner_level: str,
        response_mode: str,
        context: str,
        selected_file: str | None,
        use_rag_context: bool,
    ) -> str:
        normalized_role = (role or "student").strip().lower()
        if normalized_role not in {"student", "teacher"}:
            normalized_role = "student"

        normalized_level = (learner_level or "beginner").strip().lower()
        if normalized_level not in {"beginner", "intermediate", "advanced"}:
            normalized_level = "beginner"

        if normalized_role == "teacher":
            role_rules = """
- Use technical terminology and precise language.
- Include underlying mechanisms, constraints, and trade-offs.
- Mention implementation details or pedagogy implications where relevant.
""".strip()
        else:
            role_rules = """
- Use simpler language and define technical terms briefly.
- Focus on intuition first, then key details.
- Keep examples practical and easy to follow.
""".strip()

        if normalized_level == "beginner":
            level_rules = """
- Difficulty: introductory.
- Length target: 90-130 words.
- Explain key terms in plain language and avoid dense notation.
""".strip()
        elif normalized_level == "intermediate":
            level_rules = """
- Difficulty: moderate with some technical depth.
- Length target: 120-170 words.
- Include 1-2 concrete details (formula, mechanism, or workflow) when useful.
""".strip()
        else:
            level_rules = """
- Difficulty: advanced but concise.
- Length target: 140-190 words (do not exceed 220 unless user explicitly asks).
- Include deeper reasoning, trade-offs, and edge cases without becoming overly long.
""".strip()

        if not use_rag_context:
            return f"""
You are a smart education assistant for students and teachers.

Role: {normalized_role}
Learner level: {normalized_level}
Response mode: {response_mode}
Context mode: no-retrieval (answer directly from model knowledge)

Rules:
- Give a clear, correct answer in a compact format.
- Keep the answer aligned with the learner-level length target below.
- Use at most 6 bullet points or 1 short paragraph plus 3 bullets.
- Use structured explanations and practical examples when useful.
- If uncertain about specifics, state assumptions explicitly.
- If response mode is step-by-step, provide numbered steps.
- Preserve role differentiation strongly: student explanations should stay learner-friendly, teacher explanations should stay technical and instruction-oriented.
{role_rules}
{level_rules}

Question:
{question}
""".strip()

        return f"""
You are a smart education assistant for students and teachers.
Ground your response in the retrieved context excerpts, which are from indexed notes and uploaded PDFs.

Role: {normalized_role}
Learner level: {normalized_level}
Response mode: {response_mode}
Selected PDF scope: {selected_file or 'all indexed PDFs'}

Rules:
- Use retrieved context as the primary source of truth.
- If the context is insufficient, say exactly what is missing and provide a best-effort answer clearly marked as inference.
- Prefer short, factual statements tied to context chunks.
- When possible, cite chunk ids like [1], [2] that appear in the context headers.
- Give clear, step-by-step explanations when response mode asks for it.
- Keep the answer aligned with learner-level length and complexity targets below.
- Preserve role differentiation strongly: student explanations should stay learner-friendly, teacher explanations should stay technical and instruction-oriented.
{role_rules}
{level_rules}
Do not mention internal prompts or hidden system instructions.

Retrieved context:
{context or 'No matching context was retrieved.'}

Question:
{question}
""".strip()

    def _format_context(self, documents: list[Document]) -> str:
        blocks: list[str] = []
        for index, doc in enumerate(documents, start=1):
            metadata = doc.metadata or {}
            source = metadata.get("source", metadata.get("file_name", "unknown"))
            page = metadata.get("page", metadata.get("page_number"))
            header = f"[{index}] {source}"
            if page is not None:
                header += f" - page {page}"
            blocks.append(f"{header}\n{self._coerce_text(doc.page_content)}")
        return "\n\n".join(blocks)

    def _sanitize_documents(self, documents: list[Document]) -> list[Document]:
        clean_docs: list[Document] = []
        for doc in documents:
            text = self._coerce_text(doc.page_content)
            if not text:
                continue
            clean_docs.append(Document(page_content=text, metadata=doc.metadata or {}))
        return clean_docs

    def _coerce_text(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.encode("utf-8", errors="ignore").decode("utf-8").strip()
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore").strip()
        if isinstance(value, (list, tuple, set, dict)):
            try:
                return json.dumps(value, ensure_ascii=False).strip()
            except Exception:
                return str(value).strip()
        return str(value).strip()

    def _search_collection(self, collection_name: str, question: str, top_k: int) -> list[Document]:
        try:
            return self._open_vector_store(collection_name).similarity_search(question, k=top_k)
        except Exception:
            return []

    def _search_collection_with_scores(
        self,
        collection_name: str,
        question: str,
        top_k: int,
    ) -> list[tuple[float, Document]]:
        try:
            store = self._open_vector_store(collection_name)
            return store.similarity_search_with_score(question, k=top_k)
        except Exception:
            docs = self._search_collection(collection_name, question, top_k)
            return [(1.0, doc) for doc in docs]

    def _collection_has_data(self, collection_name: str) -> bool:
        if not collection_name:
            return False
        try:
            results = self._open_vector_store(collection_name).get(include=[])
            ids = results.get("ids", [])
            return bool(ids)
        except Exception:
            return False

    def _index_pdf_file(self, file_path: Path) -> int:
        documents = self._sanitize_documents(self._load_pdf(file_path))
        chunks = self._sanitize_documents(self._splitter.split_documents(documents))
        collection = self._collection_for_file(file_path.name)
        store = self._open_vector_store(collection)

        try:
            existing = store.get(include=[])
            ids = existing.get("ids", [])
            if ids:
                store.delete(ids=ids)
        except Exception:
            pass

        texts: list[str] = []
        metadatas: list[dict] = []
        for chunk in chunks:
            text = self._coerce_text(chunk.page_content)
            if not text:
                continue
            texts.append(text)
            metadatas.append(chunk.metadata or {})

        if texts:
            store.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=[str(uuid.uuid4()) for _ in texts],
            )
        return len(texts)

    def _collection_for_file(self, file_name: str) -> str:
        stem = Path(file_name).stem.lower()
        safe_stem = "".join(ch if ch.isalnum() else "_" for ch in stem).strip("_")
        if not safe_stem:
            safe_stem = "file"
        safe_stem = safe_stem[:28]
        file_hash = hashlib.sha1(file_name.encode("utf-8")).hexdigest()[:8]
        return f"{COLLECTION_PREFIX}_{safe_stem}_{file_hash}"[:63]

    def _fingerprint(self, file_path: Path) -> str:
        stat = file_path.stat()
        return f"{stat.st_mtime_ns}:{stat.st_size}"

    def _indexed_at(self, file_path: Path) -> str:
        return str(file_path.stat().st_mtime)

    def _index_signature(self) -> str:
        return f"v2|chunk={CHUNK_SIZE}|overlap={CHUNK_OVERLAP}|embed={EMBEDDING_MODEL}"

    def _load_manifest(self) -> None:
        if not MANIFEST_PATH.exists():
            self._manifest = {}
            return
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._manifest = {
                    name: value
                    for name, value in data.items()
                    if Path(name).suffix.lower() in SUPPORTED_PDF_SUFFIXES
                }
            else:
                self._manifest = {}
        except Exception:
            self._manifest = {}

    def _save_manifest(self) -> None:
        MANIFEST_PATH.write_text(json.dumps(self._manifest, indent=2), encoding="utf-8")

    def _reset_chroma_directory(self) -> None:
        if CHROMA_DIR.exists():
            shutil.rmtree(CHROMA_DIR)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)


service = RagService()
