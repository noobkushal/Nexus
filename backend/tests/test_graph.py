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
    assert "dossier_path" in state.metadata
    assert any("Scout Archive" in s for s in state.steps)


@pytest.mark.asyncio
async def test_graph_forge_scaffold_project():
    state = await agent_graph.execute(
        user_prompt="Please scaffold a new project and template for my microservice code",
        conversation_id="test-conv-scaffold",
    )
    assert state.intent == "coding"
    assert state.target_agent_id == "coding_agent"
    assert "scaffolded_project" in state.metadata
    assert any("Forge Scaffolder" in s for s in state.steps)


@pytest.mark.asyncio
async def test_graph_apex_tailor_resume():
    state = await agent_graph.execute(
        user_prompt="Please tailor my resume and cv for a Senior Architect job",
        conversation_id="test-conv-tailor",
    )
    assert state.intent == "career"
    assert state.target_agent_id == "career_agent"
    assert "tailored_resume_path" in state.metadata
    assert any("Apex Career" in s for s in state.steps)


@pytest.mark.asyncio
async def test_graph_consequential_action_intercept(test_database):
    factory, owner = test_database
    db = factory()
    state = await agent_graph.execute(
        user_prompt="Please delete all files in the old storage directory",
        conversation_id="test-conv-3",
        owner_user_id=owner.id,
        db=db,
    )
    db.close()
    assert state.requires_approval is True
    assert state.approval_id is not None
    assert "SAFETY BARRIER INTERCEPT" in state.response_content
    assert state.claimed_actions_executed is False
