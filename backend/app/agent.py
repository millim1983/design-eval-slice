from __future__ import annotations
"""LangChain agent utilities for question routing and retries."""

import os
from typing import Callable

from langchain.agents import AgentExecutor, AgentType, Tool, initialize_agent
from langchain_community.llms import Ollama
from langchain.schema import OutputParserException
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.rag import RagService


def _rag_tool_factory(rag: RagService) -> Callable[[str], str]:
    """Create a tool function querying the ``RagService``."""

    def _rag_query(question: str) -> str:
        result = rag.query(question)
        return result["answer"]

    return _rag_query


def build_agent(rag: RagService) -> AgentExecutor:
    """Return an agent with RAG and free-form chat tools."""
    llm = Ollama(base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"), model="llama2")
    tools = [
        Tool(
            name="rag_search",
            func=_rag_tool_factory(rag),
            description=(
                "Search expert and evaluation documents to answer domain questions."
            ),
        ),
        Tool(
            name="free_chat",
            func=llm.invoke,
            description="General chat without document lookup.",
        ),
    ]
    return initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, handle_parsing_errors=True)


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(OutputParserException),
)
def run_agent(agent: AgentExecutor, question: str) -> str:
    """Execute ``agent`` with retries and light post-processing."""
    output = agent.run(question)
    return output.strip()
