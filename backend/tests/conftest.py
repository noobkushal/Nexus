"""Shared isolated database and authenticated owner for API tests."""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import get_current_user
from app.db.models import UserModel
from app.db.session import Base, get_db
from app.db import models  # noqa: F401
from app.main import app


@pytest.fixture
def test_database():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup_db = factory()
    owner = UserModel(
        id=str(uuid.uuid4()),
        username="test-owner",
        role="owner",
        is_active=True,
        token_version=0,
    )
    setup_db.add(owner)
    setup_db.commit()
    setup_db.close()

    def override_get_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    def override_current_user():
        return owner

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    yield factory, owner
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture(autouse=True)
def install_authenticated_test_context(test_database):
    """All API tests run with a temporary owner and isolated database."""
    yield
