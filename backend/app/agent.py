from __future__ import annotations
"""LangChain agent utilities for question routing and retries."""

from typing import Callable

from langchain.agents import AgentExecutor, AgentType, Tool, initialize_agent
from langchain_community.llms import Ollama
from langchain.output_parsers import PydanticOutputParser
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from pydantic import ValidationError

from app.rag import RagService
from app.schemas import AgentAnswer
from app.core.config import ModelsConfig, load_config


def _rag_tool_factory(rag: RagService) -> Callable[[str], str]:
    """Create a tool function querying the ``RagService``."""

    def _rag_query(question: str) -> str:
        result = rag.query(question)
        return result["answer"]

    return _rag_query


def build_agent(rag: RagService, models: ModelsConfig | None = None) -> AgentExecutor:
    """Return an agent with RAG and free-form chat tools.

    Parameters
    ----------
    rag:
        Service used for retrieval-augmented generation.
    models:
        Model configuration loaded from ``models.yaml``. If ``None`` the
        configuration is loaded on demand.
    """
    if models is None:
        models = load_config().models
    llm = Ollama(base_url=models.base_url, model=models.model)
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


parser = PydanticOutputParser(pydantic_object=AgentAnswer)
FORMAT_INSTRUCTIONS = parser.get_format_instructions()


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(ValidationError),
)
def run_agent(agent: AgentExecutor, question: str) -> AgentAnswer:
    """Execute ``agent`` with structured output parsing and retries."""
    prompt = f"{question}\n{FORMAT_INSTRUCTIONS}"
    output = agent.run(prompt)
    return parser.parse(output)
