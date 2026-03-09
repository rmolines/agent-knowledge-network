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

# Mock arq so tests that import api.deps or api.main don't need the package
# installed. Unit tests mock the ARQ pool via dependency overrides.
_mock_arq = MagicMock()
_mock_arq.ArqRedis = MagicMock
_mock_arq.create_pool = AsyncMock(return_value=MagicMock())
sys.modules.setdefault("arq", _mock_arq)
sys.modules.setdefault("arq.connections", MagicMock())

# Mock redis so tests that import api.main (which loads auth router → redis service)
# don't need the package installed. Unit tests never reach real Redis.
_mock_redis_asyncio = MagicMock()
_mock_redis = MagicMock()
_mock_redis.asyncio = _mock_redis_asyncio
sys.modules.setdefault("redis", _mock_redis)
sys.modules.setdefault("redis.asyncio", _mock_redis_asyncio)
