import io
import re
import hashlib
import logging
from contextlib import contextmanager
from typing import Dict, List, Iterator, Optional
import hashlib
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import ProgrammingError

from src.backend.config import settings

logger = logging.getLogger(__name__)

APP_DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:"
    f"{settings.postgres_password}"
    f"@{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

# Main app engine (privileged)
engine = create_engine(
    APP_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,  # Fail fast if pool exhausted
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={'connect_timeout': 10}
)

# Base agent engine for SET ROLE operations
agent_base_engine = create_engine(
    APP_DATABASE_URL,
    poolclass=NullPool,
    connect_args={'connect_timeout': 10}
)

# Strict identifier validation: lowercase, must start with letter
SAFE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")

# Reserved words to prevent conflicts
RESERVED_WORDS = {
    'public', 'user', 'role', 'table', 'schema', 'database',
    'current_user', 'session_user', 'none', 'default', 'all'
}

def validate_identifier(name: str, param_name: str) -> str:
    """
    Validate and normalize identifier for use in SQL.
    
    Returns lowercase normalized identifier.
    Raises ValueError if invalid.
    """
    if not name:
        raise ValueError(f"{param_name} cannot be empty")
    
    # Normalize to lowercase
    name_lower = name.lower()
    
    if name_lower in RESERVED_WORDS:
        raise ValueError(f"{param_name} '{name}' is a reserved word")
    
    if not SAFE_IDENTIFIER.match(name_lower):
        raise ValueError(
            f"Invalid {param_name}: '{name}'. "
            f"Must start with letter and contain only lowercase letters, numbers, and underscores"
        )
    
    if len(name_lower) > 63:
        raise ValueError(f"{param_name} too long (max 63 chars)")
    
    return name_lower

def get_thread_role_name(thread_id: str) -> str:
    """Generate the role name for a thread."""
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    return f"thread_{safe_thread_id}"


# ----------------------------
# Privileged raw connection (COPY)
# ----------------------------

@contextmanager
def get_conn():
    """
    App-level privileged raw connection.
    Used for COPY, etc.
    """
    conn = engine.raw_connection()
    try:
        yield conn
    finally:
        conn.close()

# ----------------------------
# Role existence checks
# ----------------------------

def role_exists(role_name: str, conn: Optional[Connection] = None) -> bool:
    """
    Check if a role exists in the database.
    
    Args:
        role_name: Role to check
        conn: Optional connection to use (for transactional consistency)
    """
    if conn is not None:
        result = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :role_name"),
            {"role_name": role_name}
        )
        return result.fetchone() is not None
    else:
        # Fallback for legacy callers without connection
        with engine.connect() as temp_conn:
            result = temp_conn.execute(
                text("SELECT 1 FROM pg_roles WHERE rolname = :role_name"),
                {"role_name": role_name}
            )
            return result.fetchone() is not None

def schema_exists(schema_name: str, conn: Connection) -> bool:
    """Check if a schema exists."""
    result = conn.execute(
        text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema_name"),
        {"schema_name": schema_name}
    )
    return result.fetchone() is not None

def ensure_thread_role_exists(thread_id: str) -> None:
    """
    Ensure thread role exists. If not, initialize it.
    This provides auto-migration for existing threads.
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    role_name = get_thread_role_name(thread_id)
    
    # Quick check without locking (optimization)
    if role_exists(role_name):
        return
    
    # Role doesn't exist, initialize the thread
    logger.warning(f"Thread role {role_name} doesn't exist. Auto-initializing thread {thread_id}")
    initialize_thread(thread_id)

# ----------------------------
# Thread initialization (ONE TIME per thread)
# ----------------------------
def initialize_thread(thread_id: str) -> None:
    """
    ONE-TIME setup for a new thread:
    1. Create the schema
    2. Create a dedicated role for this thread
    3. Grant the role READ-ONLY access to its schema
    
    This is called once when a thread is created and never needs to be repeated.
    Uses advisory lock to prevent race conditions during concurrent initialization.
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    role_name = get_thread_role_name(thread_id)
    
    # ✅ FIX A: stable advisory lock ID (process-independent)
    lock_id = int(
        hashlib.sha256(thread_id.encode("utf-8")).hexdigest()[:8],
        16
    )
    
    logger.info(f"Initializing thread {thread_id} with role {role_name}")
    
    with engine.begin() as conn:
        # Acquire advisory lock to prevent concurrent initialization
        conn.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": lock_id}
        )
        logger.debug(f"Acquired advisory lock {lock_id} for thread {thread_id}")
        
        # Create schema (idempotent)
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_thread_id}"'))
        logger.info(f"Schema {safe_thread_id} created/verified")
        
        # Check if role exists (within same transaction)
        if not role_exists(role_name, conn):
            # Create role
            conn.execute(text(f'CREATE ROLE "{role_name}" NOLOGIN'))
            logger.info(f"Role {role_name} created")
        else:
            logger.info(f"Role {role_name} already exists")
        
        # Grant usage on schema (idempotent)
        conn.execute(text(f'GRANT USAGE ON SCHEMA "{safe_thread_id}" TO "{role_name}"'))
        
        # Grant SELECT-ONLY privileges on all current tables (READ-ONLY ACCESS)
        conn.execute(text(
            f'GRANT SELECT ON ALL TABLES IN SCHEMA "{safe_thread_id}" TO "{role_name}"'
        ))

        # ✅ FIX B: default privileges explicitly tied to app DB owner
        conn.execute(text(
            f'''
            ALTER DEFAULT PRIVILEGES
            FOR ROLE "{settings.postgres_user}"
            IN SCHEMA "{safe_thread_id}"
            GRANT SELECT ON TABLES TO "{role_name}"
            '''
        ))
        
        # Grant usage on sequences (needed for serial columns, but still read-only)
        conn.execute(text(
            f'GRANT USAGE ON ALL SEQUENCES IN SCHEMA "{safe_thread_id}" TO "{role_name}"'
        ))

        # ✅ FIX B (sequences)
        conn.execute(text(
            f'''
            ALTER DEFAULT PRIVILEGES
            FOR ROLE "{settings.postgres_user}"
            IN SCHEMA "{safe_thread_id}"
            GRANT USAGE ON SEQUENCES TO "{role_name}"
            '''
        ))
        
        # Allow the main app user to SET ROLE to this thread role
        conn.execute(text(f'GRANT "{role_name}" TO "{settings.postgres_user}"'))
        logger.info(f"Granted {role_name} to {settings.postgres_user}")

