"""Shared synchronous MongoDB helper utilities.

The application uses the singleton in `app.core.database` for the actual
connection lifecycle. This module provides a thin service layer on top of that
singleton so routes and future services can work with collections in a
consistent way.
"""

from contextlib import contextmanager
from typing import Generator, Optional

from app.core.database import db_instance


class MongoDBService:
    """Convenience wrapper around the shared synchronous MongoDB connection."""

    def __init__(self, database=None):
        self._db_instance = db_instance
        self._override_db = database

    @property
    def db(self):
        """Return the active MongoDB database object."""
        if self._override_db is not None:
            return self._override_db
        return self._db_instance.db

    def ensure_connected(self):
        """Ensure the underlying database connection is ready."""
        if self._override_db is None:
            self._db_instance.ensure_connected()
        return self.db

    def get_collection(self, collection_name: str):
        """Return a collection by name."""
        return self.ensure_connected()[collection_name]

    def ping(self) -> bool:
        """Ping MongoDB to verify connectivity."""
        self.ensure_connected().command("ping")
        return True

    def close(self) -> None:
        """Close the shared database connection."""
        if self._override_db is None:
            self._db_instance.close_connection()

    @contextmanager
    def collection(self, collection_name: str) -> Generator:
        """Context manager yielding a collection handle.

        This keeps the calling style simple while still centralizing the
        database access point.
        """
        yield self.get_collection(collection_name)


mongo_db_service = MongoDBService()
