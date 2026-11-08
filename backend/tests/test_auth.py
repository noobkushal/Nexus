"""Regression tests for authentication primitives and role policy."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import auth
from app.core.config import settings


def test_password_hash_round_trip_and_unique_salts():
    first = auth.hash_password("correct horse battery staple")
    second = auth.hash_password("correct horse battery staple")
    assert first != second
    assert auth.verify_password("correct horse battery staple", first)
    assert not auth.verify_password("wrong password", first)


def test_password_policy_rejects_short_passwords():
    with pytest.raises(ValueError, match="12 characters"):
        auth.hash_password("short")


def test_signed_token_round_trip(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "x" * 48)
    monkeypatch.setattr(settings, "ACCESS_TOKEN_TTL_MINUTES", 20)
    user = SimpleNamespace(id="owner-1", token_version=3)
    token = auth.create_access_token(user)
    claims = auth.decode_access_token(token)
    assert claims["sub"] == "owner-1"
    assert claims["ver"] == 3
    assert claims["iss"] == "nexus"


def test_token_tampering_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "x" * 48)
    token = auth.create_access_token(SimpleNamespace(id="owner-1", token_version=0))
    parts = token.split(".")
    parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
    with pytest.raises(HTTPException) as exc:
        auth.decode_access_token(".".join(parts))
    assert exc.value.status_code == 401


def test_missing_or_weak_signing_secret_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "weak")
    with pytest.raises(HTTPException) as exc:
        auth.create_access_token(SimpleNamespace(id="owner-1", token_version=0))
    assert exc.value.status_code == 503


def test_role_policy_denies_wrong_role():
    dependency = auth.require_roles("owner")
    with pytest.raises(HTTPException) as exc:
        dependency(SimpleNamespace(role="auditor"))
    assert exc.value.status_code == 403


def test_role_policy_accepts_owner():
    dependency = auth.require_roles("owner")
    assert dependency(SimpleNamespace(role="owner")).role == "owner"


def test_malformed_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "x" * 48)
    with pytest.raises(HTTPException) as exc:
        auth.decode_access_token("not-a-token")
    assert exc.value.status_code == 401


def test_expired_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "x" * 48)
    monkeypatch.setattr(settings, "ACCESS_TOKEN_TTL_MINUTES", 1)
    token = auth.create_access_token(SimpleNamespace(id="owner-1", token_version=0))
    monkeypatch.setattr(auth.time, "time", lambda: 4_000_000_000)
    with pytest.raises(HTTPException) as exc:
        auth.decode_access_token(token)
    assert exc.value.status_code == 401


def test_bootstrap_login_and_logout_revoke_session(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.api.auth import BootstrapRequest, LoginRequest, bootstrap_owner, login, logout
    from app.core.auth import get_current_user
    from app.db.session import Base
    from app.db import models  # noqa: F401

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "s" * 48)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_SECRET", "b" * 32)

    created = bootstrap_owner(BootstrapRequest(username="owner", password="a sufficiently long password"), "b" * 32, db)
    assert created["user"]["role"] == "owner"
    assert "password_hash" not in created["user"]

    signed_in = login(LoginRequest(username="owner", password="a sufficiently long password"), db)
    assert signed_in["access_token"]
    active_user = get_current_user("Bearer " + signed_in["access_token"], db)
    assert active_user.username == "owner"

    logout(active_user, db)
    with pytest.raises(HTTPException) as exc:
        get_current_user("Bearer " + signed_in["access_token"], db)
    assert exc.value.status_code == 401
    db.close()
    engine.dispose()


def test_bootstrap_rejects_wrong_secret(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.api.auth import BootstrapRequest, bootstrap_owner
    from app.db.session import Base
    from app.db import models  # noqa: F401

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "s" * 48)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_SECRET", "b" * 32)
    with pytest.raises(HTTPException) as exc:
        bootstrap_owner(BootstrapRequest(username="owner", password="a sufficiently long password"), "wrong", db)
    assert exc.value.status_code == 403
    assert db.query(__import__("app.db.models", fromlist=["UserModel"]).UserModel).count() == 0
    db.close()
    engine.dispose()
