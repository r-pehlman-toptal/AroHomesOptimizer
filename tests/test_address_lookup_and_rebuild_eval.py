"""
Tests for address_lookup and rebuild_eval (readonly queries).

Run with: pytest tests/test_address_lookup_and_rebuild_eval.py -v
Requires DB_URL and existing property_address (and optionally property_geometry, zoning) data.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from src.db import QueryRunner
from src.query_service import queries
from src.query_service.schemas import (
    AddressLookupParams,
    RebuildEvalParams,
)


def _get_conn():
    """Return a connection; skip if DB unavailable."""
    try:
        runner = QueryRunner.from_env()
        return runner.engine.connect()
    except Exception:
        pytest.skip("DB_URL not configured or connection failed")


def _one_property_id(conn):
    """Return one existing property_id from property_address."""
    r = conn.execute(text("SELECT property_id FROM property_address LIMIT 1"))
    row = r.fetchone()
    r.close()
    if not row:
        pytest.skip("property_address is empty")
    return row[0]


def _one_property_id_without_geometry_or_zoning(conn):
    """Return a property_id that has no geometry and no zoning (if any)."""
    r = conn.execute(text("""
        SELECT pa.property_id FROM property_address pa
        LEFT JOIN property_geometry pg ON pg.property_id = pa.property_id
        LEFT JOIN property_zoning pz ON pz.property_id = pa.property_id
        WHERE pg.property_id IS NULL AND pz.property_id IS NULL
        LIMIT 1
    """))
    row = r.fetchone()
    r.close()
    return row[0] if row else None


def test_address_lookup_returns_property_id_for_known_numeric():
    """Address lookup with numeric address_text (property_id) returns one candidate with that property_id."""
    conn = _get_conn()
    try:
        pid = _one_property_id(conn)
        params = AddressLookupParams(address_text=str(pid))
        rows = queries.address_lookup(conn, params)
        assert len(rows) >= 1
        assert rows[0].property_id == pid
        assert rows[0].match_score == 1.0
    finally:
        conn.close()


def test_rebuild_eval_returns_parcel_footprint_and_comps_economics_when_data_exists():
    """Rebuild eval for a resolved property returns parcel_footprint and comps_economics (structure present)."""
    conn = _get_conn()
    try:
        pid = _one_property_id(conn)
        params = RebuildEvalParams(address_text=str(pid), target_living_sq_ft=2700.0)
        resp = queries.rebuild_eval(conn, params)
        assert resp.property_id == pid
        assert resp.resolved_address is not None
        assert resp.parcel_footprint is not None
        assert resp.comps_economics is not None
        assert resp.comps_economics.comp_count is not None
        assert resp.feasibility_fit is not None
    finally:
        conn.close()


def test_rebuild_eval_returns_invalid_and_notes_when_address_unresolved():
    """Rebuild eval with non-numeric address and no zip/city returns is_valid=false and notes."""
    conn = _get_conn()
    try:
        params = RebuildEvalParams(
            address_text="unknown street 123",
            zip_code=None,
            city_name=None,
        )
        resp = queries.rebuild_eval(conn, params)
        assert resp.property_id is None
        assert resp.resolved_address is None
        assert resp.is_valid is False
        assert resp.notes is not None
        assert "could not be resolved" in resp.notes.lower() or "zip_code" in resp.notes.lower()
    finally:
        conn.close()


def test_rebuild_eval_returns_invalid_when_geometry_and_zoning_missing():
    """Rebuild eval for a parcel with no geometry and no zoning returns is_valid=false and notes."""
    conn = _get_conn()
    try:
        pid = _one_property_id_without_geometry_or_zoning(conn)
        if pid is None:
            pytest.skip("No property without geometry and zoning found")
        params = RebuildEvalParams(address_text=str(pid), target_living_sq_ft=2700.0)
        resp = queries.rebuild_eval(conn, params)
        assert resp.property_id == pid
        assert resp.resolved_address is not None
        assert resp.is_valid is False
        assert resp.notes is not None
        assert "geometry" in resp.notes.lower() or "zoning" in resp.notes.lower()
    finally:
        conn.close()
