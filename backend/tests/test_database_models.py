"""Tests for SQLAlchemy Relational Database Models & Persistence."""
import uuid
import pytest
from app.db.models import (
    AgentActivityModel,
    AgentModel,
    ConversationModel,
    IntegrationSettingModel,
    MemoryRecordModel,
    MessageModel,
    TaskModel,
    UserModel,
)
from app.db.session import Base, SessionLocal, engine, init_db


@pytest.fixture(scope="module")
def db_session():
    """Sets up an in-memory/test database session."""
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_user_model_persistence(db_session):
    """Verify creating and retrieving user accounts."""
    uid = f"usr-{uuid.uuid4().hex[:6]}"
    user = UserModel(id=uid, username=f"operator_{uid}", email=f"{uid}@nexus.local", role="admin")
    db_session.add(user)
    db_session.commit()

    fetched = db_session.query(UserModel).filter_by(id=uid).first()
    assert fetched is not None
    assert fetched.username == f"operator_{uid}"
    assert fetched.role == "admin"


def test_conversation_and_messages_relationship(db_session):
    """Verify multi-turn message cascade within conversation sessions."""
    cid = f"conv-{uuid.uuid4().hex[:6]}"
    conv = ConversationModel(id=cid, title="System Architecture Session")
    db_session.add(conv)
    db_session.commit()

    msg1 = MessageModel(
        id=f"msg-{uuid.uuid4().hex[:6]}",
        conversation_id=cid,
        role="user",
        content="How do we enforce sandboxed security?",
        intent="coding",
    )
    msg2 = MessageModel(
        id=f"msg-{uuid.uuid4().hex[:6]}",
        conversation_id=cid,
        role="assistant",
        content="Filesystem access is restricted to approved roots.",
        intent="coding",
    )
    db_session.add_all([msg1, msg2])
    db_session.commit()

    loaded_conv = db_session.query(ConversationModel).filter_by(id=cid).first()
    assert loaded_conv is not None
    assert len(loaded_conv.messages) == 2
    assert loaded_conv.messages[0].role == "user"
    assert loaded_conv.messages[1].role == "assistant"


def test_task_model_persistence(db_session):
    """Verify task model creation and lifecycle states."""
    tid = f"task-{uuid.uuid4().hex[:6]}"
    task = TaskModel(
        id=tid,
        title="Deploy PostgreSQL with pgvector",
        description="Verify Docker compose container",
        status="pending",
        priority="high",
        assigned_agent="workflow_agent",
    )
    db_session.add(task)
    db_session.commit()

    loaded_task = db_session.query(TaskModel).filter_by(id=tid).first()
    assert loaded_task is not None
    assert loaded_task.priority == "high"

    # Update status
    loaded_task.status = "completed"
    db_session.commit()

    refetched = db_session.query(TaskModel).filter_by(id=tid).first()
    assert refetched.status == "completed"


def test_memory_and_settings_persistence(db_session):
    """Verify long-term memory and integration settings models."""
    mid = f"mem-{uuid.uuid4().hex[:6]}"
    mem = MemoryRecordModel(
        id=mid,
        category="preferences",
        key="theme_dark",
        content="Preferred charcoal UI mode",
        importance=3,
    )
    setting_key = f"n8n_poll_interval_{uuid.uuid4().hex[:6]}"
    setting = IntegrationSettingModel(
        id=f"set-{uuid.uuid4().hex[:6]}",
        key=setting_key,
        value_json='{"seconds": 30}',
        is_secret=False,
    )
    db_session.add_all([mem, setting])
    db_session.commit()

    loaded_mem = db_session.query(MemoryRecordModel).filter_by(id=mid).first()
    assert loaded_mem is not None
    assert loaded_mem.key == "theme_dark"

    loaded_setting = db_session.query(IntegrationSettingModel).filter_by(key=setting_key).first()
    assert loaded_setting is not None
    assert "30" in loaded_setting.value_json
