"""
Attom API client: property detail by address. API key from env ATTOM_API_KEY.
Ref: https://api.developer.attomdata.com/docs
"""
from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional


ATTOM_BASE = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
MIN_VALID_PPSF = 400.0


def _get_api_key() -> Optional[str]:
    return (os.getenv("ATTOM_API_KEY") or "").strip() or None


def fetch_property_detail(address: str) -> Dict[str, Any]:
    """
    Fetch property detail from Attom by address. Keeps API key server-side.
    Returns normalized dict for UI: full_address, line1, city, state, zip, beds, baths,
    living_sq_ft, lot_sq_ft, year_built, property_type, attom_id, last_sale_amount, last_sale_date, avm_value.
    Raises on network/API error; returns empty result if no match.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ATTOM_API_KEY not set", "property": None}

    encoded = urllib.parse.quote(address.strip())
    url = f"{ATTOM_BASE}/property/detail?address={encoded}"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "APIKey": api_key,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        if e.code == 400:
            return {"error": "Address not found or invalid", "property": None}
        return {"error": f"Attom API error {e.code}: {body[:200]}", "property": None}
    except urllib.error.URLError as e:
        return {"error": str(e.reason) if getattr(e, "reason", None) else str(e), "property": None}
    except Exception as e:
        return {"error": str(e), "property": None}

    # Attom returns { "property": [ { ... } ] } or similar
    props: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        props = data.get("property") or data.get("properties") or []
    if isinstance(data, list):
        props = data
    if not props or not isinstance(props, list):
        return {"error": None, "property": _normalize_from_raw(None, address)}

    # Use first match
    raw = props[0] if isinstance(props[0], dict) else None
    normalized = _normalize_from_raw(raw, address)
    # If we have attomId but no AVM, fetch AVM from /attomavm/detail
    if normalized.get("attom_id") and normalized.get("avm_value") is None:
        avm_val, avm_conf = _fetch_avm_by_attom_id(api_key, str(normalized["attom_id"]))
        if avm_val is not None:
            normalized["avm_value"] = avm_val
            normalized["avm_confidence"] = avm_conf
    return {"error": None, "property": normalized}


def _fetch_avm_by_attom_id(api_key: str, attom_id: str) -> tuple[Optional[float], Optional[float]]:
    """Fetch AVM value and confidence from Attom /attomavm/detail by attomId. Returns (value, confidence)."""
    url = f"{ATTOM_BASE}/attomavm/detail?attomId={urllib.parse.quote(attom_id)}"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "APIKey": api_key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return (None, None)
    # Response may be { "property": [ { "valuation": { "avm": 2087800, "scr": 0.85 } } ] } or similar
    props = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
    if not props or not isinstance(props[0], dict):
        return (None, None)
    p = props[0]
    val_block = p.get("valuation") or p.get("avm") or {}
    if isinstance(val_block, dict):
        avm = val_block.get("avm") or val_block.get("value") or val_block.get("amount")
        scr = val_block.get("scr") or val_block.get("confidence")
    try:
        return (float(avm), float(scr) if scr is not None else None)
    except (TypeError, ValueError):
        pass
    avm = _deep_get(p, "avm", "value", "amount")
    try:
        return (float(avm), None) if avm is not None else (None, None)
    except (TypeError, ValueError):
        return (None, None)


def geocode_address(address: str) -> tuple[Optional[float], Optional[float]]:
    """
    Resolve address to (latitude, longitude) using Attom property/detail.
    Returns (None, None) if key missing, address not found, or API error.
    """
    api_key = _get_api_key()
    if not api_key:
        return (None, None)
    encoded = urllib.parse.quote(address.strip())
    url = f"{ATTOM_BASE}/property/detail?address={encoded}"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "APIKey": api_key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return (None, None)
    props = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
    if not props or not isinstance(props[0], dict):
        return (None, None)
    loc = (props[0].get("location") or {}) if isinstance(props[0].get("location"), dict) else {}
    lat = loc.get("latitude") or loc.get("Latitude")
    lon = loc.get("longitude") or loc.get("Longitude")
    try:
        return (float(lat), float(lon)) if lat is not None and lon is not None else (None, None)
    except (TypeError, ValueError):
        return (None, None)


def fetch_avm_snapshot(
    latitude: float, longitude: float, radius_miles: float
) -> Dict[str, Any]:
    """
    Fetch AVM snapshot from Attom for properties within radius of (lat, lon).
    Returns { "error": str or None, "properties": [ { "avm_value", "address", "distance", ... } ] }.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ATTOM_API_KEY not set", "properties": []}
    url = f"{ATTOM_BASE}/avm/snapshot?latitude={latitude}&longitude={longitude}&radius={radius_miles}"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "APIKey": api_key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        return {"error": f"Attom API error {e.code}: {body[:200]}", "properties": []}
    except Exception as e:
        return {"error": str(e), "properties": []}
    props = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
    if not isinstance(props, list):
        return {"error": None, "properties": []}
    out_list: List[Dict[str, Any]] = []
    for p in props:
        if not isinstance(p, dict):
            continue
        avm_block = p.get("avm") or {}
        amt = avm_block.get("amount") if isinstance(avm_block.get("amount"), dict) else {}
        val = amt.get("value") or amt.get("Value") if isinstance(amt, dict) else None
        try:
            avm_value = float(val) if val is not None else None
        except (TypeError, ValueError):
            avm_value = None
        addr_block = p.get("address") or {}
        one_line = (addr_block.get("oneLine") or "") if isinstance(addr_block, dict) else ""
        loc_block = p.get("location") or {}
        dist = loc_block.get("distance") or loc_block.get("Distance") if isinstance(loc_block, dict) else None
        try:
            distance = float(dist) if dist is not None else None
        except (TypeError, ValueError):
            distance = None
        if avm_value is not None:
            out_list.append({
                "avm_value": avm_value,
                "address": one_line or None,
                "distance_miles": distance,
            })
    return {"error": None, "properties": out_list}


