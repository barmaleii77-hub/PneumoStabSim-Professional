import pytest

from src.security.access_control import (
    AccessControlService,
    AccessDeniedError,
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
