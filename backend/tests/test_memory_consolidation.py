"""Tests for Long-Term Memory Consolidation."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.memory.manager import memory_manager
from app.services.memory_consolidation import memory_consolidator


def test_memory_consolidator_service():
    """Verify extracting preferences and profile facts from message turns."""
    messages = [
        {"role": "user", "content": "Hello NEXUS, my role is Lead AI Systems Architect."},
        {"role": "assistant", "content": "Welcome! How can I assist you today?"},
        {"role": "user", "content": "I prefer dark charcoal interfaces with minimal accent colors."},
        {"role": "assistant", "content": "Acknowledged."},
        {"role": "user", "content": "Always use Windows PowerShell commands for setup."},
    ]

    result = memory_consolidator.extract_and_consolidate(
        conversation_id="conv-mem-test",
        messages=messages,
    )

    assert result["extracted_count"] >= 2
    keys = [m["key"] for m in result["memories"]]
    assert "operator_role" in keys or "preference" in keys or "operating_directive" in keys

    # Verify memory is queryable from memory_manager
    prefs = memory_manager.list_memories()
    assert any("charcoal" in m.content or "PowerShell" in m.content for m in prefs)


@pytest.mark.asyncio
async def test_memory_consolidate_api():
    """Verify the /api/v1/memory/consolidate endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "conversation_id": "conv-api-test",
            "messages": [
                {"role": "user", "content": "My stack is Python, FastAPI, and Next.js on Windows 11."},
            ],
        }
        res = await client.post("/api/v1/memory/consolidate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["conversation_id"] == "conv-api-test"
        assert data["extracted_count"] >= 1