def fetch_avm_in_radius(address: str, radius_miles: float) -> Dict[str, Any]:
    """
    Estimated value of properties within a given radius of an address.
    Geocodes address via Attom, then calls AVM snapshot and aggregates.
    Returns { "error", "center_latitude", "center_longitude", "property_count",
              "median_avm_value", "mean_avm_value", "min_avm_value", "max_avm_value", "properties" }.
    """
    lat, lon = geocode_address(address)
    if lat is None or lon is None:
        return {
            "error": "Address could not be geocoded",
            "center_latitude": None,
            "center_longitude": None,
            "property_count": 0,
            "median_avm_value": None,
            "mean_avm_value": None,
            "min_avm_value": None,
            "max_avm_value": None,
            "properties": [],
        }
    snap = fetch_avm_snapshot(lat, lon, radius_miles)
    if snap.get("error"):
        return {
            "error": snap["error"],
            "center_latitude": lat,
            "center_longitude": lon,
            "property_count": 0,
            "median_avm_value": None,
            "mean_avm_value": None,
            "min_avm_value": None,
            "max_avm_value": None,
            "properties": [],
        }
    plist = snap.get("properties") or []
    if not plist:
        return {
            "error": None,
            "center_latitude": lat,
            "center_longitude": lon,
            "property_count": 0,
            "median_avm_value": None,
            "mean_avm_value": None,
            "min_avm_value": None,
            "max_avm_value": None,
            "properties": [],
        }
    values = [x["avm_value"] for x in plist if x.get("avm_value") is not None]
    values.sort()
    n = len(values)
    mean_val = sum(values) / n if n else None
    median_val = values[n // 2] if n else None
    min_val = values[0] if values else None
    max_val = values[-1] if values else None
    return {
        "error": None,
        "center_latitude": lat,
        "center_longitude": lon,
        "property_count": n,
        "median_avm_value": median_val,
        "mean_avm_value": mean_val,
        "min_avm_value": min_val,
        "max_avm_value": max_val,
        "properties": plist,
    }


def _deep_get(obj: Any, *keys: str) -> Any:
    """Get first value found for any of the keys, recursing into dicts and lists."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] is not None:
                return obj[k]
        for v in obj.values():
            found = _deep_get(v, *keys)
            if found is not None:
                return found
    if isinstance(obj, list):
        for item in obj:
            found = _deep_get(item, *keys)
            if found is not None:
                return found
    return None


def _safe_int(val: Any) -> Optional[int]:
    """Coerce to int for beds, baths, year_built."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def _safe_float(val: Any) -> Optional[float]:
    """Coerce to float for sqft, lot_sq_ft."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# ---- One-by-one extractors (Attom response paths vary; try known paths then deep search) ----


def _extract_beds(raw: Optional[Dict[str, Any]]) -> Optional[int]:
    """Attom: property.building.rooms.beds (docs)."""
    if not raw:
        return None
    bldg = raw.get("building")
    if isinstance(bldg, dict):
        rooms = bldg.get("rooms")
        if isinstance(rooms, dict):
            for key in ("beds", "Beds"):
                if rooms.get(key) is not None:
                    return _safe_int(rooms[key])
        for key in ("beds", "Beds"):
            if bldg.get(key) is not None:
                return _safe_int(bldg[key])
    for key in ("beds", "Beds"):
        if raw.get(key) is not None:
            return _safe_int(raw[key])
    return _safe_int(_deep_get(raw, "beds", "bedrooms"))


def _extract_baths(raw: Optional[Dict[str, Any]]) -> Optional[int]:
    """Attom: property.building.rooms.bathstotal (lowercase in response, per docs)."""
    if not raw:
        return None
    bldg = raw.get("building")
    if isinstance(bldg, dict):
        rooms = bldg.get("rooms")
        if isinstance(rooms, dict):
            for key in ("bathstotal", "bathsTotal", "baths", "BathsTotal"):
                if rooms.get(key) is not None:
                    return _safe_int(rooms[key])
        for key in ("bathstotal", "bathsTotal", "baths"):
            if bldg.get(key) is not None:
                return _safe_int(bldg[key])
    for key in ("bathstotal", "bathsTotal", "baths"):
        if raw.get(key) is not None:
            return _safe_int(raw[key])
    return _safe_int(_deep_get(raw, "bathstotal", "bathsTotal", "baths", "bathrooms"))


def _extract_living_sq_ft(raw: Optional[Dict[str, Any]]) -> Optional[float]:
    """Attom: property.building.size.universalsize | livingsize | bldgsize (lowercase, per docs)."""
    if not raw:
        return None
    bldg = raw.get("building")
    if isinstance(bldg, dict):
        size_block = bldg.get("size")
        if isinstance(size_block, dict):
            for key in ("universalsize", "universalSize", "livingsize", "livingSize", "bldgsize", "size", "gla"):
                if size_block.get(key) is not None:
                    return _safe_float(size_block[key])
        for key in ("size", "universalSize", "universalsize", "gla", "livingSqFt", "sqft"):
            if bldg.get(key) is not None:
                return _safe_float(bldg[key])
    for key in ("universalsize", "universalSize", "size"):
        if raw.get(key) is not None:
            return _safe_float(raw[key])
    return _safe_float(_deep_get(raw, "universalsize", "universalSize", "livingsize", "size", "gla", "livingSqFt", "sqft"))


def _extract_year_built(raw: Optional[Dict[str, Any]]) -> Optional[int]:
    """Attom: property.summary.yearbuilt (lowercase) or yearBuilt (per docs)."""
    if not raw:
        return None
    summary = raw.get("summary")
    if isinstance(summary, dict):
        for key in ("yearbuilt", "yearBuilt", "year_built"):
            if summary.get(key) is not None:
                return _safe_int(summary[key])
    bldg = raw.get("building")
    if isinstance(bldg, dict) and bldg.get("yearBuilt") is not None:
        return _safe_int(bldg["yearBuilt"])
    for key in ("yearbuilt", "yearBuilt", "year_built"):
        if raw.get(key) is not None:
            return _safe_int(raw[key])
    return _safe_int(_deep_get(raw, "yearbuilt", "yearBuilt", "year_built"))


def estimate_buildable_footprint(
    lot_sq_ft: Optional[float],
    lot_width_ft: Optional[float] = None,
    lot_depth_ft: Optional[float] = None,
    front_setback_ft: float = 20.0,
    rear_setback_ft: float = 20.0,
    side_setback_ft: float = 5.0,
) -> tuple[Optional[float], Optional[float], Optional[float], str]:
    """
    Estimate buildable footprint from lot area and optional dimensions. Use when zoning is unknown (e.g. Attom).
    If width/depth missing, assumes depth ≈ 2× width (typical residential). Uses assumed setbacks.
    Returns (buildable_width_ft, buildable_depth_ft, buildable_sq_ft, notes).
    """
    if lot_sq_ft is None or lot_sq_ft <= 0:
        return (None, None, None, "Lot area missing or invalid.")
    if lot_width_ft is not None and lot_depth_ft is not None and lot_width_ft > 0 and lot_depth_ft > 0:
        w_ft, d_ft = lot_width_ft, lot_depth_ft
        notes = "Estimated from Attom lot dimensions; assumed setbacks (no zoning)."
    else:
        # Assume depth = 2 * width (common residential): area = w * 2w = 2*w^2 => w = sqrt(area/2)
        w_ft = math.sqrt(lot_sq_ft / 2.0)
        d_ft = lot_sq_ft / w_ft if w_ft > 0 else None
        notes = "Estimated from lot area (depth≈2×width); assumed setbacks 20/20/5 ft (no zoning)."
    if w_ft is None or d_ft is None or w_ft <= 0 or d_ft <= 0:
        return (None, None, None, notes)
    build_w = max(0.0, w_ft - 2 * side_setback_ft)
    build_d = max(0.0, d_ft - front_setback_ft - rear_setback_ft)
    build_sq = round(build_w * build_d, 2) if (build_w > 0 and build_d > 0) else 0.0
    if build_w <= 0 or build_d <= 0:
        notes += " Setbacks exceed estimated dimensions; no buildable pad."
    return (
        round(build_w, 2) if build_w > 0 else None,
        round(build_d, 2) if build_d > 0 else None,
        build_sq if build_sq > 0 else None,
        notes,
    )


def _extract_lot_sq_ft(raw: Optional[Dict[str, Any]]) -> Optional[float]:
    """Attom: property.lot.lotsize2 (lowercase in response, per docs)."""
    if not raw:
        return None
    lot = raw.get("lot")
    if isinstance(lot, dict):
        for key in ("lotsize2", "lotSize2", "size", "sqft", "lotSqFt"):
            if lot.get(key) is not None:
                return _safe_float(lot[key])
    for key in ("lotsize2", "lotSize2"):
        if raw.get(key) is not None:
            return _safe_float(raw[key])
    return _safe_float(_deep_get(raw, "lotsize2", "lotSize2", "lotSize", "lotSqFt", "lot_sqft"))


def _extract_lot_dimensions(raw: Optional[Dict[str, Any]]) -> tuple[Optional[float], Optional[float]]:
    """Attom: property.lot.depth and property.lot.frontage (width). Returns (lot_depth_ft, lot_width_ft)."""
    if not raw or not isinstance(raw, dict):
        return (None, None)
    lot = raw.get("lot")
    if not isinstance(lot, dict):
        return (None, None)
    depth = lot.get("depth") or lot.get("lotDepth")
    frontage = lot.get("frontage") or lot.get("frontageFt") or lot.get("width")
    return (_safe_float(depth), _safe_float(frontage))


def _parse_sale_history(raw: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse salehistory array from a raw Attom property dict. Returns list of sale records."""
    out: List[Dict[str, Any]] = []
    if not raw or not isinstance(raw, dict):
        return out
    salehistory = raw.get("salehistory") or raw.get("saleHistory") or []
    if not isinstance(salehistory, list):
        return out
    for sh in salehistory:
        if not isinstance(sh, dict):
            continue
        amt = sh.get("amount") or {}
        calc = sh.get("calculation") or {}
        sale_date = sh.get("saleTransDate") or sh.get("salesearchdate")
        sale_amt = (amt.get("saleamt") or amt.get("saleAmt")) if isinstance(amt, dict) else None
        rec_date = amt.get("salerecdate") or amt.get("saleRecDate") if isinstance(amt, dict) else None
        sale_type = amt.get("saletranstype") or amt.get("saleTransType") if isinstance(amt, dict) else None
        ppsf = (calc.get("pricepersizeunit") or calc.get("pricePerSizeUnit")) if isinstance(calc, dict) else None
        ppbed = (calc.get("priceperbed") or calc.get("pricePerBed")) if isinstance(calc, dict) else None
        try:
            sale_amt = float(sale_amt) if sale_amt is not None else None
        except (TypeError, ValueError):
            sale_amt = None
        try:
            ppsf = float(ppsf) if ppsf is not None else None
        except (TypeError, ValueError):
            ppsf = None
        try:
            ppbed = float(ppbed) if ppbed is not None else None
        except (TypeError, ValueError):
            ppbed = None
        out.append({
            "sale_date": sale_date,
            "sale_amount": sale_amt,
            "record_date": rec_date,
            "sale_type": sale_type,
            "price_per_sqft": ppsf,
            "price_per_bed": ppbed,
        })
    return out


def fetch_sale_history(address: str) -> Dict[str, Any]:
    """
    Fetch sale history for an address using Attom's /saleshistory/snapshot endpoint.
    Falls back to /property/detail if the dedicated endpoint returns nothing.
    Returns { "error": str or None, "sale_history": [ { sale_date, sale_amount, ... } ] }.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ATTOM_API_KEY not set", "sale_history": []}

    encoded = urllib.parse.quote(address.strip())

    def _fetch_url(url: str) -> Optional[Dict]:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "APIKey": api_key},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 400:
                return None
            body = ""
            try:
                body = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"Attom API error {e.code}: {body[:200]}")

    # Primary: dedicated sale-history endpoint
    try:
        data = _fetch_url(f"{ATTOM_BASE}/saleshistory/snapshot?address={encoded}")
    except RuntimeError as e:
        return {"error": str(e), "sale_history": []}
    except Exception as e:
        return {"error": str(e), "sale_history": []}

    if data is not None:
        props = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
        if props and isinstance(props, list) and isinstance(props[0], dict):
            sale_history = _parse_sale_history(props[0])
            if sale_history:
                return {"error": None, "sale_history": sale_history}

    # Fallback: /property/detail also sometimes contains salehistory
    try:
        data2 = _fetch_url(f"{ATTOM_BASE}/property/detail?address={encoded}")
    except Exception:
        return {"error": None, "sale_history": []}

    if data2 is None:
        return {"error": "Address not found or invalid", "sale_history": []}
    props2 = (data2.get("property") or data2.get("properties") or []) if isinstance(data2, dict) else []
    if not props2 or not isinstance(props2, list) or not isinstance(props2[0], dict):
        return {"error": None, "sale_history": []}
    return {"error": None, "sale_history": _parse_sale_history(props2[0])}


def _normalize_from_raw(raw: Optional[Dict[str, Any]], fallback_address: str) -> Dict[str, Any]:
    """Build a stable schema for the UI from Attom property/detail response."""
    out: Dict[str, Any] = {
        "full_address": fallback_address,
        "line1": None,
        "line2": None,
        "city": None,
        "state": None,
        "zip": None,
        "beds": None,
        "baths": None,
        "living_sq_ft": None,
        "lot_sq_ft": None,
        "year_built": None,
        "property_type": None,
        "attom_id": None,
        "last_sale_amount": None,
        "last_sale_date": None,
        "avm_value": None,
        "avm_confidence": None,
        "assessed_value": None,
        "tax_amount": None,
        "tax_year": None,
        "market_value": None,
        "latitude": None,
        "longitude": None,
        "avm_high": None,
        "avm_low": None,
        "avm_per_sqft": None,
        "sale_history": [],
    }
    if not raw:
        out["full_address"] = fallback_address
        return out

    # Identifier (Attom response: attomId, id, or obPropId)
    ident = raw.get("identifier") or {}
    if isinstance(ident, dict):
        out["attom_id"] = ident.get("attomId") or ident.get("id") or ident.get("obPropId")

    # Address (Attom uses address block with line1, line2, locality, countrySubd, postal1)
    addr = raw.get("address") or {}
    if isinstance(addr, dict):
        out["line1"] = addr.get("line1") or addr.get("addressLine1")
        out["line2"] = addr.get("line2") or addr.get("addressLine2")
        out["city"] = addr.get("locality") or addr.get("city")
        out["state"] = addr.get("countrySubd") or addr.get("state")
        out["zip"] = (addr.get("postal1") or addr.get("postalCode") or "").strip()
        one = (addr.get("oneLine") or "").strip()
        if one:
            out["full_address"] = one
        elif out["line1"] or out["city"]:
            parts = [p for p in [out["line1"], out["city"], out["state"], out["zip"]] if p]
            out["full_address"] = ", ".join(parts) if parts else fallback_address

    # One-by-one: beds, baths, sqft, year built, lot size and dimensions
    out["beds"] = _extract_beds(raw)
    out["baths"] = _extract_baths(raw)
    out["living_sq_ft"] = _extract_living_sq_ft(raw)
    out["year_built"] = _extract_year_built(raw)
    out["lot_sq_ft"] = _extract_lot_sq_ft(raw)
    lot_depth, lot_frontage = _extract_lot_dimensions(raw)
    out["lot_depth_ft"] = lot_depth
    out["lot_width_ft"] = lot_frontage  # Attom uses "frontage" for width

    if out["last_sale_amount"] is None:
        out["last_sale_amount"] = _deep_get(raw, "saleAmount", "amount", "salePrice", "price")
    if out["last_sale_date"] is None:
        out["last_sale_date"] = _deep_get(raw, "saleTransDate", "saleDate", "transDate", "date")
    if out["avm_value"] is None:
        out["avm_value"] = _deep_get(raw, "avm", "value", "amount", "estimate", "zestimate")

    out["property_type"] = (raw.get("summary") or {}).get("propclass") if isinstance(raw.get("summary"), dict) else raw.get("propertyType") or raw.get("type")

    # Sale (may be in sale block or summary)
    sale = raw.get("sale") or raw.get("saleAmount") or {}
    if isinstance(sale, dict):
        out["last_sale_amount"] = sale.get("amount") or sale.get("saleAmount") or sale.get("price")
        out["last_sale_date"] = sale.get("saleTransDate") or sale.get("saleDate") or sale.get("date")
    if out["last_sale_amount"] is None and raw.get("saleAmount") is not None:
        out["last_sale_amount"] = raw.get("saleAmount")
    if out["last_sale_date"] is None and raw.get("saleTransDate") is not None:
        out["last_sale_date"] = raw.get("saleTransDate")

    # Sale history (reuse shared parser; backfill last_sale from first record)
    out["sale_history"] = _parse_sale_history(raw)
    if out["sale_history"] and out["last_sale_amount"] is None:
        out["last_sale_amount"] = out["sale_history"][0].get("sale_amount")
    if out["sale_history"] and out["last_sale_date"] is None:
        out["last_sale_date"] = out["sale_history"][0].get("sale_date")

    # AVM (may be in valuation block or avm.amount / avm.calculations)
    val = raw.get("valuation") or raw.get("avm") or {}
    if isinstance(val, dict):
        out["avm_value"] = val.get("avm") or val.get("value") or val.get("amount")
        out["avm_confidence"] = val.get("confidence") or val.get("scr")
        amt = val.get("amount") if isinstance(val.get("amount"), dict) else None
        if amt:
            out["avm_high"] = amt.get("high") or amt.get("High")
            out["avm_low"] = amt.get("low") or amt.get("Low")
        calcs = val.get("calculations") if isinstance(val.get("calculations"), dict) else None
        if calcs:
            out["avm_per_sqft"] = calcs.get("perSizeUnit") or calcs.get("perSizeunit")

    # Location (for geocode / radius searches)
    loc = raw.get("location") or {}
    if isinstance(loc, dict):
        out["latitude"] = loc.get("latitude") or loc.get("Latitude")
        out["longitude"] = loc.get("longitude") or loc.get("Longitude")

    # Assessment (assessed.assdttlvalue, tax.taxamt, tax.taxyear, market.mktttlvalue)
    assess = raw.get("assessment") or {}
    if isinstance(assess, dict):
        assessed_block = assess.get("assessed") or {}
        if isinstance(assessed_block, dict) and (assessed_block.get("assdttlvalue") is not None or assessed_block.get("assdTtlValue") is not None):
            out["assessed_value"] = assessed_block.get("assdttlvalue") or assessed_block.get("assdTtlValue")
        tax_block = assess.get("tax") or {}
        if isinstance(tax_block, dict):
            out["tax_amount"] = tax_block.get("taxamt") or tax_block.get("taxAmt")
            out["tax_year"] = tax_block.get("taxyear") or tax_block.get("taxYear")
        market_block = assess.get("market") or {}
        if isinstance(market_block, dict) and (market_block.get("mktttlvalue") is not None or market_block.get("mktTtlValue") is not None):
            val_mkt = market_block.get("mktttlvalue") or market_block.get("mktTtlValue")
            if val_mkt and float(val_mkt) > 0:
                out["market_value"] = val_mkt

    # Coerce numerics for UI
    for key in ("beds", "baths", "year_built", "tax_year"):
        if out.get(key) is not None:
            try:
                out[key] = int(float(out[key]))
            except (TypeError, ValueError):
                out[key] = None
    for key in ("living_sq_ft", "lot_sq_ft", "lot_depth_ft", "lot_width_ft", "last_sale_amount", "avm_value", "avm_confidence", "assessed_value", "tax_amount", "market_value", "latitude", "longitude", "avm_high", "avm_low", "avm_per_sqft"):
        if out.get(key) is not None:
            try:
                out[key] = float(out[key])
            except (TypeError, ValueError):
                out[key] = None

    return out


def build_rebuild_features_from_property(
    normalized: Dict[str, Any],
    target_living_sq_ft: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Build rebuild-oriented features from a normalized Attom property.
    Use API fields when present; calculate derived values when the API doesn't provide them.
    """
    p = normalized or {}
    # --- API-sourced (pass through) ---
    out: Dict[str, Any] = {
        "full_address": p.get("full_address"),
        "avm_value": p.get("avm_value"),
        "avm_high": p.get("avm_high"),
        "avm_low": p.get("avm_low"),
        "avm_confidence": p.get("avm_confidence"),
        "avm_per_sqft": p.get("avm_per_sqft"),
        "last_sale_amount": p.get("last_sale_amount"),
        "last_sale_date": p.get("last_sale_date"),
        "assessed_value": p.get("assessed_value"),
        "tax_amount": p.get("tax_amount"),
        "tax_year": p.get("tax_year"),
        "market_value": p.get("market_value"),
        "year_built": p.get("year_built"),
        "living_sq_ft": p.get("living_sq_ft"),
        "beds": p.get("beds"),
        "baths": p.get("baths"),
        "property_type": p.get("property_type"),
        "lot_sq_ft": p.get("lot_sq_ft"),
        "attom_id": p.get("attom_id"),
        "latitude": p.get("latitude"),
        "longitude": p.get("longitude"),
    }
    sale_history = p.get("sale_history") or []
    out["sale_count"] = len(sale_history) if isinstance(sale_history, list) else 0

    # --- Calculated: suggested_existing_value (when API doesn't give a single "existing value") ---
    suggested = None
    source = None
    if p.get("avm_value") is not None:
        try:
            suggested = float(p["avm_value"])
            source = "avm"
        except (TypeError, ValueError):
            pass
    if suggested is None and p.get("last_sale_amount") is not None:
        try:
            suggested = float(p["last_sale_amount"])
            source = "last_sale"
        except (TypeError, ValueError):
            pass
    if suggested is None and sale_history and isinstance(sale_history, list) and len(sale_history) > 0:
        first = sale_history[0]
        if isinstance(first, dict) and first.get("sale_amount") is not None:
            try:
                suggested = float(first["sale_amount"])
                source = "sale_history"
            except (TypeError, ValueError):
                pass
    out["suggested_existing_value"] = suggested
    out["suggested_existing_value_source"] = source

    # --- value_per_sqft: use API (avm_per_sqft) when present, else calculate from AVM / living_sq_ft ---
    if p.get("avm_per_sqft") is not None:
        try:
            out["value_per_sqft"] = float(p["avm_per_sqft"])
        except (TypeError, ValueError):
            out["value_per_sqft"] = None
    else:
        out["value_per_sqft"] = None
    if out.get("value_per_sqft") is None and p.get("avm_value") is not None and p.get("living_sq_ft") is not None:
        try:
            avm = float(p["avm_value"])
            sqft = float(p["living_sq_ft"])
            if sqft > 0:
                out["value_per_sqft"] = round(avm / sqft, 2)
        except (TypeError, ValueError):
            pass

    # --- Calculated: gap_to_target_sqft (only when target_living_sq_ft provided) ---
    if target_living_sq_ft is not None and p.get("living_sq_ft") is not None:
        try:
            current = float(p["living_sq_ft"])
            target = float(target_living_sq_ft)
            out["gap_to_target_sqft"] = round(target - current, 2)
        except (TypeError, ValueError):
            out["gap_to_target_sqft"] = None
    else:
        out["gap_to_target_sqft"] = None

    # --- DB-aligned fields (same names as PropertyInfoRow / ParcelFootprintRow for unified use) ---
    out["sold_date"] = p.get("last_sale_date")
    out["sold_price"] = out.get("suggested_existing_value") or p.get("last_sale_amount")
    out["ppsf"] = out.get("value_per_sqft")
    if out["ppsf"] is None and p.get("last_sale_amount") is not None and p.get("living_sq_ft") is not None:
        try:
            amt = float(p["last_sale_amount"])
            sqft = float(p["living_sq_ft"])
            if sqft > 0:
                out["ppsf"] = round(amt / sqft, 2)
        except (TypeError, ValueError):
            pass
    out["property_use_standardized"] = p.get("property_type")
    out["zip_code"] = (p.get("zip") or "").strip() or None
    out["city_name"] = (p.get("city") or "").strip() or None
    out["days_on_market"] = None  # Attom typically doesn't provide
    out["lot_size_sq_ft"] = p.get("lot_sq_ft")
    lot_sq = out.get("lot_size_sq_ft")
    try:
        out["is_valid_dimensions"] = lot_sq is not None and float(lot_sq) > 0
    except (TypeError, ValueError):
        out["is_valid_dimensions"] = False
    out["lot_width_ft"] = p.get("lot_width_ft")   # Attom: lot.frontage
    out["lot_depth_ft"] = p.get("lot_depth_ft")   # Attom: lot.depth
    out["ratio_band"] = None
    has_dims = out.get("lot_width_ft") is not None and out.get("lot_depth_ft") is not None
    out["footprint_notes"] = "From Attom (lot depth/frontage)." if has_dims else ("From Attom; width/depth not available." if (out.get("lot_size_sq_ft") is not None) else None)

    # Estimated buildable footprint (no zoning: use lot area + dimensions when available, else assumed setbacks)
    lot_area = out.get("lot_size_sq_ft")
    lot_w = out.get("lot_width_ft")
    lot_d = out.get("lot_depth_ft")
    if lot_area is not None and isinstance(lot_area, (int, float)) and float(lot_area) > 0:
        build_w, build_d, build_sq, build_notes = estimate_buildable_footprint(
            float(lot_area), lot_width_ft=lot_w, lot_depth_ft=lot_d
        )
        out["buildable_width_ft"] = build_w
        out["buildable_depth_ft"] = build_d
        out["buildable_sq_ft"] = build_sq
        out["buildable_notes"] = build_notes
        target_sq = target_living_sq_ft
        if target_sq is not None and isinstance(target_sq, (int, float)) and build_sq is not None:
            out["fits_target_sqft"] = float(build_sq) >= float(target_sq)
        else:
            out["fits_target_sqft"] = None
    else:
        out["buildable_width_ft"] = None
        out["buildable_depth_ft"] = None
        out["buildable_sq_ft"] = None
        out["buildable_notes"] = "Lot area missing; cannot estimate buildable footprint."
        out["fits_target_sqft"] = None

    return out


_DEFAULT_SETBACKS = {
    "front_setback_ft": 20.0,
    "rear_setback_ft": 20.0,
    "side_setback_ft": 5.0,
}

# Lot-width buckets for density breakdown (ft)
_LOT_WIDTH_BUCKETS = [
    (0,    40,  "< 40 ft"),
    (40,   50,  "40–50 ft"),
    (50,   60,  "50–60 ft"),
    (60,   80,  "60–80 ft"),
    (80,   None, "80 ft +"),
]


def fetch_target_sites_attom(
    zip_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_miles: float = 20.0,
    max_year_built: int = 1975,
    min_living_sq_ft: int = 1100,
    max_living_sq_ft: int = 1700,
    target_build_sq_ft: float = 2700.0,
    front_setback_ft: float = 20.0,
    rear_setback_ft: float = 20.0,
    side_setback_ft: float = 5.0,
    property_type: str = "SINGLE FAMILY RESIDENCE",
    page_size: int = 100,
) -> Dict[str, Any]:
    """
    Find density / incidence of ~50-year-old, ~1,400 sqft homes on buildable lots.

    Uses Attom /property/snapshot filtered by geography + maxYearBuilt + living sqft range.
    For each property:
      - Extracts lot dimensions (width/depth from Attom, or estimated from lot_sq_ft)
      - Calls estimate_buildable_footprint() with default residential setbacks
      - Determines whether target_build_sq_ft fits on the buildable footprint

    Returns:
        {
          "error": str | None,
          "area_label": str,
          "filters": { max_year_built, min/max_living_sq_ft, target_build_sq_ft, setbacks },
          "total_count": int,
          "buildable_count": int,           # fits target_build_sq_ft
          "buildable_pct": float | None,
          "lot_width_distribution": [        # sorted by bucket
            { "bucket": str, "count": int, "buildable_count": int }, ...
          ],
          "lot_depth_p25/p50/p75": float | None,
          "lot_width_p25/p50/p75": float | None,
          "properties": [
            {
              "lat", "lon", "address", "year_built", "living_sq_ft",
              "lot_sq_ft", "lot_width_ft", "lot_depth_ft",
              "buildable_sq_ft", "buildable_width_ft", "buildable_depth_ft",
              "fits_target", "buildable_notes",
              "avm_value",
            }, ...
          ]
        }
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ATTOM_API_KEY not set", "total_count": 0, "properties": []}

    zip_clean = (zip_code or "").strip()
    if zip_clean:
        geo_params = f"postalCode={urllib.parse.quote(zip_clean)}"
        area_label = f"ZIP {zip_clean}"
    else:
        lat = latitude if latitude is not None else _LA_CENTER_LAT
        lon = longitude if longitude is not None else _LA_CENTER_LON
        geo_params = f"latitude={lat}&longitude={lon}&radius={radius_miles}"
        area_label = f"LA area ({lat},{lon} r={radius_miles} mi)"

    base_url = (
        f"{ATTOM_BASE}/property/snapshot"
        f"?{geo_params}"
        f"&maxYearBuilt={max_year_built}"
        f"&minUniversalSize={min_living_sq_ft}"
        f"&maxUniversalSize={max_living_sq_ft}"
        f"&propertyType={urllib.parse.quote(property_type)}"
    )
    _empty = {"error": None, "area_label": area_label, "total_count": 0, "buildable_count": 0, "buildable_pct": None, "lot_width_distribution": [], "properties": [], "filters": _build_filters(max_year_built, min_living_sq_ft, max_living_sq_ft, target_build_sq_ft, front_setback_ft, rear_setback_ft, side_setback_ft)}
    try:
        raw_props = _attom_get_paged(api_key, base_url, total=page_size)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        if e.code == 404:
            return _empty
        return {**_empty, "error": f"Attom API error {e.code}: {body[:200]}"}
    except Exception as e:
        return {**_empty, "error": str(e)}

    out_list: List[Dict[str, Any]] = []
    lot_widths: List[float] = []
    lot_depths: List[float] = []
    buildable_count = 0

    # Bucket accumulators: { bucket_label: [count, buildable_count] }
    bucket_acc: Dict[str, List[int]] = {b[2]: [0, 0] for b in _LOT_WIDTH_BUCKETS}

    for prop in raw_props:
        if not isinstance(prop, dict):
            continue

        # Coordinates
        loc = prop.get("location") or {}
        lat_v = _safe_float(loc.get("latitude") or loc.get("lat")) if isinstance(loc, dict) else None
        lon_v = _safe_float(loc.get("longitude") or loc.get("lng") or loc.get("lon")) if isinstance(loc, dict) else None

        # Address
        addr_block = prop.get("address") or {}
        one_line = (addr_block.get("oneLine") or addr_block.get("line1") or "") if isinstance(addr_block, dict) else ""
        prop_zip = (addr_block.get("postal1") or addr_block.get("postalCode") or "").strip() if isinstance(addr_block, dict) else ""

        # Year built
        summary = prop.get("summary") or {}
        year_built = None
        if isinstance(summary, dict):
            year_built = _safe_int(summary.get("yearbuilt") or summary.get("yearBuilt"))

        # Living sqft
        living_sq_ft = _extract_living_sq_ft(prop)

        # Lot
        lot_block = prop.get("lot") or {}
        lot_sq_ft = None
        lot_width_ft: Optional[float] = None
        lot_depth_ft: Optional[float] = None
        if isinstance(lot_block, dict):
            raw_lotsize2 = lot_block.get("lotsize2") or lot_block.get("lotSize2")
            raw_lotsize1 = lot_block.get("lotsize1") or lot_block.get("lotSize1")
            if raw_lotsize2 is not None:
                lot_sq_ft = _safe_float(raw_lotsize2)
            elif raw_lotsize1 is not None:
                v = _safe_float(raw_lotsize1)
                if v is not None:
                    lot_sq_ft = round(v * 43560, 1)
            lot_depth_ft = _safe_float(lot_block.get("depth") or lot_block.get("lotDepth"))
            lot_width_ft = _safe_float(lot_block.get("frontage") or lot_block.get("lotFrontage"))

        # Attom ID (for bulk AVM join)
        ident = prop.get("identifier") or {}
        attom_id: Optional[str] = None
        if isinstance(ident, dict):
            raw_id = ident.get("obPropId") or ident.get("Id") or ident.get("id")
            attom_id = str(int(raw_id)) if raw_id is not None else None

        # Last sale amount (fallback existing-value proxy)
        sale_block = prop.get("sale") or {}
        last_sale_amount: Optional[float] = None
        if isinstance(sale_block, dict):
            amt_block = sale_block.get("amount") or {}
            if isinstance(amt_block, dict):
                last_sale_amount = _safe_float(amt_block.get("saleamt") or amt_block.get("saleAmt") or amt_block.get("amount"))
            if last_sale_amount is None:
                last_sale_amount = _safe_float(sale_block.get("saleamt") or sale_block.get("saleAmt"))

        # AVM (populated by /property/snapshot only rarely; enriched later by bulk call)
        avm_block = prop.get("avm") or {}
        avm_value = None
        if isinstance(avm_block, dict):
            amt = avm_block.get("amount") or {}
            if isinstance(amt, dict):
                avm_value = _safe_float(amt.get("value") or amt.get("Value"))
            if avm_value is None:
                avm_value = _safe_float(avm_block.get("value") or avm_block.get("Value"))

        # Buildable footprint
        bw, bd, bsq, bnotes = estimate_buildable_footprint(
            lot_sq_ft,
            lot_width_ft=lot_width_ft,
            lot_depth_ft=lot_depth_ft,
            front_setback_ft=front_setback_ft,
            rear_setback_ft=rear_setback_ft,
            side_setback_ft=side_setback_ft,
        )
        fits_target = (bsq is not None and bsq >= target_build_sq_ft)

        if fits_target:
            buildable_count += 1

        # Lot-width bucket
        eff_width = lot_width_ft  # use actual if available
        if eff_width is None and bw is not None:
            # reverse-estimate width from buildable width
            eff_width = bw + 2 * side_setback_ft
        if eff_width is not None:
            lot_widths.append(eff_width)
            for lo, hi, label in _LOT_WIDTH_BUCKETS:
                if hi is None and eff_width >= lo:
                    bucket_acc[label][0] += 1
                    if fits_target:
                        bucket_acc[label][1] += 1
                    break
                elif hi is not None and lo <= eff_width < hi:
                    bucket_acc[label][0] += 1
                    if fits_target:
                        bucket_acc[label][1] += 1
                    break

        # Expose estimated width on the property record too
        if lot_width_ft is None and eff_width is not None:
            lot_width_ft = eff_width

        # Lot depth: use actual if available; fall back to lot_sq_ft / eff_width
        eff_depth = lot_depth_ft
        if eff_depth is None and lot_sq_ft and eff_width and eff_width > 0:
            eff_depth = round(lot_sq_ft / eff_width, 1)
        if eff_depth is not None:
            lot_depths.append(eff_depth)
        # Expose estimated depth on the property record too
        if lot_depth_ft is None and eff_depth is not None:
            lot_depth_ft = eff_depth

        out_list.append({
            "lat": lat_v,
            "lon": lon_v,
            "address": one_line or None,
            "zip_code": prop_zip or None,
            "attom_id": attom_id,
            "year_built": year_built,
            "living_sq_ft": living_sq_ft,
            "lot_sq_ft": lot_sq_ft,
            "lot_width_ft": lot_width_ft,
            "lot_depth_ft": lot_depth_ft,
            "buildable_sq_ft": bsq,
            "buildable_width_ft": bw,
            "buildable_depth_ft": bd,
            "fits_target": fits_target,
            "buildable_notes": bnotes,
            "avm_value": avm_value,         # from /property/snapshot (usually None)
            "last_sale_amount": last_sale_amount,  # fallback existing-value proxy
        })

    total = len(out_list)
    lot_widths.sort()
    lot_depths.sort()

    lot_width_dist = [
        {"bucket": label, "count": bucket_acc[label][0], "buildable_count": bucket_acc[label][1]}
        for _, _, label in _LOT_WIDTH_BUCKETS
        if bucket_acc[label][0] > 0
    ]

    return {
        "error": None,
        "area_label": area_label,
        "filters": _build_filters(max_year_built, min_living_sq_ft, max_living_sq_ft, target_build_sq_ft, front_setback_ft, rear_setback_ft, side_setback_ft),
        "total_count": total,
        "buildable_count": buildable_count,
        "buildable_pct": round(100 * buildable_count / total, 1) if total > 0 else None,
        "lot_width_p25": _percentile(lot_widths, 0.25),
        "lot_width_median": _percentile(lot_widths, 0.5),
        "lot_width_p75": _percentile(lot_widths, 0.75),
        "lot_depth_p25": _percentile(lot_depths, 0.25),
        "lot_depth_median": _percentile(lot_depths, 0.5),
        "lot_depth_p75": _percentile(lot_depths, 0.75),
        "lot_width_distribution": lot_width_dist,
        "properties": out_list,
    }


def _build_filters(max_year_built: int, min_sqft: int, max_sqft: int, target_sq: float,
                   front_setback_ft: float = 20.0, rear_setback_ft: float = 20.0, side_setback_ft: float = 5.0) -> Dict[str, Any]:
    return {
        "max_year_built": max_year_built,
        "min_living_sq_ft": min_sqft,
        "max_living_sq_ft": max_sqft,
        "target_build_sq_ft": target_sq,
        "assumed_setbacks": {
            "front_setback_ft": front_setback_ft,
            "rear_setback_ft": rear_setback_ft,
            "side_setback_ft": side_setback_ft,
        },
    }


def _attom_get(api_key: str, url: str, timeout: int = 30) -> Dict[str, Any]:
    """Make a GET request to Attom API. Returns parsed JSON or raises."""
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "APIKey": api_key},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


_ATTOM_PAGE_MAX = 200  # Attom hard limit per page


def _attom_get_paged(api_key: str, base_url: str, total: int, timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Paginate an Attom snapshot endpoint to collect up to `total` records.
    Appends &pageSize=200&page=N to base_url for each page until we have
    enough records or Attom returns an empty page.
    base_url must NOT already contain pageSize or page params.
    """
    collected: List[Dict[str, Any]] = []
    per_page = min(total, _ATTOM_PAGE_MAX)
    page = 1
    while len(collected) < total:
        url = f"{base_url}&pageSize={per_page}&page={page}"
        try:
            data = _attom_get(api_key, url, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                break  # no more results
            raise
        props = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
        if not isinstance(props, list) or len(props) == 0:
            break
        collected.extend(props)
        if len(props) < per_page:
            break  # last page was partial — no more to fetch
        page += 1
    return collected[:total]


def _percentile(sorted_values: List[float], pct: float) -> Optional[float]:
    """Compute percentile (0–1) from a pre-sorted list using linear interpolation."""
    if not sorted_values:
        return None
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    rank = pct * (n - 1)
    lower = int(rank)
    upper = min(lower + 1, n - 1)
    fraction = rank - lower
    return round(sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower]), 2)


