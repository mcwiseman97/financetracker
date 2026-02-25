"""
Atomic JSON I/O with backup support.
All writes use write-to-temp-then-rename pattern for crash safety.
"""
from __future__ import annotations
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


class StorageManager:
    DATA_DIR = Path.home() / ".local" / "share" / "financetracker"

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _path(self, filename: str) -> Path:
        return self.DATA_DIR / filename

    def load(self, filename: str) -> dict:
        """Load JSON file, returns {} if missing or corrupt."""
        path = self._path(filename)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self, filename: str, data: dict) -> None:
        """Atomic write: write to .tmp file then os.replace() for crash safety."""
        path = self._path(filename)
        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, path)
        except OSError:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    def backup(self) -> Path:
        """Create timestamped .zip backup of all data files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.DATA_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"financetracker_backup_{timestamp}.zip"

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for json_file in self.DATA_DIR.glob("*.json"):
                zf.write(json_file, json_file.name)

        return backup_path

    def file_exists(self, filename: str) -> bool:
        return self._path(filename).exists()

    def copy_default(self, src_path: Path, filename: str) -> None:
        """Copy a default/bundled file into the data directory if not present."""
        dest = self._path(filename)
        if not dest.exists() and src_path.exists():
            shutil.copy2(src_path, dest)
