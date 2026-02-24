from pathlib import Path


def load_sql(path: Path) -> str:
    """
    Read an .sql file from disk and return its contents.

    This small helper keeps SQL loading consistent across ETL,
    gold/aggregate builds, and ad‑hoc analytics queries.
    """
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")

