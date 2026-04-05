#!/usr/bin/env python3
"""
Database Migration Script for Customer Success FTE
Applies schema migrations to PostgreSQL database.

Usage:
    python migrate.py [command]

Commands:
    up          Apply all pending migrations
    down        Rollback last migration
    status      Show migration status
    seed        Seed database with initial data
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from datetime import datetime

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "fte_db"),
    "user": os.getenv("POSTGRES_USER", "fte_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

MIGRATIONS_DIR = Path(__file__).parent.parent / "database" / "migrations"


async def get_connection():
    """Get database connection."""
    return await asyncpg.connect(**DB_CONFIG)


async def ensure_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            checksum VARCHAR(64) NOT NULL
        )
    """)


async def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    rows = await conn.fetch("""
        SELECT version, applied_at FROM schema_migrations ORDER BY version
    """)
    return {row["version"]: row["applied_at"] for row in rows}


async def get_migration_files():
    """Get list of migration files sorted by version."""
    if not MIGRATIONS_DIR.exists():
        print(f"Migrations directory not found: {MIGRATIONS_DIR}")
        return []
    
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return migration_files


async def migrate_up():
    """Apply all pending migrations."""
    print("Starting database migration...")
    conn = await get_connection()
    
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied_migrations(conn)
        migration_files = await get_migration_files()
        
        if not migration_files:
            print("No migration files found.")
            return
        
        pending = [
            f for f in migration_files 
            if f.stem not in applied
        ]
        
        if not pending:
            print("Database is up to date. No migrations to apply.")
            return
        
        print(f"Found {len(pending)} pending migration(s):")
        
        for migration_file in pending:
            print(f"\nApplying migration: {migration_file.name}")
            
            # Read migration SQL
            sql = migration_file.read_text()
            
            # Calculate checksum
            import hashlib
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            
            # Apply migration
            try:
                await conn.execute(sql)
                
                # Record migration
                await conn.execute("""
                    INSERT INTO schema_migrations (version, checksum)
                    VALUES ($1, $2)
                """, migration_file.stem, checksum)
                
                print(f"  ✓ Applied successfully")
                
            except Exception as e:
                print(f"  ✗ Migration failed: {e}")
                raise
        
        print(f"\n✓ All migrations applied successfully!")
        
    finally:
        await conn.close()


async def migrate_down():
    """Rollback the last migration."""
    print("Rolling back last migration...")
    conn = await get_connection()
    
    try:
        await ensure_migrations_table(conn)
        
        # Get last applied migration
        last_migration = await conn.fetchrow("""
            SELECT version FROM schema_migrations 
            ORDER BY id DESC LIMIT 1
        """)
        
        if not last_migration:
            print("No migrations to rollback.")
            return
        
        version = last_migration["version"]
        print(f"Rolling back migration: {version}")
        
        # Find rollback file
        rollback_file = MIGRATIONS_DIR / f"{version}_rollback.sql"
        
        if not rollback_file.exists():
            print(f"Rollback file not found: {rollback_file}")
            print("Manual rollback required.")
            return
        
        # Apply rollback
        sql = rollback_file.read_text()
        await conn.execute(sql)
        
        # Remove migration record
        await conn.execute("""
            DELETE FROM schema_migrations WHERE version = $1
        """, version)
        
        print(f"✓ Rollback successful!")
        
    finally:
        await conn.close()


async def show_status():
    """Show migration status."""
    conn = await get_connection()
    
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied_migrations(conn)
        migration_files = await get_migration_files()
        
        print("\nMigration Status:")
        print("=" * 60)
        
        for migration_file in migration_files:
            version = migration_file.stem
            if version in applied:
                status = "✓ Applied"
                date = applied[version].strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {version:30} {status:15} {date}")
            else:
                status = "○ Pending"
                print(f"  {version:30} {status}")
        
        print("=" * 60)
        print(f"Total: {len(migration_files)} migrations")
        print(f"Applied: {len(applied)}")
        print(f"Pending: {len(migration_files) - len(applied)}")
        print()
        
    finally:
        await conn.close()


async def seed_database():
    """Seed database with initial data."""
    print("Seeding database...")
    conn = await get_connection()
    
    try:
        # Insert default channel configurations
        await conn.execute("""
            INSERT INTO channel_configs (channel, enabled, config, response_template, max_response_length)
            VALUES 
                ('email', true, '{"api": "gmail"}', 'email_template', 2000),
                ('whatsapp', true, '{"api": "twilio"}', 'whatsapp_template', 1600),
                ('web_form', true, '{"api": "internal"}', 'web_form_template', 1000)
            ON CONFLICT (channel) DO NOTHING
        """)
        
        print("✓ Seeded channel configurations")
        
        # Insert sample knowledge base entries
        sample_kb = [
            ("How to create a task", "To create a task in TechNova:\n1. Click the '+ New Task' button\n2. Enter task name\n3. Assign to team member\n4. Set due date\n5. Click 'Create'", "getting_started"),
            ("How to use Kanban boards", "Kanban boards help visualize your workflow:\n1. Go to Projects > Board View\n2. Drag cards between columns\n3. Set WIP limits for each column\n4. Use swimlanes to organize by assignee", "features"),
            ("API rate limits", "TechNova API rate limits:\n- Basic: 1,000 requests/hour\n- Pro: 5,000 requests/hour\n- Enterprise: 10,000 requests/hour\n\nContact support if you need higher limits.", "api"),
        ]
        
        for title, content, category in sample_kb:
            await conn.execute("""
                INSERT INTO knowledge_base (title, content, category)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
            """, title, content, category)
        
        print(f"✓ Seeded {len(sample_kb)} knowledge base entries")
        print("✓ Database seeding complete!")
        
    finally:
        await conn.close()


async def main():
    """Main entry point."""
    command = sys.argv[1] if len(sys.argv) > 1 else "up"
    
    if command == "up":
        await migrate_up()
    elif command == "down":
        await migrate_down()
    elif command == "status":
        await show_status()
    elif command == "seed":
        await seed_database()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python migrate.py [up|down|status|seed]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
