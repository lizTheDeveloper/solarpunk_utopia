"""Tests for Fork Rights (GAP-65) - Data Export and Community Forking

Tests the Bakunin principle: Freedom includes freedom to exit.
"""
import pytest
import os
import sqlite3
from datetime import datetime, UTC

from app.services.fork_rights_service import ForkRightsService
from app.models.fork_rights import DataExportRequest, ConnectionExportConsent


@pytest.fixture
def db_path(tmp_path):
    """Create temporary database for testing."""
    db_file = tmp_path / "test_fork_rights.db"
    return str(db_file)


@pytest.fixture
def service(db_path):
    """Create fork rights service with test database."""
    return ForkRightsService(db_path)


@pytest.fixture
def setup_test_data(db_path):
    """Set up test data: users, offers, exchanges."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            bio TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS needs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchanges (
            id TEXT PRIMARY KEY,
            provider_id TEXT,
            receiver_id TEXT,
            completed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vouches (
            id TEXT PRIMARY KEY,
            voucher_id TEXT,
            vouchee_id TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cells (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_by TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cell_members (
            cell_id TEXT,
            user_id TEXT,
            role TEXT,
            joined_at TEXT,
            PRIMARY KEY (cell_id, user_id)
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO users VALUES
        ('maria-pk', 'Maria', 'Community organizer'),
        ('bob-pk', 'Bob', 'Gardener'),
        ('alice-pk', 'Alice', 'Baker')
    """)

    cursor.execute("""
        INSERT INTO offers VALUES
        ('offer-1', 'maria-pk', 'Teaching Spanish', 'I can teach Spanish'),
        ('offer-2', 'maria-pk', 'Sourdough starter', 'Extra starter available')
    """)

    cursor.execute("""
        INSERT INTO exchanges VALUES
        ('exchange-1', 'maria-pk', 'bob-pk', '2025-12-19T00:00:00Z')
    """)

    cursor.execute("""
        INSERT INTO vouches VALUES
        ('vouch-1', 'maria-pk', 'bob-pk')
    """)

    cursor.execute("""
        INSERT INTO cells VALUES
        ('cell-main', 'Main Community', 'genesis-steward', '2025-01-01T00:00:00Z')
    """)

    cursor.execute("""
        INSERT INTO cell_members VALUES
        ('cell-main', 'maria-pk', 'member', '2025-01-01T00:00:00Z'),
        ('cell-main', 'bob-pk', 'member', '2025-01-01T00:00:00Z'),
        ('cell-main', 'alice-pk', 'steward', '2025-01-01T00:00:00Z')
    """)

    conn.commit()
    conn.close()


# Data Export Tests

def test_request_data_export(service):
    """Test requesting a data export."""
    request = service.request_data_export(
        user_id="maria-pk",
        export_type="data_only"
    )

    assert request.user_id == "maria-pk"
    assert request.export_type == "data_only"
    assert request.status == "pending"


def test_export_user_data(service, setup_test_data):
    """Test exporting user's data."""
    export = service.export_user_data("maria-pk")

    assert export.user_id == "maria-pk"
    assert export.my_profile["name"] == "Maria"
    assert len(export.my_offers) == 2
    assert len(export.my_exchanges) == 1
    assert len(export.my_vouches_given) == 1


def test_export_respects_privacy(service, setup_test_data):
    """Test that export doesn't include other people's data."""
    export = service.export_user_data("maria-pk")

    # Should NOT include Bob's or Alice's offers
    for offer in export.my_offers:
        assert offer["user_id"] == "maria-pk"

    # Connections should be empty (no consent given)
    assert len(export.my_connections) == 0


# Connection Consent Tests

def test_connection_consent_request(service):
    """Test requesting connection export consent."""
    consent = ConnectionExportConsent(
        id="consent-1",
        requester_id="maria-pk",
        connection_id="bob-pk",
        asked_at=datetime.now(UTC),
        expires_at=datetime.now(UTC)
    )

    result = service.repo.create_consent_request(consent)
    assert result.requester_id == "maria-pk"
    assert result.connection_id == "bob-pk"