def fetch_new_build_benchmark_attom(
    zip_code: str,
    min_year_built: int = 2020,
    min_ppsf: float = MIN_VALID_PPSF,
    property_type: str = "SINGLE FAMILY RESIDENCE",
    page_size: int = 100,
) -> Dict[str, Any]:
    """
    Calculate new-build benchmark (p25/p50/p75 PPSF, count, DOM) from Attom data.

    Uses Attom /sale/snapshot filtered by postalCode + minYearBuilt (since 2020) to
    get recent new-build sales, then computes PPSF percentiles in this service.

    Comp set: homes built since min_year_built (default 2020, last 5–6 years).
    New builds sell at a premium. If sale_count == 0, that is a negative signal for
    the area.

    Returns:
        {
          "error": str | None,
          "zip_code": str,
          "min_year_built": int,
          "sale_count": int,
          "p25_ppsf": float | None,
          "median_ppsf": float | None,
          "p75_ppsf": float | None,
          "p25_dom": float | None,
          "median_dom": float | None,
          "p75_dom": float | None,
          "has_new_builds": bool,        # False is a negative signal
          "note": str,
        }
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ATTOM_API_KEY not set", "zip_code": zip_code, "sale_count": 0, "has_new_builds": False, "note": "API key not configured."}

    encoded_zip = urllib.parse.quote(zip_code.strip())
    url = (
        f"{ATTOM_BASE}/sale/snapshot"
        f"?postalCode={encoded_zip}"
        f"&minYearBuilt={min_year_built}"
        f"&pageSize={page_size}"
        f"&propertyType={urllib.parse.quote(property_type)}"
    )
    try:
        data = _attom_get(api_key, url)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        if e.code == 404:
            return {"error": None, "zip_code": zip_code, "sale_count": 0, "has_new_builds": False, "note": f"No sales found in ZIP {zip_code}."}
        return {"error": f"Attom API error {e.code}: {body[:200]}", "zip_code": zip_code, "sale_count": 0, "has_new_builds": False, "note": ""}
    except Exception as e:
        return {"error": str(e), "zip_code": zip_code, "sale_count": 0, "has_new_builds": False, "note": ""}

    properties = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
    if not isinstance(properties, list):
        properties = []

    ppsf_values: List[float] = []
    dom_values: List[float] = []

    for prop in properties:
        if not isinstance(prop, dict):
            continue
        # Sale amount
        sale_block = prop.get("sale") or {}
        sale_amt = None
        if isinstance(sale_block, dict):
            amt_block = sale_block.get("amount") or {}
            if isinstance(amt_block, dict):
                sale_amt = _safe_float(amt_block.get("saleamt") or amt_block.get("saleAmt") or amt_block.get("amount"))
            if sale_amt is None:
                sale_amt = _safe_float(sale_block.get("saleamt") or sale_block.get("saleAmt"))
        if sale_amt is None:
            sale_amt = _safe_float(prop.get("saleamt") or prop.get("saleAmt"))

        # Living sqft
        bldg = prop.get("building") or {}
        living_sq_ft = _extract_living_sq_ft(prop) if isinstance(prop, dict) else None

        if sale_amt and sale_amt > 0 and living_sq_ft and living_sq_ft > 0:
            ppsf = sale_amt / living_sq_ft
            if ppsf >= min_ppsf:  # Keep comps above configured PPSF floor.
                ppsf_values.append(round(ppsf, 2))

        # Days on market
        calc_block = (sale_block.get("calculation") or {}) if isinstance(sale_block, dict) else {}
        dom = _safe_float(
            (calc_block.get("daysOnMarket") or calc_block.get("days_on_market"))
            if isinstance(calc_block, dict) else None
        )
        if dom is None:
            dom = _safe_float(prop.get("daysOnMarket") or prop.get("days_on_market"))
        if dom is not None and dom >= 0:
            dom_values.append(dom)

    ppsf_values.sort()
    dom_values.sort()
    sale_count = len(ppsf_values)
    has_new_builds = sale_count > 0
    note = (
        f"{sale_count} new-build sale(s) with PPSF data found in ZIP {zip_code} (year_built ≥ {min_year_built}, PPSF ≥ {round(min_ppsf)})."
        if has_new_builds
        else f"No new-build sales found in ZIP {zip_code} (year_built ≥ {min_year_built}, PPSF ≥ {round(min_ppsf)}). Negative signal for this area."
    )

    return {
        "error": None,
        "zip_code": zip_code,
        "min_year_built": min_year_built,
        "sale_count": sale_count,
        "p25_ppsf": _percentile(ppsf_values, 0.25),
        "median_ppsf": _percentile(ppsf_values, 0.5),
        "p75_ppsf": _percentile(ppsf_values, 0.75),
        "p25_dom": _percentile(dom_values, 0.25),
        "median_dom": _percentile(dom_values, 0.5),
        "p75_dom": _percentile(dom_values, 0.75),
        "has_new_builds": has_new_builds,
        "note": note,
    }


_LA_CENTER_LAT = 34.0522
_LA_CENTER_LON = -118.2437
_LA_DEFAULT_RADIUS_MILES = 20.0


def fetch_new_build_properties_for_map(
    zip_code: Optional[str],
    min_year_built: int = 2020,
    property_type: str = "SINGLE FAMILY RESIDENCE",
    page_size: int = 100,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_miles: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Fetch new-build sale properties from Attom for geographic map plotting.

    Geography selection (in priority order):
      1. zip_code provided → postalCode filter
      2. latitude + longitude provided → lat/lon + radius (default 20 miles)
      3. Neither → defaults to LA center (34.0522, -118.2437) with 20-mile radius

    Uses /sale/snapshot + minYearBuilt. Returns per-property records with
    lat, lon, living_sq_ft, lot_sq_ft, year_built, sale_amt, ppsf, address.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ATTOM_API_KEY not set", "zip_code": zip_code, "property_count": 0, "properties": [], "min_year_built": min_year_built}

    encoded_pt = urllib.parse.quote(property_type)

    zip_clean = (zip_code or "").strip()
    if zip_clean:
        geo_params = f"postalCode={urllib.parse.quote(zip_clean)}"
        area_label = f"ZIP {zip_clean}"
    else:
        lat = latitude if latitude is not None else _LA_CENTER_LAT
        lon = longitude if longitude is not None else _LA_CENTER_LON
        radius = radius_miles if radius_miles is not None else _LA_DEFAULT_RADIUS_MILES
        geo_params = f"latitude={lat}&longitude={lon}&radius={radius}"
        area_label = f"LA area ({lat},{lon} r={radius} mi)"

    url = (
        f"{ATTOM_BASE}/sale/snapshot"
        f"?{geo_params}"
        f"&minYearBuilt={min_year_built}"
        f"&pageSize={page_size}"
        f"&propertyType={encoded_pt}"
    )
    try:
        data = _attom_get(api_key, url)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        if e.code == 404:
            return {"error": None, "zip_code": zip_clean or None, "area_label": area_label, "property_count": 0, "properties": [], "min_year_built": min_year_built}
        return {"error": f"Attom API error {e.code}: {body[:200]}", "zip_code": zip_clean or None, "area_label": area_label, "property_count": 0, "properties": [], "min_year_built": min_year_built}
    except Exception as e:
        return {"error": str(e), "zip_code": zip_clean or None, "area_label": area_label, "property_count": 0, "properties": [], "min_year_built": min_year_built}

    raw_props = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
    if not isinstance(raw_props, list):
        raw_props = []

    out_list: List[Dict[str, Any]] = []
    for prop in raw_props:
        if not isinstance(prop, dict):
            continue

        # Coordinates
        loc = prop.get("location") or {}
        lat = _safe_float(loc.get("latitude") or loc.get("lat")) if isinstance(loc, dict) else None
        lon = _safe_float(loc.get("longitude") or loc.get("lng") or loc.get("lon")) if isinstance(loc, dict) else None
        if lat is None or lon is None:
            continue  # Can't map without coordinates

        # Address
        addr_block = prop.get("address") or {}
        one_line = (addr_block.get("oneLine") or addr_block.get("line1") or "") if isinstance(addr_block, dict) else ""

        # Year built
        summary = prop.get("summary") or {}
        year_built = None
        if isinstance(summary, dict):
            year_built = _safe_int(summary.get("yearbuilt") or summary.get("yearBuilt"))
        if year_built is None:
            year_built = _safe_int(prop.get("yearbuilt") or prop.get("yearBuilt"))

        # Living sqft
        living_sq_ft = _extract_living_sq_ft(prop)

        # Lot dimensions
        lot_block = prop.get("lot") or {}
        lot_sq_ft = None
        lot_width_ft = None
        lot_depth_ft = None
        if isinstance(lot_block, dict):
            raw_lotsize = lot_block.get("lotsize2") or lot_block.get("lotSize2") or lot_block.get("lotsize1")
            if raw_lotsize is not None:
                v = _safe_float(raw_lotsize)
                if v is not None:
                    # lotsize1 is acres, lotsize2 is sq ft
                    lot_sq_ft = v if (lot_block.get("lotsize2") or lot_block.get("lotSize2")) else v * 43560
            lot_depth_ft = _safe_float(lot_block.get("depth") or lot_block.get("lotDepth"))
            lot_width_ft = _safe_float(lot_block.get("frontage") or lot_block.get("lotFrontage"))

        # Sale amount
        sale_block = prop.get("sale") or {}
        sale_amt = None
        if isinstance(sale_block, dict):
            amt_block = sale_block.get("amount") or {}
            if isinstance(amt_block, dict):
                sale_amt = _safe_float(amt_block.get("saleamt") or amt_block.get("saleAmt") or amt_block.get("amount"))
            if sale_amt is None:
                sale_amt = _safe_float(sale_block.get("saleamt") or sale_block.get("saleAmt"))
        if sale_amt is None:
            sale_amt = _safe_float(prop.get("saleamt") or prop.get("saleAmt"))

        ppsf = None
        if sale_amt and sale_amt > 0 and living_sq_ft and living_sq_ft > 0:
            raw_ppsf = sale_amt / living_sq_ft
            if raw_ppsf >= MIN_VALID_PPSF:
                ppsf = round(raw_ppsf, 2)

        out_list.append({
            "lat": lat,
            "lon": lon,
            "address": one_line or None,
            "year_built": year_built,
            "living_sq_ft": living_sq_ft,
            "lot_sq_ft": lot_sq_ft,
            "lot_width_ft": lot_width_ft,
            "lot_depth_ft": lot_depth_ft,
            "sale_amt": sale_amt,
            "ppsf": ppsf,
        })

    return {
        "error": None,
        "zip_code": zip_clean or None,
        "area_label": area_label,
        "min_year_built": min_year_built,
        "property_count": len(out_list),
        "properties": out_list,
    }


def fetch_bulk_avm_by_zip(
    zip_code: str,
    page_size: int = 200,
) -> Dict[str, Any]:
    """
    Fetch bulk AVM values for a ZIP code via Attom /attomavm/detail?postalCode=...

    Returns a dict keyed by attom_id (str) → avm_value (float), plus metadata.
    One API call covers the whole ZIP — much cheaper than per-property calls.

    Returns:
        {
          "error": str | None,
          "zip_code": str,
          "avm_count": int,
          "avm_by_id": { attom_id: avm_value, ... },  # keyed by str(obPropId)
        }
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ATTOM_API_KEY not set", "zip_code": zip_code, "avm_count": 0, "avm_by_id": {}}

    encoded_zip = urllib.parse.quote(zip_code.strip())
    url = f"{ATTOM_BASE}/attomavm/detail?postalCode={encoded_zip}&pageSize={page_size}"
    try:
        data = _attom_get(api_key, url)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        if e.code == 404:
            return {"error": None, "zip_code": zip_code, "avm_count": 0, "avm_by_id": {}}
        return {"error": f"Attom AVM API error {e.code}: {body[:200]}", "zip_code": zip_code, "avm_count": 0, "avm_by_id": {}}
    except Exception as e:
        return {"error": str(e), "zip_code": zip_code, "avm_count": 0, "avm_by_id": {}}

    raw_props = (data.get("property") or data.get("properties") or []) if isinstance(data, dict) else []
    if not isinstance(raw_props, list):
        raw_props = []

    avm_by_id: Dict[str, float] = {}
    for prop in raw_props:
        if not isinstance(prop, dict):
            continue
        # Attom ID
        ident = prop.get("identifier") or {}
        raw_id = ident.get("obPropId") or ident.get("Id") or ident.get("id") if isinstance(ident, dict) else None
        if raw_id is None:
            continue
        attom_id = str(int(raw_id))

        # AVM value
        avm_block = prop.get("avm") or {}
        avm_val = None
        if isinstance(avm_block, dict):
            amt = avm_block.get("amount") or {}
            if isinstance(amt, dict):
                avm_val = _safe_float(amt.get("value") or amt.get("Value"))
            if avm_val is None:
                avm_val = _safe_float(avm_block.get("value") or avm_block.get("Value"))
        if avm_val is not None and avm_val > 0:
            avm_by_id[attom_id] = avm_val

    return {
        "error": None,
        "zip_code": zip_code,
        "avm_count": len(avm_by_id),
        "avm_by_id": avm_by_id,
    }


