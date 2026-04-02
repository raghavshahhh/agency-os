#!/usr/bin/env python3
"""
RAGSPRO Backup System — Daily auto-backup with 7-day retention
"""

import json
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR

BACKUP_DIR = DATA_DIR / "backups"
BACKUP_RETENTION_DAYS = 7


def ensure_backup_dir():
    """Ensure backup directory exists"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_daily_backup():
    """Create a daily backup of all data files"""
    ensure_backup_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = BACKUP_DIR / backup_name
    backup_path.mkdir(exist_ok=True)

    # Files to backup
    files_to_backup = [
        "leads.json",
        "clients.json",
        "pipeline.json",
        "revenue.json",
        "outreach_log.json",
        "crm_clients.json",
        "crm_deals.json",
        "settings.json"
    ]

    backed_up = []
    errors = []

    for filename in files_to_backup:
        source = DATA_DIR / filename
        if source.exists():
            try:
                shutil.copy2(source, backup_path / filename)
                backed_up.append(filename)
            except Exception as e:
                errors.append(f"{filename}: {e}")

    # Backup content folder
    content_dir = DATA_DIR / "content"
    if content_dir.exists():
        try:
            shutil.copytree(content_dir, backup_path / "content", dirs_exist_ok=True)
            backed_up.append("content/")
        except Exception as e:
            errors.append(f"content/: {e}")

    # Create ZIP archive
    zip_path = backup_path.with_suffix('.zip')
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in backup_path.rglob('*'):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(backup_path.parent))

        # Remove uncompressed backup
        shutil.rmtree(backup_path)

        print(f"✅ Backup created: {zip_path.name}")
        print(f"   Files backed up: {len(backed_up)}")
        if errors:
            print(f"   Errors: {len(errors)}")

        return zip_path
    except Exception as e:
        print(f"❌ Failed to create ZIP: {e}")
        return None


def cleanup_old_backups():
    """Remove backups older than retention period"""
    ensure_backup_dir()

    cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
    removed = 0

    for backup_file in BACKUP_DIR.glob("backup_*.zip"):
        try:
            # Extract date from filename
            date_str = backup_file.stem.split('_')[1]
            file_date = datetime.strptime(date_str, "%Y%m%d")

            if file_date < cutoff_date:
                backup_file.unlink()
                removed += 1
        except:
            pass

    if removed > 0:
        print(f"🗑️ Cleaned up {removed} old backups (retention: {BACKUP_RETENTION_DAYS} days)")

    return removed


def list_backups():
    """List available backups"""
    ensure_backup_dir()

    backups = []
    for backup_file in sorted(BACKUP_DIR.glob("backup_*.zip"), reverse=True):
        try:
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": backup_file,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            })
        except:
            pass

    return backups


def restore_backup(backup_name):
    """Restore data from a backup"""
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        return {"success": False, "error": "Backup not found"}

    try:
        # Extract backup
        with zipfile.ZipFile(backup_path, 'r') as zf:
            zf.extractall(BACKUP_DIR / "temp_restore")

        # Copy files back to data dir
        temp_dir = BACKUP_DIR / "temp_restore"
        for file_path in temp_dir.rglob('*.json'):
            target = DATA_DIR / file_path.name
            shutil.copy2(file_path, target)

        # Cleanup temp
        shutil.rmtree(temp_dir)

        return {"success": True, "message": f"Restored from {backup_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_backup_job():
    """Run the complete backup job (daily at midnight)"""
    print(f"[{datetime.now()}] Running daily backup...")

    backup = create_daily_backup()
    cleanup_old_backups()

    if backup:
        return {"success": True, "backup": backup.name}
    return {"success": False, "error": "Backup creation failed"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAGSPRO Backup System")
    parser.add_argument("action", choices=["backup", "list", "restore", "cleanup"], default="backup")
    parser.add_argument("--name", help="Backup name for restore")

    args = parser.parse_args()

    if args.action == "backup":
        run_backup_job()
    elif args.action == "list":
        backups = list_backups()
        print(f"\n📦 Available Backups ({len(backups)}):")
        for b in backups:
            print(f"  {b['name']} - {b['size_mb']}MB - {b['created']}")
    elif args.action == "restore":
        if not args.name:
            print("Error: --name required for restore")
        else:
            result = restore_backup(args.name)
            print(result["message"] if result["success"] else result["error"])
    elif args.action == "cleanup":
        cleanup_old_backups()
