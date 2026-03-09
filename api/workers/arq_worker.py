"""
ARQ worker settings — background job processing.

Run with: arq api.workers.arq_worker.WorkerSettings

Jobs registered here run in a separate process. Each job must be an async
function importable from this module or from imported modules.
"""

from arq.connections import RedisSettings

from api.config import settings
from api.workers.indexer import index_post  # noqa: F401  — registered as ARQ job

__all__ = ["WorkerSettings"]


class WorkerSettings:
    """ARQ worker configuration. Pass to `arq` CLI as the settings class."""

    functions = [index_post]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
