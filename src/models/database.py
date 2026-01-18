"""Database connection and Peewee models for anime1-desktop."""
import logging
import time
from pathlib import Path
from typing import Optional

from peewee import (
    SqliteDatabase,
    Model,
    TextField,
    IntegerField,
    TimestampField,
    BooleanField,
)

from src.utils.app_dir import ensure_app_data_dir

logger = logging.getLogger(__name__)

# Database file name
DB_FILE_NAME = "anime1.db"

# Global database instance
_db: Optional[SqliteDatabase] = None

# 是否已安装查询追踪
_query_tracing_installed = False


def install_query_tracing():
    """安装数据库查询自动追踪 (只执行一次)"""
    global _query_tracing_installed
    if _query_tracing_installed:
        return

    try:
        from src.utils.trace import TraceSpan, is_tracing_enabled

        db = get_database()

        # 保存原始 execute_sql 方法
        original_execute = db.execute_sql

        def traced_execute(sql, params=None, require_commit=True):
            """包装后的 execute_sql，自动追踪所有查询"""
            if not is_tracing_enabled():
                return original_execute(sql, params, require_commit)

            start_time = time.time()
            try:
                result = original_execute(sql, params, require_commit)
                elapsed = (time.time() - start_time) * 1000

                # 从 SQL 提取表名作为追踪名称
                sql_upper = sql.upper().strip()
                table_name = "db_query"
                if sql_upper.startswith("SELECT"):
                    table_name = "db_select"
                elif sql_upper.startswith("INSERT"):
                    table_name = "db_insert"
                elif sql_upper.startswith("UPDATE"):
                    table_name = "db_update"
                elif sql_upper.startswith("DELETE"):
                    table_name = "db_delete"

                # 尝试提取表名
                import re
                match = re.search(r'FROM\s+["`]?(\w+)', sql_upper)
                if match:
                    table_name = f"db:{match.group(1)}"

                # 记录查询
                with TraceSpan(table_name, 'db_query', {
                    'sql': sql[:200],  # 限制 SQL 长度
                    'params': str(params)[:100] if params else None
                }) as span:
                    span.end(success=True)

                # 慢查询警告 (>100ms)
                if elapsed > 100:
                    logger.debug(f"SLOW QUERY ({elapsed:.2f}ms): {sql[:100]}")

                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.debug(f"DB ERROR ({elapsed:.2f}ms): {sql[:100]} - {e}")
                raise

        # 替换 execute_sql 方法
        db.execute_sql = traced_execute
        _query_tracing_installed = True
        logger.info("Database query tracing installed")

    except Exception as e:
        logger.warning(f"Failed to install query tracing: {e}")


def get_database_path() -> Path:
    """Get the path to the database file."""
    app_dir = ensure_app_data_dir()
    return app_dir / DB_FILE_NAME


def get_database() -> SqliteDatabase:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        db_path = get_database_path()
        _db = SqliteDatabase(str(db_path), pragmas={
            "journal_mode": "wal",
            "cache_size": -64000,  # 64MB cache
            "foreign_keys": 1,
        })
        logger.info(f"Database initialized at: {db_path}")
    return _db


def close_database():
    """Close the database connection."""
    global _db
    if _db is not None:
        _db.close()
        _db = None
        logger.info("Database connection closed")


class BaseModel(Model):
    """Base model class with common functionality."""

    class Meta:
        database = get_database()


def init_database():
    """Initialize the database and create tables if they don't exist.

    This function:
    1. Creates the database connection
    2. Creates all tables if they don't exist
    3. Runs any pending migrations
    """
    db = get_database()
    db.connect()

    # 安装数据库查询追踪
    install_query_tracing()

    # Import models to register them
    from src.models.favorite import FavoriteAnime
    from src.models.cover_cache import CoverCache
    from src.models.playback_history import PlaybackHistory
    from src.models.performance_trace import PerformanceTrace, PerformanceStat

    # Create tables
    db.create_tables([
        FavoriteAnime,
        CoverCache,
        PlaybackHistory,
        PerformanceTrace,
        PerformanceStat,
    ])

    # Run migrations
    from src.models.migration import run_migrations
    run_migrations()

    logger.info("Database initialized successfully")
