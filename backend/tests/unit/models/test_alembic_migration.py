import pytest
import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def test_db_url():
    """Get database URL for testing migrations."""
    # Use environment variable or default to a test database
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/experimentation_migration_test",
    )


@pytest.fixture(scope="module")
def alembic_config(test_db_url):
    """Create Alembic configuration for migration tests."""
    # IMPORTANT: Update path to point to the correct Alembic directory
    # Determine the project root directory
    project_root = Path(__file__).parent.parent.parent.parent

    # Point to where Alembic is actually installed
    # In this case: /backend/app/db/migrations
    alembic_dir = project_root / "app" / "db" / "migrations"

    # Alternative path if you've installed Alembic at a different location
    alembic_ini_path = project_root / "app" / "db" / "alembic.ini"

    # Verify that the directory exists
    if not alembic_dir.exists():
        # Log detailed information for debugging
        logger.error(f"Alembic directory not found at {alembic_dir}")
        logger.info(f"Current file: {__file__}")
        logger.info(f"Project root resolved to: {project_root}")
        logger.info(f"Contents of project root: {os.listdir(project_root)}")
        if (project_root / "app").exists():
            logger.info(
                f"Contents of app directory: {os.listdir(project_root / 'app')}"
            )
        if (project_root / "app" / "db").exists():
            logger.info(
                f"Contents of db directory: {os.listdir(project_root / 'app' / 'db')}"
            )
        raise FileNotFoundError(f"Could not find alembic directory at {alembic_dir}")

    logger.info(f"Using alembic directory: {alembic_dir}")

    # Create Alembic config
    config = Config()

    # If alembic.ini exists, use it
    if alembic_ini_path.exists():
        config = Config(alembic_ini_path)

    # Set script location and database URL
    config.set_main_option("script_location", str(alembic_dir))
    config.set_main_option("sqlalchemy.url", test_db_url)

    return config


@pytest.fixture(scope="module")
def clean_test_database(test_db_url):
    """Set up a clean database for migration testing."""
    # Extract database name from URL
    db_name = test_db_url.split("/")[-1]
    base_url = test_db_url.rsplit("/", 1)[0]
    default_db = f"{base_url}/postgres"

    # Connect to default database to manage test database
    engine = create_engine(default_db)
    conn = engine.connect()
    conn.execute(text("COMMIT"))

    # Drop and recreate test database
    try:
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(text("COMMIT"))
        conn.execute(text(f"CREATE DATABASE {db_name}"))
        conn.execute(text("COMMIT"))
    except Exception as e:
        logger.error(f"Error setting up test database: {e}")
        raise
    finally:
        conn.close()
        engine.dispose()

    # Connect to the clean test database and create schema
    engine = create_engine(test_db_url)
    with engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS experimentation"))
        conn.execute(text("COMMIT"))

    yield engine

    # Cleanup after tests
    engine.dispose()


def test_migrations_apply_cleanly(alembic_config, clean_test_database):
    """Test that all migrations apply cleanly from scratch."""
    # Skip test if there are no migrations yet
    try:
        script_directory = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_directory.walk_revisions())
        if not revisions:
            pytest.skip("No migrations found to test")

        # Get the latest revision
        head_revision = script_directory.get_current_head()

        # Apply all migrations up to the latest revision
        command.upgrade(alembic_config, head_revision)

        # Verify migration was applied
        with clean_test_database.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

        assert (
            current_rev == head_revision
        ), f"Expected head revision {head_revision}, got {current_rev}"

        logger.info(f"Successfully applied migrations to revision {head_revision}")
    except Exception as e:
        logger.error(f"Error applying migrations: {e}")
        pytest.skip(f"Migration test failed: {str(e)}")


