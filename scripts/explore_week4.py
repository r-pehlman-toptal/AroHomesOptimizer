#!/usr/bin/env python3
"""
Week 4 exploratory analysis: submarket distributions (PPSF by city, DOM by city, summary table).

Produces 2–3 charts/tables from city_year (gold) or analytics city×year MV.
Run from project root with DB_URL set. Optional: matplotlib for charts (saves to scripts/out/week4_*.png).
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass

from sqlalchemy import text

from src.db.connection import get_engine

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def run_query(conn, sql: str, params=None):
    if pd is None:
        result = conn.execute(text(sql), params or {})
        return [dict(row._mapping) for row in result]
    df = pd.read_sql(text(sql), conn, params=params or {})
    return df


def main() -> int:
    try:
        engine = get_engine()
    except RuntimeError as e:
        print(f"DB not configured: {e}", file=sys.stderr)
        return 1

    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(exist_ok=True)

    with engine.connect() as conn:
        # Prefer city_year (gold); fallback to analytics MV (no DOM in MV).
        try:
            df = run_query(conn, """
                SELECT city, year AS sale_year, transaction_count,
                       median_price_per_sqft AS median_ppsf,
                       median_days_on_market AS median_dom
                FROM city_year
                WHERE year >= 2020
                ORDER BY city, year
            """)
        except Exception:
            try:
                df = run_query(conn, """
                    SELECT city_name AS city, sale_year, total_sales AS transaction_count,
                           median_ppsf, NULL AS median_dom
                    FROM analytics.mv_agg_city_year_metrics
                    WHERE sale_year >= 2020
                    ORDER BY city_name, sale_year
                """)
            except Exception as e:
                print(f"Could not load city-year data: {e}", file=sys.stderr)
                return 1

        if pd is not None:
            if df.empty:
                print("No city-year data (empty result).", file=sys.stderr)
                return 0
            # Table: latest year summary by city
            latest_year = df["sale_year"].max()
            summary = df.loc[df["sale_year"] == latest_year].sort_values("median_ppsf", ascending=False)
            print("\n--- Submarket summary (latest year", int(latest_year), ") ---")
            print(summary.to_string(index=False))

            if HAS_MATPLOTLIB:
                # Chart 1: Median PPSF by city over years
                fig, ax = plt.subplots(figsize=(10, 5))
                for city in summary["city"].unique()[:6]:
                    sub = df[df["city"] == city]
                    ax.plot(sub["sale_year"], sub["median_ppsf"], marker="o", label=city, markersize=4)
                ax.set_xlabel("Year")
                ax.set_ylabel("Median PPSF ($/sf)")
                ax.set_title("Median PPSF by submarket (city)")
                ax.legend(loc="best", fontsize=8)
                ax.grid(True, alpha=0.3)
                fig.tight_layout()
                fig.savefig(out_dir / "week4_ppsf_by_city.png", dpi=120)
                plt.close(fig)
                print("Saved", out_dir / "week4_ppsf_by_city.png")

                # Chart 2: Median DOM by city over years (if available)
                if "median_dom" in df.columns and df["median_dom"].notna().any():
                    fig2, ax2 = plt.subplots(figsize=(10, 5))
                    for city in summary["city"].unique()[:6]:
                        sub = df[df["city"] == city]
                        if sub["median_dom"].notna().any():
                            ax2.plot(sub["sale_year"], sub["median_dom"], marker="o", label=city, markersize=4)
                    ax2.set_xlabel("Year")
                    ax2.set_ylabel("Median DOM (days)")
                    ax2.set_title("Median days on market by submarket (city)")
                    ax2.legend(loc="best", fontsize=8)
                    ax2.grid(True, alpha=0.3)
                    fig2.tight_layout()
                    fig2.savefig(out_dir / "week4_dom_by_city.png", dpi=120)
                    plt.close(fig2)
                    print("Saved", out_dir / "week4_dom_by_city.png")

                # Chart 3: Transaction volume by city over years
                fig3, ax3 = plt.subplots(figsize=(10, 5))
                for city in summary["city"].unique()[:6]:
                    sub = df[df["city"] == city]
                    ax3.plot(sub["sale_year"], sub["transaction_count"], marker="o", label=city, markersize=4)
                ax3.set_xlabel("Year")
                ax3.set_ylabel("Transaction count")
                ax3.set_title("Sales volume by submarket (city)")
                ax3.legend(loc="best", fontsize=8)
                ax3.grid(True, alpha=0.3)
                fig3.tight_layout()
                fig3.savefig(out_dir / "week4_volume_by_city.png", dpi=120)
                plt.close(fig3)
                print("Saved", out_dir / "week4_volume_by_city.png")
        else:
            # No pandas: list of dicts
            print("\n--- City-year rows (sample) ---")
            rows = df[:15] if isinstance(df, list) else df.head(15).to_dict("records")
            for row in rows:
                print(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