def test_respond_to_consent(service):
    """Test responding to consent request."""
    # Create consent request
    consent = ConnectionExportConsent(
        id="consent-1",
        requester_id="maria-pk",
        connection_id="bob-pk",
        asked_at=datetime.now(UTC),
        expires_at=datetime.now(UTC)
    )
    service.repo.create_consent_request(consent)

    # Respond
    service.respond_to_connection_consent("consent-1", "allow")

    # Check response recorded
    pending = service.get_pending_consents("bob-pk")
    assert len(pending) == 0  # No longer pending


# Community Forking Tests

def test_fork_community(service, setup_test_data):
    """Test forking a community."""
    fork = service.fork_community(
        user_id="maria-pk",
        original_cell_id="cell-main",
        new_cell_name="Autonomous Collective",
        fork_reason="Governance disagreement",
        members_to_invite=["bob-pk"]
    )

    assert fork.original_cell_id == "cell-main"
    assert fork.forked_by == "maria-pk"
    assert "bob-pk" in fork.members_invited

    # Check new cell was created
    conn = sqlite3.connect(service.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cells WHERE id = ?", (fork.new_cell_id,))
    new_cell = cursor.fetchone()
    conn.close()

    assert new_cell is not None


def test_leave_community(service, setup_test_data):
    """Test leaving a community."""
    # Leave
    service.leave_community(
        user_id="maria-pk",
        cell_id="cell-main"
    )

    # Check membership removed
    conn = sqlite3.connect(service.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM cell_members
        WHERE cell_id = 'cell-main' AND user_id = 'maria-pk'
    """)
    membership = cursor.fetchone()
    conn.close()

    assert membership is None  # No longer a member


def test_no_exit_surveillance(service, setup_test_data):
    """Test that exit doesn't create excessive tracking."""
    service.leave_community(
        user_id="maria-pk",
        cell_id="cell-main"
    )

    # Exit record should be minimal - just that it happened
    conn = sqlite3.connect(service.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM exit_records
        WHERE user_id = 'maria-pk' AND cell_id = 'cell-main'
    """)
    exit_record = cursor.fetchone()
    conn.close()

    # Should only have: user_id, cell_id, left_at
    # NO "why", NO "exit count", NO "departure risk"
    assert exit_record is not None
    assert len(exit_record) == 3  # Just the essential fields


# Privacy Tests

def test_no_connection_export_without_consent(service, setup_test_data):
    """Test that connections aren't exported without consent."""
    export = service.export_user_data("maria-pk")

    # Maria exchanged with Bob, but no consent given
    assert len(export.my_connections) == 0


def test_connection_export_with_consent(service, setup_test_data):
    """Test that connections ARE exported with consent."""
    # Create and approve consent
    consent = ConnectionExportConsent(
        id="consent-1",
        requester_id="maria-pk",
        connection_id="bob-pk",
        asked_at=datetime.now(UTC),
        expires_at=datetime.now(UTC)
    )
    service.repo.create_consent_request(consent)
    service.respond_to_connection_consent("consent-1", "allow")

    # Now export
    export = service.export_user_data("maria-pk")

    # Bob's info should be included (he consented)
    assert len(export.my_connections) == 1
    assert export.my_connections[0]["id"] == "bob-pk"


# Architecture Constraints Tests

def test_local_first_export(service, setup_test_data):
    """Test that export creates local file, not cloud upload."""
    export_path = service.generate_export_file("maria-pk")

    # Should be local path (data/exports/...)
    assert export_path.startswith("data/exports/")

    # Should NOT be:
    # - s3:// URL
    # - http:// URL
    # - Any cloud storage path

    # Should be SQLite database
    assert export_path.endswith(".db")


def test_export_works_offline(service, setup_test_data):
    """Test that export doesn't require internet."""
    # This entire test works without network - that's the point!
    export = service.export_user_data("maria-pk")

    # All data retrieved from local SQLite
    # No API calls, no cloud fetches
    assert export.my_profile is not None
    assert len(export.my_offers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
