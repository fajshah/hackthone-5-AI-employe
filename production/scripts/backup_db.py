#!/usr/bin/env python3
"""
Database Backup Script for Customer Success FTE
Creates PostgreSQL database backups with compression.

Usage:
    python backup_db.py [--output PATH] [--compress] [--retention DAYS]

Options:
    --output PATH       Output directory for backups (default: ./backups)
    --compress          Enable gzip compression (default: True)
    --retention DAYS    Number of days to retain backups (default: 30)
"""

import asyncio
import asyncpg
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import gzip
import shutil

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "fte_db"),
    "user": os.getenv("POSTGRES_USER", "fte_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "./backups"))
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))


def create_backup_directory():
    """Create backup directory if it doesn't exist."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Backup directory: {BACKUP_DIR.absolute()}")


def generate_backup_filename():
    """Generate backup filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"fte_backup_{timestamp}.sql"


async def backup_database(output_path: Path, compress: bool = True):
    """Create database backup using pg_dump."""
    print(f"Starting database backup...")
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    # Build pg_dump command
    dump_cmd = [
        "pg_dump",
        "-h", DB_CONFIG["host"],
        "-p", str(DB_CONFIG["port"]),
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["database"],
        "-F", "c",  # Custom format (compressed)
        "-f", str(output_path),
        "--verbose"
    ]
    
    # Set password environment variable
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    
    try:
        # Execute pg_dump
        process = subprocess.run(
            dump_cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            print(f"✗ Backup failed: {process.stderr}")
            return False
        
        # Check file size
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✓ Backup created: {output_path}")
        print(f"  Size: {file_size_mb:.2f} MB")
        
        return True
    
    except FileNotFoundError:
        print("✗ pg_dump not found. Please install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False


async def backup_with_gzip(output_path: Path):
    """Create backup and compress with gzip."""
    sql_file = output_path.with_suffix('.sql')
    
    # Build pg_dump command for plain SQL
    dump_cmd = [
        "pg_dump",
        "-h", DB_CONFIG["host"],
        "-p", str(DB_CONFIG["port"]),
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["database"],
        "-f", str(sql_file)
    ]
    
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    
    try:
        # Execute pg_dump
        process = subprocess.run(
            dump_cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            print(f"✗ Backup failed: {process.stderr}")
            return False
        
        # Compress with gzip
        print("Compressing backup...")
        with open(sql_file, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        sql_file.unlink()
        
        # Check file size
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✓ Backup created: {output_path}")
        print(f"  Size (compressed): {file_size_mb:.2f} MB")
        
        return True
    
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False


async def cleanup_old_backups(retention_days: int):
    """Remove backups older than retention period."""
    print(f"\nCleaning up backups older than {retention_days} days...")
    
    if not BACKUP_DIR.exists():
        print("No backup directory found.")
        return
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0
    
    for backup_file in BACKUP_DIR.glob("fte_backup_*"):
        # Extract date from filename
        try:
            date_str = backup_file.stem.replace("fte_backup_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            
            if file_date < cutoff_date:
                backup_file.unlink()
                print(f"  Deleted: {backup_file.name}")
                deleted_count += 1
        
        except ValueError:
            # Skip files with invalid naming pattern
            continue
    
    print(f"✓ Deleted {deleted_count} old backup(s)")


async def list_backups():
    """List all available backups."""
    print("\nAvailable Backups:")
    print("=" * 60)
    
    if not BACKUP_DIR.exists():
        print("No backup directory found.")
        return
    
    backups = sorted(BACKUP_DIR.glob("fte_backup_*"), reverse=True)
    
    if not backups:
        print("No backups found.")
        return
    
    for backup in backups:
        file_size = backup.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        modified = datetime.fromtimestamp(backup.stat().st_mtime)
        
        print(f"  {backup.name:40} {file_size_mb:8.2f} MB  {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("=" * 60)
    print(f"Total: {len(backups)} backup(s)")


async def restore_backup(backup_file: str):
    """Restore database from backup."""
    backup_path = BACKUP_DIR / backup_file
    
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}")
        return False
    
    print(f"Restoring from backup: {backup_file}")
    print("⚠️  WARNING: This will overwrite the current database!")
    print("Continue? (yes/no): ", end="")
    
    # For non-interactive usage, skip confirmation
    # response = input().lower()
    response = "yes"  # Auto-confirm for scripted usage
    
    if response not in ["yes", "y"]:
        print("Restore cancelled.")
        return False
    
    # Build pg_restore command
    restore_cmd = [
        "pg_restore",
        "-h", DB_CONFIG["host"],
        "-p", str(DB_CONFIG["port"]),
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["database"],
        "--clean",
        "--if-exists",
        str(backup_path)
    ]
    
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_CONFIG["password"]
    
    try:
        process = subprocess.run(
            restore_cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            print(f"✗ Restore failed: {process.stderr}")
            return False
        
        print(f"✓ Database restored from: {backup_file}")
        return True
    
    except Exception as e:
        print(f"✗ Restore failed: {e}")
        return False


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup PostgreSQL database")
    parser.add_argument("--output", default=str(BACKUP_DIR),
                        help="Output directory for backups")
    parser.add_argument("--compress", action="store_true", default=True,
                        help="Enable gzip compression")
    parser.add_argument("--retention", type=int, default=RETENTION_DAYS,
                        help="Retention period in days")
    parser.add_argument("--list", action="store_true",
                        help="List all backups")
    parser.add_argument("--restore", metavar="FILE",
                        help="Restore from backup file")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="Skip old backup cleanup")
    
    args = parser.parse_args()
    
    # Update backup directory
    global BACKUP_DIR, RETENTION_DAYS
    BACKUP_DIR = Path(args.output)
    RETENTION_DAYS = args.retention
    
    if args.list:
        await list_backups()
        return
    
    if args.restore:
        await restore_backup(args.restore)
        return
    
    # Create backup
    create_backup_directory()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.compress:
        filename = f"fte_backup_{timestamp}.sql.gz"
        output_path = BACKUP_DIR / filename
        success = await backup_with_gzip(output_path)
    else:
        filename = f"fte_backup_{timestamp}.sql"
        output_path = BACKUP_DIR / filename
        success = await backup_database(output_path, compress=False)
    
    if success and not args.no_cleanup:
        await cleanup_old_backups(RETENTION_DAYS)
    
    if success:
        print("\n✓ Backup complete!")
    else:
        print("\n✗ Backup failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
