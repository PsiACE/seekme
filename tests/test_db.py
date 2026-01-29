"""Integration tests for SQL database layer."""

from __future__ import annotations

from seekme import Client


def _prepare_table(client: Client) -> None:
    assert client.db is not None
    client.db.execute("DELETE FROM seekme_items")
    client.db.commit()


def test_execute_and_fetch(client: Client, table_cleanup: list[str]) -> None:
    assert client.db is not None
    client.db.execute(
        """
        CREATE TABLE IF NOT EXISTS seekme_items (
            id INT PRIMARY KEY,
            name VARCHAR(128)
        )
        """
    )
    client.db.commit()
    table_cleanup.append("seekme_items")
    _prepare_table(client)
    assert client.db is not None

    client.db.execute(
        "INSERT INTO seekme_items (id, name) VALUES (:id, :name)",
        {"id": 1, "name": "alpha"},
    )

    row = client.db.fetch_one(
        "SELECT id, name FROM seekme_items WHERE id = :id",
        {"id": 1},
    )

    assert row == {"id": 1, "name": "alpha"}


def test_transaction_commit_and_rollback(client: Client, table_cleanup: list[str]) -> None:
    assert client.db is not None
    client.db.execute(
        """
        CREATE TABLE IF NOT EXISTS seekme_items (
            id INT PRIMARY KEY,
            name VARCHAR(128)
        )
        """
    )
    client.db.commit()
    table_cleanup.append("seekme_items")
    _prepare_table(client)
    assert client.db is not None

    client.db.begin()
    client.db.execute(
        "INSERT INTO seekme_items (id, name) VALUES (:id, :name)",
        {"id": 2, "name": "beta"},
    )
    client.db.rollback()

    rows = client.db.fetch_all("SELECT id, name FROM seekme_items WHERE id = :id", {"id": 2})
    assert rows == []

    client.db.begin()
    client.db.execute(
        "INSERT INTO seekme_items (id, name) VALUES (:id, :name)",
        {"id": 3, "name": "gamma"},
    )
    client.db.commit()

    row = client.db.fetch_one(
        "SELECT id, name FROM seekme_items WHERE id = :id",
        {"id": 3},
    )

    assert row == {"id": 3, "name": "gamma"}


def _ensure_table(client: Client) -> None:
    assert client.db is not None
    client.db.execute("DELETE FROM seekme_people")
    client.db.commit()


def test_insert_select_update_delete(client: Client, table_cleanup: list[str]) -> None:
    assert client.db is not None
    client.db.execute(
        """
        CREATE TABLE IF NOT EXISTS seekme_people (
            id INT PRIMARY KEY,
            name VARCHAR(64),
            score INT
        )
        """
    )
    client.db.commit()
    table_cleanup.append("seekme_people")
    _ensure_table(client)
    assert client.db is not None

    client.db.begin()
    client.db.execute(
        "INSERT INTO seekme_people (id, name, score) VALUES (:id, :name, :score)",
        {"id": 1, "name": "alice", "score": 90},
    )
    client.db.execute(
        "INSERT INTO seekme_people (id, name, score) VALUES (:id, :name, :score)",
        {"id": 2, "name": "bob", "score": 80},
    )
    client.db.commit()

    rows = client.db.fetch_all("SELECT id, name, score FROM seekme_people ORDER BY id")
    assert rows == [
        {"id": 1, "name": "alice", "score": 90},
        {"id": 2, "name": "bob", "score": 80},
    ]

    client.db.begin()
    client.db.execute("UPDATE seekme_people SET score = :score WHERE id = :id", {"id": 2, "score": 85})
    client.db.commit()

    row = client.db.fetch_one("SELECT id, name, score FROM seekme_people WHERE id = :id", {"id": 2})
    assert row == {"id": 2, "name": "bob", "score": 85}

    client.db.begin()
    client.db.execute("DELETE FROM seekme_people WHERE id = :id", {"id": 1})
    client.db.commit()

    rows = client.db.fetch_all("SELECT id FROM seekme_people ORDER BY id")
    assert rows == [{"id": 2}]

