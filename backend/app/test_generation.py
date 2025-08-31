import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from langchain.output_parsers import PydanticOutputParser

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.providers import Provider, generate_structured  # noqa:E402
from app.schemas import LLMChatResponse  # noqa:E402


class FakeProvider(Provider):
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0

    async def generate(self, prompt: str, model: str, **kwargs):
        out = self.outputs[self.calls]
        self.calls += 1
        return {"response": out}


@pytest.mark.asyncio
async def test_generate_structured_valid():
    provider = FakeProvider(['{"answer": "hi", "citations": []}'])
    parser = PydanticOutputParser(pydantic_object=LLMChatResponse)
    result, raw = await generate_structured(provider, "q", "m", parser)
    assert result.answer == "hi"
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_generate_structured_invalid():
    provider = FakeProvider(['oops', 'bad', 'still'])
    parser = PydanticOutputParser(pydantic_object=LLMChatResponse)
    with pytest.raises(ValidationError):
        await generate_structured(provider, "q", "m", parser)
    assert provider.calls == 3


@pytest.mark.asyncio
async def test_generate_structured_retry_success():
    provider = FakeProvider(['oops', '{"answer": "ok", "citations": []}'])
    parser = PydanticOutputParser(pydantic_object=LLMChatResponse)
    result, raw = await generate_structured(provider, "q", "m", parser)
    assert result.answer == "ok"
    assert provider.calls == 2
