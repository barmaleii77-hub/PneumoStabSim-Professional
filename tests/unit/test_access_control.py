import random

import pytest

from src.security.access_control import (
    AccessControlService,
    AccessDeniedError,
    _serialise_metadata,
    SecurityAuditLogger,
    UserRole,
)


def test_access_control_admin_allows_metadata(tmp_path) -> None:
    logger = SecurityAuditLogger(tmp_path / "audit.log")
    access_control = AccessControlService(audit_logger=logger)
    access_control.set_role(UserRole.ADMIN, actor="pytest")

    # Admin role should be able to update metadata without raising.
    access_control.require_permission("metadata", intent="set")


def test_access_control_guest_denies_simulation_write(tmp_path) -> None:
    logger = SecurityAuditLogger(tmp_path / "audit.log")
    access_control = AccessControlService(audit_logger=logger)
    access_control.set_role(UserRole.GUEST, actor="pytest")

    with pytest.raises(AccessDeniedError):
        access_control.require_permission("current.simulation", intent="set")

    assert logger.verify_chain()


def test_security_audit_logger_chain_integrity(tmp_path) -> None:
    logger = SecurityAuditLogger(tmp_path / "audit.log")
    digest_one = logger.record(
        "unit-test", "pytest", scope="demo", allowed=True, metadata={"step": 1}
    )
    digest_two = logger.record(
        "unit-test", "pytest", scope="demo", allowed=False, metadata={"step": 2}
    )

    assert digest_one != digest_two
    assert logger.verify_chain()


class _ShuffledSet(set[str]):
    """A set that iterates in a shuffled order on every iteration."""

    def __iter__(self):  # type: ignore[override]
        items = list(super().__iter__())
        random.shuffle(items)
        return iter(items)


def test_serialise_metadata_orders_unordered_iterables() -> None:
    random.seed(1)
    payload = {"flags": _ShuffledSet({"alpha", "beta", "gamma"})}

    converted = _serialise_metadata(payload)

    assert converted["flags"] == ["alpha", "beta", "gamma"]


def test_security_audit_logger_digest_is_deterministic_for_sets(tmp_path) -> None:
    logger = SecurityAuditLogger(tmp_path / "audit.log")

    payload = {
        "timestamp": "2025-01-01T00:00:00+00:00",
        "actor": "pytest",
        "action": "demo",
        "scope": "demo",
        "allowed": True,
        "metadata": {"flags": _ShuffledSet({"alpha", "beta", "gamma"})},
    }

    random.seed(2)
    digest_one = logger._digest("seed", payload)
    random.seed(42)
    digest_two = logger._digest("seed", payload)

    assert digest_one == digest_two
