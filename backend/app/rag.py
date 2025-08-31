from __future__ import annotations
"""RAG indexing utilities using LlamaIndex.

This module fetches expert guide documents and evaluation interpretation
texts from external databases and builds vector indexes for retrieval.
"""

from typing import Any, List
import os
import httpx
from llama_index.core import Document, VectorStoreIndex


async def fetch_documents(url: str) -> List[Document]:
    """Fetch documents from an external REST endpoint.

    The endpoint is expected to return JSON list of objects with
    ``id`` and ``text`` fields. This structure keeps the function generic so
    different databases can expose a compatible API.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30.0)
        resp.raise_for_status()
        items: List[dict[str, Any]] = resp.json()
    docs: List[Document] = []
    for i, item in enumerate(items):
        text = item.get("text", "")
        doc_id = str(item.get("id", i))
        docs.append(Document(text=text, doc_id=doc_id))
    return docs


class RagService:
    """Manage LlamaIndex vector indexes for RAG queries."""

    def __init__(self, expert_url: str, evaluation_url: str) -> None:
        self.expert_url = expert_url
        self.evaluation_url = evaluation_url
        self._expert_index: VectorStoreIndex | None = None
        self._evaluation_index: VectorStoreIndex | None = None

    async def refresh(self) -> None:
        """(Re)build indexes by fetching latest documents."""
        self._expert_index = await self._build_index(self.expert_url)
        self._evaluation_index = await self._build_index(self.evaluation_url)

    async def _build_index(self, url: str) -> VectorStoreIndex:
        docs = await fetch_documents(url)
        return VectorStoreIndex.from_documents(docs)

    def query(self, question: str) -> dict[str, Any]:
        """Query both indexes and aggregate answers."""
        if not self._expert_index or not self._evaluation_index:
            raise RuntimeError("Indexes not initialized")
        expert_res = self._expert_index.as_query_engine().query(question)
        eval_res = self._evaluation_index.as_query_engine().query(question)
        sources = []
        for res in (expert_res, eval_res):
            for sn in getattr(res, "source_nodes", []) or []:
                sources.append({
                    "doc_id": sn.node.doc_id,
                    "text": sn.node.get_content(),
                })
        answer = "\n".join([
            getattr(expert_res, "response", str(expert_res)),
            getattr(eval_res, "response", str(eval_res)),
        ])
        return {"answer": answer.strip(), "sources": sources}
