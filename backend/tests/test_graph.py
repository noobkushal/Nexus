"""Test Multi-Agent State Graph Execution."""
import pytest
from app.agents.graph import agent_graph


@pytest.mark.asyncio
async def test_graph_intent_routing_coding():
    state = await agent_graph.execute(
        user_prompt="Can you check the git commit and fix a bug in the code?",
        conversation_id="test-conv-1",
    )
    assert state.intent == "coding"
    assert state.target_agent_id == "coding_agent"
    assert len(state.steps) >= 3
    assert any("coding_agent" in s for s in state.steps)


@pytest.mark.asyncio
async def test_graph_intent_routing_research():
    state = await agent_graph.execute(
        user_prompt="Please research and search the web for latest AI papers",
        conversation_id="test-conv-2",
    )
    assert state.intent == "research"
    assert state.target_agent_id == "research_agent"


@pytest.mark.asyncio
async def test_graph_consequential_action_intercept():
    state = await agent_graph.execute(
        user_prompt="Please delete all files in the old storage directory",
        conversation_id="test-conv-3",
    )
    assert state.requires_approval is True
    assert state.approval_id is not None
    assert "SAFETY BARRIER INTERCEPT" in state.response_content
    assert state.claimed_actions_executed is False