def cleanup_thread(thread_id: str) -> None:
    """
    Clean up a thread's resources (optional, for thread deletion).
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    role_name = get_thread_role_name(thread_id)
    
    logger.info(f"Cleaning up thread {thread_id}")
    
    with engine.begin() as conn:
        # Drop schema and all contents
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{safe_thread_id}" CASCADE'))
        
        # Check if role exists before trying to revoke/drop
        if role_exists(role_name, conn):
            # Revoke the role from all users first
            conn.execute(text(f'REVOKE "{role_name}" FROM "{settings.postgres_user}"'))
            
            # Drop the role
            conn.execute(text(f'DROP ROLE "{role_name}"'))
            
    logger.info(f"Thread {thread_id} cleanup complete")

# ----------------------------
# Secure agent execution
# ----------------------------

@contextmanager
def get_thread_conn(thread_id: str) -> Iterator[Connection]:
    """
    Get a connection that operates as the thread's role.
    
    SECURITY MODEL:
    - Connection assumes the thread-specific role using SET ROLE
    - Role has READ-ONLY access (SELECT only)
    - PostgreSQL enforces all permission checks
    - No JIT grants/revokes needed
    - Multiple threads can run concurrently
    - Completely isolated by PostgreSQL's native permission system
    
    TRANSACTION MODEL:
    - Connection is provided inside an active transaction
    - Transaction commits automatically on success
    - Transaction rolls back automatically on exception
    - Since agents only read data, rollbacks have no effect on data integrity
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    role_name = get_thread_role_name(thread_id)
    
    # Ensure role exists (auto-migration)
    ensure_thread_role_exists(thread_id)
    
    logger.debug(f"Getting thread connection for {thread_id}, role: {role_name}")
    
    with agent_base_engine.connect() as conn:
        try:
            with conn.begin():
                # Assume the thread's role - THIS IS THE SECURITY BOUNDARY
                try:
                    conn.execute(text(f'SET ROLE "{role_name}"'))
                    logger.debug(f"Successfully set role to {role_name}")
                except ProgrammingError as e:
                    logger.error(f"Failed to SET ROLE {role_name}: {e}")
                    raise ValueError(f"Cannot assume role {role_name}. Thread may not be initialized.") from e
                
                # Set search path to ONLY the thread schema (no public fallback)
                # This prevents accidentally accessing shared tables
                conn.execute(text(f'SET search_path TO "{safe_thread_id}"'))
                
                # Prevent runaway queries
                conn.execute(text("SET statement_timeout = '10s'"))
                
                # Prevent memory exhaustion
                conn.execute(text("SET work_mem = '64MB'"))
                
                # Prevent idle connections
                conn.execute(text("SET idle_in_transaction_session_timeout = '30s'"))
                
                # Audit log the role assumption
                logger.info(
                    f"SECURITY_AUDIT: Thread {thread_id} connection established with role {role_name}"
                )
                
                yield conn
                
        except Exception as e:
            logger.error(f"Error in thread connection for {thread_id}: {e}", exc_info=True)
            raise
        finally:
            # Role automatically resets when connection closes
            logger.debug(f"Thread connection for {thread_id} closed")

