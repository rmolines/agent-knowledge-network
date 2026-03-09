"""Shared pytest fixtures and environment setup for all test suites."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Provide dummy env vars so pydantic-settings can instantiate Settings without
# a real .env file. Unit tests never reach the actual services.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/testdb")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

# Mock api.db before any test module imports it, so the engine is never
# instantiated (asyncpg may not be installed in the unit-test environment).
_mock_db = MagicMock()
_mock_db.get_db = AsyncMock()
sys.modules.setdefault("api.db", _mock_db)

# Mock qdrant_client so tests that import workers/indexer don't need the
# package installed. Unit tests exercise pure functions and never hit Qdrant.
sys.modules.setdefault("qdrant_client", MagicMock())
sys.modules.setdefault("qdrant_client.models", MagicMock())