def fetch_product_mix_attom(
    zip_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_miles: float = 20.0,
    max_year_built: int = 1975,
    min_living_sq_ft: int = 1100,
    max_living_sq_ft: int = 1700,
    target_sizes: Optional[List[int]] = None,
    front_setback_ft: float = 20.0,
    rear_setback_ft: float = 20.0,
    side_setback_ft: float = 5.0,
    benchmark_zip_code: Optional[str] = None,
    min_year_built_comps: int = 2020,
    min_ppsf_comps: float = MIN_VALID_PPSF,
    page_size: int = 200,
) -> Dict[str, Any]:
    """
    Product mix optimizer: sweep across multiple target home sizes to find the
    optimal tradeoff between quantity (buildable count) and value creation.

    Steps:
      1. Fetch all target-site properties once (with buildable footprint per property).
      2. Fetch new-build PPSF benchmark for the area (ZIP or radius).
      3. Sweep across target_sizes in-memory:
           - buildable_count  = properties where buildable_sq_ft >= size
           - new_build_value  = size × median_ppsf  (estimated sale price of new build)
           - avg_existing_avm = mean AVM of buildable properties (when available)
           - avg_value_accretion = new_build_value − avg_existing_avm
           - total_value_created = avg_value_accretion × buildable_count
      4. Mark the "optimal" size = highest total_value_created.

    Returns:
        {
          "error": str | None,
          "area_label": str,
          "total_scanned": int,
          "new_build_benchmark": { median_ppsf, p25_ppsf, p75_ppsf, sale_count, has_new_builds, note },
          "products": [
            {
              "target_sqft": int,
              "buildable_count": int,
              "buildable_pct": float | None,
              "new_build_value": float | None,       # size × median_ppsf
              "avg_existing_avm": float | None,
              "avm_coverage": int,                   # # of properties with AVM data
              "avg_value_accretion": float | None,
              "total_value_created": float | None,
              "is_optimal": bool,                    # highest total_value_created
            }, ...
          ],
          "filters": { ... },
        }
    """
    if target_sizes is None:
        target_sizes = [2100, 2400, 2700, 3000, 3500]
    target_sizes = sorted(set(int(s) for s in target_sizes if s > 0))

    # ── 1. Fetch all target-site properties (target_build_sq_ft=1 = get all) ──
    sites = fetch_target_sites_attom(
        zip_code=zip_code,
        latitude=latitude,
        longitude=longitude,
        radius_miles=radius_miles,
        max_year_built=max_year_built,
        min_living_sq_ft=min_living_sq_ft,
        max_living_sq_ft=max_living_sq_ft,
        target_build_sq_ft=1.0,
        front_setback_ft=front_setback_ft,
        rear_setback_ft=rear_setback_ft,
        side_setback_ft=side_setback_ft,
        page_size=page_size,
    )
    if sites.get("error"):
        return {"error": sites["error"], "products": [], "total_scanned": 0}

    properties = sites.get("properties") or []
    area_label = sites.get("area_label", "")

    # ── 2. New-build PPSF benchmark ───────────────────────────────────────────
    bmark_zip = (benchmark_zip_code or "").strip() or (zip_code or "").strip()
    if bmark_zip:
        benchmark = fetch_new_build_benchmark_attom(
            bmark_zip,
            min_year_built=min_year_built_comps,
            min_ppsf=min_ppsf_comps,
        )
    else:
        benchmark = {
            "median_ppsf": None, "p25_ppsf": None, "p75_ppsf": None,
            "sale_count": 0, "has_new_builds": False,
            "note": "No ZIP provided for new-build benchmark; PPSF not available.",
        }

    median_ppsf = benchmark.get("median_ppsf")

    # ── 2b. Bulk AVM join — one call per ZIP, keyed by attom_id ──────────────
    # /property/snapshot rarely returns AVM; /attomavm/detail?postalCode= does.
    # Fall back chain per property: bulk_avm → last_sale_amount → None.
    avm_zip = bmark_zip or (zip_code or "").strip()
    bulk_avm: Dict[str, float] = {}
    avm_source = "none"
    if avm_zip:
        bulk_result = fetch_bulk_avm_by_zip(avm_zip, page_size=page_size)
        if not bulk_result.get("error") and bulk_result.get("avm_count", 0) > 0:
            bulk_avm = bulk_result["avm_by_id"]
            avm_source = "bulk_avm"

    # Enrich property records with resolved existing value
    for p in properties:
        if p.get("avm_value") and p["avm_value"] > 0:
            p["existing_value"] = p["avm_value"]
            p["existing_value_source"] = "snapshot_avm"
        elif bulk_avm and p.get("attom_id") and p["attom_id"] in bulk_avm:
            p["existing_value"] = bulk_avm[p["attom_id"]]
            p["existing_value_source"] = "bulk_avm"
        elif p.get("last_sale_amount") and p["last_sale_amount"] > 0:
            p["existing_value"] = p["last_sale_amount"]
            p["existing_value_source"] = "last_sale"
        else:
            p["existing_value"] = None
            p["existing_value_source"] = None

    ev_sources = {p["existing_value_source"] for p in properties if p.get("existing_value_source")}

    # ── 3. Sweep across target sizes ─────────────────────────────────────────
    product_rows = []
    for size in target_sizes:
        buildable = [
            p for p in properties
            if p.get("buildable_sq_ft") is not None and p["buildable_sq_ft"] >= size
        ]
        count = len(buildable)
        total = len(properties)
        buildable_pct = round(100.0 * count / total, 1) if total > 0 else None

        ev_vals = [p["existing_value"] for p in buildable if p.get("existing_value") and p["existing_value"] > 0]
        avg_avm = round(sum(ev_vals) / len(ev_vals)) if ev_vals else None

        new_build_value = round(size * median_ppsf) if median_ppsf else None
        avg_accretion = (round(new_build_value - avg_avm) if (new_build_value is not None and avg_avm is not None) else None)
        total_value = round(avg_accretion * count) if (avg_accretion is not None and count > 0) else None

        product_rows.append({
            "target_sqft": size,
            "buildable_count": count,
            "buildable_pct": buildable_pct,
            "new_build_value": new_build_value,
            "avg_existing_value": avg_avm,
            "existing_value_coverage": len(ev_vals),
            "avg_value_accretion": avg_accretion,
            "total_value_created": total_value,
            "is_optimal": False,
        })

    # ── 4. Mark optimal ───────────────────────────────────────────────────────
    scored = [r for r in product_rows if r["total_value_created"] is not None]
    if scored:
        best = max(scored, key=lambda r: r["total_value_created"])
        best["is_optimal"] = True
    elif product_rows:
        # No AVM data — fall back: mark highest buildable_count as "most quantity"
        best_qty = max(product_rows, key=lambda r: r["buildable_count"])
        best_qty["is_optimal"] = True

    export_properties = []
    for p in properties:
        export_properties.append({
            "attom_id": p.get("attom_id"),
            "address": p.get("address"),
            "zip_code": p.get("zip_code"),
            "lat": p.get("lat"),
            "lon": p.get("lon"),
            "year_built": p.get("year_built"),
            "living_sq_ft": p.get("living_sq_ft"),
            "lot_sq_ft": p.get("lot_sq_ft"),
            "lot_width_ft": p.get("lot_width_ft"),
            "lot_depth_ft": p.get("lot_depth_ft"),
            "buildable_width_ft": p.get("buildable_width_ft"),
            "buildable_depth_ft": p.get("buildable_depth_ft"),
            "buildable_sq_ft": p.get("buildable_sq_ft"),
            "buildable_notes": p.get("buildable_notes"),
            "fits_target": p.get("fits_target"),
            "avm_value": p.get("avm_value"),
            "last_sale_amount": p.get("last_sale_amount"),
            "existing_value": p.get("existing_value"),
            "existing_value_source": p.get("existing_value_source"),
        })

    return {
        "error": None,
        "area_label": area_label,
        "total_scanned": len(properties),
        "benchmark_zip_code": bmark_zip or None,
        "min_year_built_comps": min_year_built_comps,
        "min_ppsf_comps": min_ppsf_comps,
        "existing_value_sources": sorted(ev_sources),  # e.g. ["bulk_avm", "last_sale"]
        "new_build_benchmark": {
            "median_ppsf": benchmark.get("median_ppsf"),
            "p25_ppsf": benchmark.get("p25_ppsf"),
            "p75_ppsf": benchmark.get("p75_ppsf"),
            "sale_count": benchmark.get("sale_count", 0),
            "has_new_builds": benchmark.get("has_new_builds", False),
            "note": benchmark.get("note", ""),
        },
        "products": product_rows,
        "properties": export_properties,
        "filters": sites.get("filters"),
    }


