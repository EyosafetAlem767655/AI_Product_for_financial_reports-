import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_storage_paths() -> tuple[Path, Path, Path]:
    database_path = os.getenv("RAILWAY_DATABASE_PATH")
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    is_vercel = bool(os.getenv("VERCEL"))

    if database_path:
        candidate = Path(database_path)
        db_file = candidate if candidate.suffix else candidate / "aw_portal.sqlite3"
        data_dir = db_file.parent
        report_default = data_dir / "generated_reports"
    elif volume_path:
        data_dir = Path(volume_path)
        db_file = data_dir / "aw_portal.sqlite3"
        report_default = data_dir / "generated_reports"
    elif is_vercel:
        data_dir = Path("/tmp/aw-portal")
        db_file = data_dir / "aw_portal.sqlite3"
        report_default = data_dir / "generated_reports"
    else:
        data_dir = Path(os.getenv("AW_PORTAL_DATA_DIR", PROJECT_ROOT / "data"))
        db_file = data_dir / "aw_portal.sqlite3"
        report_default = PROJECT_ROOT / "generated_reports"

    report_dir = Path(os.getenv("AW_PORTAL_REPORT_DIR", report_default))
    return data_dir, db_file, report_dir


DATA_DIR, DB_FILE, REPORT_DIR = _resolve_storage_paths()


def get_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if explicit_url:
        if explicit_url.startswith("postgres://"):
            return explicit_url.replace("postgres://", "postgresql+psycopg://", 1)
        if explicit_url.startswith("postgresql://"):
            return explicit_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return explicit_url
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DB_FILE}"


DATABASE_URL = get_database_url()
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    ensure_storage()
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