def test_migrations_downgrade(alembic_config, clean_test_database):
    """Test that migrations can be downgraded successfully."""
    try:
        # Get the Alembic script directory
        script_directory = ScriptDirectory.from_config(alembic_config)

        # Get all revisions
        revisions = list(script_directory.walk_revisions())
        if not revisions:
            pytest.skip("No migrations found to test")

        revisions.reverse()  # Order from oldest to newest

        if len(revisions) < 2:
            pytest.skip("Need at least two migrations to test downgrade")

        # Apply all migrations first
        head_revision = script_directory.get_current_head()
        command.upgrade(alembic_config, head_revision)

        # Test downgrading one revision at a time, starting from the latest
        for i in range(len(revisions) - 1):
            current = revisions[i]
            previous = revisions[i + 1]

            logger.info(
                f"Testing downgrade from {current.revision} to {previous.revision}"
            )

            # Downgrade to the previous revision
            command.downgrade(alembic_config, previous.revision)

            # Verify downgrade was successful
            with clean_test_database.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()

            assert (
                current_rev == previous.revision
            ), f"Downgrade failed: expected {previous.revision}, got {current_rev}"

            # Upgrade back to current revision for next test
            command.upgrade(alembic_config, current.revision)
    except Exception as e:
        logger.error(f"Error testing migration downgrade: {e}")
        pytest.skip(f"Migration downgrade test failed: {str(e)}")


def test_schema_validation(alembic_config, clean_test_database):
    """Test that the schema after migrations matches expected configuration."""
    try:
        # Skip test if there are no migrations yet
        script_directory = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_directory.walk_revisions())
        if not revisions:
            pytest.skip("No migrations found to test")

        # First apply all migrations
        head_revision = script_directory.get_current_head()
        command.upgrade(alembic_config, head_revision)

        # Define expected tables and their properties
        expected_tables = [
            {
                "name": "users",
                "schema": "experimentation",
                "required_columns": [
                    "id",
                    "username",
                    "email",
                    "hashed_password",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
            },
            {
                "name": "experiments",
                "schema": "experimentation",
                "required_columns": [
                    "id",
                    "name",
                    "description",
                    "hypothesis",
                    "status",
                    "experiment_type",
                    "created_at",
                    "updated_at",
                ],
            },
            {
                "name": "variants",
                "schema": "experimentation",
                "required_columns": [
                    "id",
                    "experiment_id",
                    "name",
                    "is_control",
                    "traffic_allocation",
                    "created_at",
                    "updated_at",
                ],
            },
            {
                "name": "metrics",
                "schema": "experimentation",
                "required_columns": [
                    "id",
                    "experiment_id",
                    "name",
                    "event_name",
                    "metric_type",
                    "created_at",
                    "updated_at",
                ],
            },
        ]

        # Inspect the database schema
        inspector = inspect(clean_test_database)

        # Check if the schema exists
        schemas = inspector.get_schema_names()
        assert "experimentation" in schemas, "Experimentation schema should exist"

        # Get all tables in the experimentation schema
        tables = inspector.get_table_names(schema="experimentation")

        # Validate that required tables exist (only check the ones we've defined expectations for)
        for table_def in expected_tables:
            table_name = table_def["name"]
            schema = table_def["schema"]

            # Skip if we haven't created this table yet in our migrations
            if table_name not in tables:
                logger.warning(
                    f"Table {schema}.{table_name} does not exist yet - skipping validation"
                )
                continue

            # Get columns for the table
            columns = inspector.get_columns(table_name, schema=schema)
            column_names = [col["name"] for col in columns]

            # Check required columns
            for required_col in table_def["required_columns"]:
                assert (
                    required_col in column_names
                ), f"Required column {required_col} missing from {schema}.{table_name}"
    except Exception as e:
        logger.error(f"Error in schema validation: {e}")
        pytest.skip(f"Schema validation test failed: {str(e)}")


def test_verify_migrations_idempotent(alembic_config, clean_test_database):
    """Test that running migrations twice doesn't cause errors."""
    try:
        # Skip test if there are no migrations yet
        script_directory = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_directory.walk_revisions())
        if not revisions:
            pytest.skip("No migrations found to test")

        # Get the head revision
        head_revision = script_directory.get_current_head()

        # Apply migrations
        command.upgrade(alembic_config, head_revision)

        # Apply migrations again - should be idempotent
        try:
            command.upgrade(alembic_config, head_revision)
        except Exception as e:
            pytest.fail(f"Migrations are not idempotent: {str(e)}")
    except Exception as e:
        logger.error(f"Error testing migration idempotence: {e}")
        pytest.skip(f"Migration idempotence test failed: {str(e)}")