def fetch_value_accretion_heatmap_attom(
    zip_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_miles: float = 20.0,
    max_year_built: int = 1975,
    min_living_sq_ft: int = 1100,
    max_living_sq_ft: int = 1700,
    target_build_sq_ft: float = 2700.0,
    front_setback_ft: float = 20.0,
    rear_setback_ft: float = 20.0,
    side_setback_ft: float = 5.0,
    min_year_built_comps: int = 2020,
    min_ppsf_comps: float = MIN_VALID_PPSF,
    page_size: int = 200,
) -> Dict[str, Any]:
    """
    Value accretion heat map for a single target home size.

    Key insight: neighboring properties share the same new-build market value,
    so we look up PPSF once per ZIP (not per property) and apply it uniformly.
    Two adjacent houses → same new-build value from ZIP benchmark → no per-property comps needed.

    Steps:
      1. Fetch all target-site properties (with buildable footprint + zip_code).
      2. Collect unique ZIPs from property records.
      3. Parallel-fetch new-build PPSF for each unique ZIP (ThreadPoolExecutor).
      4. Per property: value_accretion = (zip_ppsf × target_sqft) − existing_value.
      5. Return per-property list for map + per-ZIP summary table.

    Returns:
        {
          "error": str | None,
          "area_label": str,
          "target_build_sq_ft": float,
          "total_count": int,
          "zip_benchmarks": [               # baseline heat map, one row per ZIP
            { "zip_code", "median_ppsf", "p25_ppsf", "p75_ppsf",
              "new_build_value", "sale_count", "has_new_builds",
              "property_count" },
            ...
          ],
          "properties": [
            { "lat", "lon", "address", "zip_code",
              "existing_value", "existing_value_source",
              "new_build_value",           # zip_ppsf × target_sqft
              "value_accretion",           # new_build_value - existing_value
              "buildable_sq_ft", "fits_target",
              "year_built", "living_sq_ft",
            }, ...
          ],
        }
    """
    # ── 1. Fetch target-site properties ──────────────────────────────────────
    sites = fetch_target_sites_attom(
        zip_code=zip_code,
        latitude=latitude,
        longitude=longitude,
        radius_miles=radius_miles,
        max_year_built=max_year_built,
        min_living_sq_ft=min_living_sq_ft,
        max_living_sq_ft=max_living_sq_ft,
        target_build_sq_ft=target_build_sq_ft,
        front_setback_ft=front_setback_ft,
        rear_setback_ft=rear_setback_ft,
        side_setback_ft=side_setback_ft,
        page_size=page_size,
    )
    if sites.get("error"):
        return {"error": sites["error"], "properties": [], "zip_benchmarks": []}

    properties = sites.get("properties") or []
    area_label = sites.get("area_label", "")

    # ── 2. Collect unique ZIPs ────────────────────────────────────────────────
    unique_zips = sorted({p["zip_code"] for p in properties if p.get("zip_code")})

    # Fall back: if no ZIP extracted from properties (radius mode), use the search ZIP
    search_zip = (zip_code or "").strip()
    if not unique_zips and search_zip:
        unique_zips = [search_zip]

    # ── 3. Bulk AVM join (same as product mix) ───────────────────────────────
    avm_zip = search_zip or (unique_zips[0] if unique_zips else "")
    bulk_avm: Dict[str, float] = {}
    if avm_zip:
        bulk_result = fetch_bulk_avm_by_zip(avm_zip, page_size=min(page_size, 200))
        if not bulk_result.get("error"):
            bulk_avm = bulk_result.get("avm_by_id", {})

    for p in properties:
        if p.get("avm_value") and p["avm_value"] > 0:
            p["existing_value"] = p["avm_value"]
            p["existing_value_source"] = "snapshot_avm"
        elif bulk_avm and p.get("attom_id") and p["attom_id"] in bulk_avm:
            p["existing_value"] = bulk_avm[p["attom_id"]]
            p["existing_value_source"] = "bulk_avm"
        elif p.get("last_sale_amount") and p["last_sale_amount"] > 0:
            p["existing_value"] = p["last_sale_amount"]
            p["existing_value_source"] = "last_sale"
        else:
            p["existing_value"] = None
            p["existing_value_source"] = None

    # ── 4. Parallel new-build PPSF lookup per ZIP ─────────────────────────────
    def _get_zip_benchmark(z: str) -> tuple:
        result = fetch_new_build_benchmark_attom(
            z,
            min_year_built=min_year_built_comps,
            min_ppsf=min_ppsf_comps,
        )
        return z, result

    zip_ppsf: Dict[str, Optional[float]] = {}
    zip_benchmark_rows: List[Dict[str, Any]] = []

    if unique_zips:
        with ThreadPoolExecutor(max_workers=min(len(unique_zips), 8)) as pool:
            futures = {pool.submit(_get_zip_benchmark, z): z for z in unique_zips}
            for future in as_completed(futures):
                z, result = future.result()
                ppsf = result.get("median_ppsf")
                zip_ppsf[z] = ppsf
                zip_benchmark_rows.append({
                    "zip_code": z,
                    "median_ppsf": ppsf,
                    "p25_ppsf": result.get("p25_ppsf"),
                    "p75_ppsf": result.get("p75_ppsf"),
                    "new_build_value": round(target_build_sq_ft * ppsf) if ppsf else None,
                    "sale_count": result.get("sale_count", 0),
                    "has_new_builds": result.get("has_new_builds", False),
                    "property_count": sum(1 for p in properties if p.get("zip_code") == z),
                })
        zip_benchmark_rows.sort(key=lambda r: (-(r["median_ppsf"] or 0)))

    # ── 5. Per-property value accretion ──────────────────────────────────────
    out_properties = []
    for p in properties:
        pz = p.get("zip_code") or ""
        local_ppsf = zip_ppsf.get(pz) or (zip_ppsf.get(search_zip) if search_zip else None)
        new_build_value = round(target_build_sq_ft * local_ppsf) if local_ppsf else None
        existing_val = p.get("existing_value")
        accretion = round(new_build_value - existing_val) if (new_build_value is not None and existing_val is not None) else None

        out_properties.append({
            "lat": p.get("lat"),
            "lon": p.get("lon"),
            "address": p.get("address"),
            "zip_code": pz or None,
            "year_built": p.get("year_built"),
            "living_sq_ft": p.get("living_sq_ft"),
            "lot_sq_ft": p.get("lot_sq_ft"),
            "lot_width_ft": p.get("lot_width_ft"),
            "lot_depth_ft": p.get("lot_depth_ft"),
            "buildable_sq_ft": p.get("buildable_sq_ft"),
            "fits_target": p.get("fits_target"),
            "existing_value": existing_val,
            "existing_value_source": p.get("existing_value_source"),
            "local_ppsf": local_ppsf,
            "new_build_value": new_build_value,
            "value_accretion": accretion,
        })

    return {
        "error": None,
        "area_label": area_label,
        "target_build_sq_ft": target_build_sq_ft,
        "total_count": len(out_properties),
        "zip_benchmarks": zip_benchmark_rows,
        "properties": out_properties,
        "filters": sites.get("filters"),
    }


def fetch_rebuild_features(
    address: str,
    target_living_sq_ft: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Fetch rebuild-oriented features from Attom by address. Uses property/detail API;
    builds features with API fields first, then calculated values when needed.
    Returns { "error": str | None, "rebuild_features": dict }.
    """
    result = fetch_property_detail(address.strip())
    if result.get("error"):
        return {
            "error": result["error"],
            "rebuild_features": None,
        }
    prop = result.get("property")
    if not prop:
        return {
            "error": None,
            "rebuild_features": None,
        }
    features = build_rebuild_features_from_property(prop, target_living_sq_ft)
    return {"error": None, "rebuild_features": features}
