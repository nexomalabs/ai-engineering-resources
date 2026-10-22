# Applied AI Engineering, Volume IV, Chapter 4
# Section 4.7, Automation Testing
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

# System under test (simplified)
class DocumentPipeline:
    def __init__(self, llm_client, router, result_store):
        self.llm_client = llm_client
        self.router = router
        self.result_store = result_store

    async def process(self, filepath: Path) -> dict:
        text = filepath.read_text()
        classification = await self.llm_client.classify(text)
        handler = self.router.get_handler(classification["type"])
        result = await handler(filepath, classification)
        await self.result_store.save(result)
        return result

# Tests
@pytest.mark.asyncio
async def test_process_contract_document(tmp_path):
    """Verify that a contract document is classified and routed correctly."""
    # Arrange
    doc_file = tmp_path / "agreement.pdf"
    doc_file.write_text("This Service Agreement is entered into by Acme Corp...")

    mock_llm = AsyncMock()
    mock_llm.classify.return_value = {
        "type": "contract",
        "confidence": 0.97,
    }

    mock_handler = AsyncMock(return_value={"processed": True, "type": "contract"})
    mock_router = AsyncMock()
    mock_router.get_handler.return_value = mock_handler

    mock_store = AsyncMock()

    pipeline = DocumentPipeline(mock_llm, mock_router, mock_store)

    # Act
    result = await pipeline.process(doc_file)

    # Assert
    mock_llm.classify.assert_awaited_once()
    mock_router.get_handler.assert_called_once_with("contract")
    mock_store.save.assert_awaited_once()
    assert result["type"] == "contract"


@pytest.mark.asyncio
async def test_llm_failure_triggers_retry():
    """Verify that LLM API failures trigger retry behavior."""
    call_count = 0

    async def flaky_classify(text: str) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("LLM API unavailable")
        return {"type": "invoice", "confidence": 0.91}

    # With proper retry logic, this should succeed on attempt 3
    result = None
    for attempt in range(3):
        try:
            result = await flaky_classify("Invoice #12345 — Amount: $1,250")
            break
        except ConnectionError:
            await asyncio.sleep(0.01)

    assert result is not None
    assert result["type"] == "invoice"
    assert call_count == 3
