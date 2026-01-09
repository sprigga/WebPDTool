"""Change measured_value from DECIMAL to String

Revision ID: 20250109_change_measured_value
Revises: 9dd55b733f64
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250109_change_measured_value'
down_revision = '9dd55b733f64'
branch_labels = None
depends_on = None


def upgrade():
    """Change measured_value column from DECIMAL to String to support string values"""
    # SQLite doesn't support ALTER COLUMN directly, need to recreate table
    # Get the bind to determine database type
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'sqlite':
        # SQLite approach: recreate table
        op.execute("""
            CREATE TABLE test_results_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                test_plan_id INTEGER NOT NULL,
                item_no INTEGER NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                measured_value VARCHAR(100),
                lower_limit DECIMAL(15, 6),
                upper_limit DECIMAL(15, 6),
                unit VARCHAR(20),
                result VARCHAR(10) NOT NULL,
                error_message TEXT,
                test_time TIMESTAMP,
                execution_duration_ms INTEGER,
                FOREIGN KEY(session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY(test_plan_id) REFERENCES test_plans(id)
            )
        """)
        
        op.execute("""
            INSERT INTO test_results_new 
            SELECT id, session_id, test_plan_id, item_no, item_name,
                   CAST(measured_value AS VARCHAR(100)),
                   lower_limit, upper_limit, unit, result, error_message,
                   test_time, execution_duration_ms
            FROM test_results
        """)
        
        op.execute("DROP TABLE test_results")
        op.execute("ALTER TABLE test_results_new RENAME TO test_results")
        
        # Recreate indexes
        op.create_index('ix_test_results_session_id', 'test_results', ['session_id'])
        op.create_index('ix_test_results_result', 'test_results', ['result'])
        op.create_index('ix_test_results_test_time', 'test_results', ['test_time'])
    else:
        # PostgreSQL/MySQL approach: use ALTER COLUMN
        op.alter_column(
            'test_results',
            'measured_value',
            existing_type=sa.DECIMAL(15, 6),
            type_=sa.String(100),
            existing_nullable=True
        )


def downgrade():
    """Revert measured_value column back to DECIMAL"""
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'sqlite':
        # SQLite approach: recreate table
        op.execute("""
            CREATE TABLE test_results_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                test_plan_id INTEGER NOT NULL,
                item_no INTEGER NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                measured_value DECIMAL(15, 6),
                lower_limit DECIMAL(15, 6),
                upper_limit DECIMAL(15, 6),
                unit VARCHAR(20),
                result VARCHAR(10) NOT NULL,
                error_message TEXT,
                test_time TIMESTAMP,
                execution_duration_ms INTEGER,
                FOREIGN KEY(session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY(test_plan_id) REFERENCES test_plans(id)
            )
        """)
        
        op.execute("""
            INSERT INTO test_results_new 
            SELECT id, session_id, test_plan_id, item_no, item_name,
                   CAST(measured_value AS DECIMAL(15, 6)),
                   lower_limit, upper_limit, unit, result, error_message,
                   test_time, execution_duration_ms
            FROM test_results
        """)
        
        op.execute("DROP TABLE test_results")
        op.execute("ALTER TABLE test_results_new RENAME TO test_results")
        
        # Recreate indexes
        op.create_index('ix_test_results_session_id', 'test_results', ['session_id'])
        op.create_index('ix_test_results_result', 'test_results', ['result'])
        op.create_index('ix_test_results_test_time', 'test_results', ['test_time'])
    else:
        # PostgreSQL/MySQL approach: use ALTER COLUMN
        op.alter_column(
            'test_results',
            'measured_value',
            existing_type=sa.String(100),
            type_=sa.DECIMAL(15, 6),
            existing_nullable=True
        )
