"""Explicit runtime paths; configuration never creates files."""
from dataclasses import dataclass
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    environment: str = "development"
    vapid_private_key: str | None = None
    vapid_subject: str | None = None

    def __post_init__(self):
        if self.environment not in {"test", "development", "production"}:
            raise ValueError("PIGPEN_ENV must be test, development or production")
        if not self.data_dir.is_absolute():
            raise ValueError("PIGPEN_DATA_DIR must be absolute")
        root = self.data_dir.resolve()
        if root.exists() and not root.is_dir():
            raise ValueError('PIGPEN_DATA_DIR must be a directory')
        if root == PROJECT_ROOT or root.is_relative_to(PROJECT_ROOT):
            raise ValueError("Runtime data must be outside the source checkout")
        if self.environment == "test" and self.vapid_private_key:
            raise ValueError("Tests must not use production push credentials")
        object.__setattr__(self, "data_dir", root)

    @property
    def environment_marker(self):
        return self.data_dir / '.pigpen-environment'

    def verify_storage(self, allow_new=False):
        if self.database_path.is_symlink() or self.environment_marker.is_symlink() or self.uploads_dir.is_symlink():
            raise ValueError('Database, environment marker and upload directory must not be symbolic links')
        if self.environment_marker.is_file():
            if self.environment_marker.read_text().strip() != self.environment:
                raise ValueError('Configured environment does not match this data directory')
        elif self.database_path.exists() or not allow_new:
            raise ValueError('Unregistered data directory; use explicit migration or restore')

    @property
    def database_path(self):
        return self.data_dir / "pigpen.sqlite3"

    @property
    def uploads_dir(self):
        return self.data_dir / "uploads"

    @classmethod
    def from_env(cls):
        raw = os.environ.get("PIGPEN_DATA_DIR")
        if not raw:
            raise ValueError("Set PIGPEN_DATA_DIR explicitly; no default financial database")
        return cls(Path(raw), os.environ.get("PIGPEN_ENV", "development"),
                   os.environ.get("PIGPEN_VAPID_PRIVATE_KEY"), os.environ.get("PIGPEN_VAPID_SUBJECT"))