# For backward compatibility with the old API
@contextmanager
def agent_execution(thread_id: str) -> Iterator[None]:
    """
    Legacy compatibility wrapper.
    With per-thread roles, this is just a no-op context manager.
    
    DEPRECATED: Use get_thread_conn() instead for actual database access.
    """
    validate_identifier(thread_id, "thread_id")
    # Ensure the thread is initialized
    ensure_thread_role_exists(thread_id)
    yield

# ----------------------------
# Legacy compatibility helpers
# ----------------------------

def ensure_schema(schema_name: str) -> None:
    """
    Ensure a schema exists.
    Note: For new code, use initialize_thread() instead.
    """
    safe_schema = validate_identifier(schema_name, "schema_name")
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'))

def grant_thread_access(thread_id: str, conn: Optional[Connection] = None) -> None:
    """
    Legacy no-op - access is now permanent via roles.
    """
    pass

def revoke_thread_access(thread_id: str, conn: Optional[Connection] = None) -> None:
    """
    Legacy no-op - access is now permanent via roles.
    """
    pass

@contextmanager
def global_agent_lock() -> Iterator[None]:
    """
    Legacy no-op - no longer needed with per-thread roles.
    """
    yield

# ----------------------------
# Data management
# ----------------------------

def create_table(schema_name: str, table_name: str, columns: Dict[str, str]) -> None:
    """
    Create a table in a schema.
    
    Args:
        schema_name: Schema name (typically thread_id)
        table_name: Table name
        columns: Dict mapping column names to PostgreSQL types
    """
    safe_schema = validate_identifier(schema_name, "schema_name")
    safe_table = validate_identifier(table_name, "table_name")
    
    # Validate column names
    validated_columns = {
        validate_identifier(col, "column_name"): dtype
        for col, dtype in columns.items()
    }
    
    cols = ", ".join([f'"{col}" {dtype}' for col, dtype in validated_columns.items()])
    sql = f'CREATE TABLE IF NOT EXISTS "{safe_schema}"."{safe_table}" ({cols})'
    
    with engine.begin() as conn:
        conn.execute(text(sql))
        logger.info(f"Table {safe_schema}.{safe_table} created")

def copy_dataframe(schema_name: str, table_name: str, df: pd.DataFrame) -> None:
    """
    Bulk insert DataFrame into table using PostgreSQL COPY.
    
    Security: Validates schema exists before writing.
    Uses privileged connection as COPY requires special permissions.
    
    Args:
        schema_name: Target schema (typically thread_id)
        table_name: Target table name
        df: DataFrame to insert
    """
    safe_schema = validate_identifier(schema_name, "schema_name")
    safe_table = validate_identifier(table_name, "table_name")
    
    # Verify schema exists (security check)
    with engine.connect() as conn:
        if not schema_exists(safe_schema, conn):
            raise ValueError(f"Schema {safe_schema} does not exist")
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.copy_expert(
                f'COPY "{safe_schema}"."{safe_table}" FROM STDIN WITH CSV',
                csv_buffer
            )
        conn.commit()
    
    logger.info(f"Copied {len(df)} rows to {safe_schema}.{safe_table}")

def register_data_source(thread_id: str, table_name: str, filename: str) -> int:
    """
    Register a data source in the global tracking table.
    
    Args:
        thread_id: Thread identifier
        table_name: Name of table
        filename: Original filename
        
    Returns:
        ID of created data source record
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    safe_table = validate_identifier(table_name, "table_name")

    sql = """
        INSERT INTO data_sources (thread_id, table_name, original_filename)
        VALUES (:thread_id, :table_name, :filename)
        RETURNING id
    """
    with engine.begin() as conn:
        res = conn.execute(text(sql), {
            "thread_id": safe_thread_id,
            "table_name": safe_table,
            "filename": filename
        })
        source_id = int(res.fetchone()[0])
    
    logger.info(f"Registered data source {source_id} for {safe_thread_id}.{safe_table}")
    return source_id

def list_thread_tables(thread_id: str) -> List[str]:
    """
    List all tables in a thread's schema.
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        List of table names
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    with engine.begin() as conn:
        res = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema_name
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """), {"schema_name": safe_thread_id})
        return [r[0] for r in res.fetchall()]

def get_table_info(thread_id: str, table_name: str) -> List[Dict[str, str]]:
    """
    Get column information for a table.
    
    Args:
        thread_id: Thread identifier
        table_name: Table name
        
    Returns:
        List of dicts with column info: {column, type, nullable}
    """
    safe_thread_id = validate_identifier(thread_id, "thread_id")
    safe_table = validate_identifier(table_name, "table_name")
    with engine.begin() as conn:
        res = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema_name
              AND table_name = :table_name
            ORDER BY ordinal_position
        """), {"schema_name": safe_thread_id, "table_name": safe_table})

        return [
            {"column": r[0], "type": r[1], "nullable": (r[2] == "YES")}
            for r in res.fetchall()
        ]