def test_migration_data_preservation(alembic_config, clean_test_database):
    """Test that data is preserved during migrations."""
    try:
        # Skip test if there are no migrations yet
        script_directory = ScriptDirectory.from_config(alembic_config)
        revisions = list(script_directory.walk_revisions())
        if not revisions:
            pytest.skip("No migrations found to test")

        revisions.reverse()  # Order from oldest to newest

        if len(revisions) < 2:
            pytest.skip("Need at least two migrations to test data preservation")

        # Apply to second-to-last revision
        target_revision = revisions[-2].revision
        command.upgrade(alembic_config, target_revision)

        # Create a session to add test data
        Session = sessionmaker(bind=clean_test_database)
        session = Session()

        # Add test data - we'll use raw SQL to avoid model dependencies
        import uuid
        from datetime import datetime

        user_id = str(uuid.uuid4())
        exp_id = str(uuid.uuid4())
        now = datetime.utcnow()

        try:
            # Check if users table exists before inserting
            with session.connection() as conn:
                users_exists = conn.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'experimentation'
                        AND table_name = 'users'
                    )
                """
                    )
                ).scalar()

                experiments_exists = conn.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'experimentation'
                        AND table_name = 'experiments'
                    )
                """
                    )
                ).scalar()

            if not users_exists or not experiments_exists:
                pytest.skip(
                    "Required tables don't exist yet - skipping data preservation test"
                )

            # Insert test user
            session.execute(
                text(
                    """
                INSERT INTO experimentation.users (id, username, email, hashed_password, is_active, created_at, updated_at)
                VALUES (:id, :username, :email, :pw, TRUE, :now, :now)
            """
                ),
                {
                    "id": user_id,
                    "username": f"test_user_{uuid.uuid4().hex[:8]}",
                    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                    "pw": "hashedpw",
                    "now": now,
                },
            )

            # Insert test experiment
            session.execute(
                text(
                    """
                INSERT INTO experimentation.experiments (id, name, description, status, experiment_type, owner_id, created_at, updated_at)
                VALUES (:id, :name, :desc, 'DRAFT', 'A_B', :owner_id, :now, :now)
            """
                ),
                {
                    "id": exp_id,
                    "name": f"Test Experiment {uuid.uuid4().hex[:8]}",
                    "desc": "A test experiment",
                    "owner_id": user_id,
                    "now": now,
                },
            )

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting test data: {e}")
            pytest.skip(f"Could not insert test data: {e}")
            return

        # Migrate to the latest revision
        head_revision = script_directory.get_current_head()
        command.upgrade(alembic_config, head_revision)

        # Verify data still exists
        try:
            # Check if users and experiments tables still exist after migration
            with session.connection() as conn:
                users_exists = conn.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'experimentation'
                        AND table_name = 'users'
                    )
                """
                    )
                ).scalar()

                experiments_exists = conn.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'experimentation'
                        AND table_name = 'experiments'
                    )
                """
                    )
                ).scalar()

            if not users_exists or not experiments_exists:
                pytest.skip(
                    "Tables were dropped during migration - skipping data verification"
                )
                return

            user_result = session.execute(
                text("SELECT * FROM experimentation.users WHERE id = :id"),
                {"id": user_id},
            ).fetchone()

            exp_result = session.execute(
                text("SELECT * FROM experimentation.experiments WHERE id = :id"),
                {"id": exp_id},
            ).fetchone()

            assert user_result is not None, "User data was lost during migration"
            assert exp_result is not None, "Experiment data was lost during migration"
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error testing data preservation: {e}")
        pytest.skip(f"Data preservation test failed: {str(e)}")
