"""Добавление поля last_activity в таблицу users"""

from sqlalchemy import Column, DateTime
from datetime import datetime
from backend.database import Base, engine

def upgrade():
    # Добавляем колонку last_activity
    with engine.connect() as conn:
        conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        conn.commit()

def downgrade():
    # Удаляем колонку last_activity
    with engine.connect() as conn:
        conn.execute("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS last_activity
        """)
        conn.commit()

if __name__ == "__main__":
    upgrade() 