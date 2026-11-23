"""CLI entry point for MacroPulse data ingestion.

Usage:
    python -m macropulse.ingest all
    python -m macropulse.ingest prices --since 2023-01-01
    python -m macropulse.ingest events
"""

import argparse
import datetime
import json
import sys

from macropulse.ingest.pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="MacroPulse Data Ingestion CLI")
    parser.add_argument(
        "target",
        choices=["indicators", "vintages", "prices", "events", "fomc", "all"],
        help="Target dataset to ingest",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Optional ISO start date (YYYY-MM-DD) for incremental ingestion",
    )

    args = parser.parse_args()
    since_date = datetime.date.fromisoformat(args.since) if args.since else None

    pipeline = IngestionPipeline()
    try:
        if args.target == "all":
            res = pipeline.ingest_all(since=since_date)
            print("Completed ingestion for ALL targets:")
            print(json.dumps(res, indent=2))
        elif args.target == "indicators":
            inserted, skipped = pipeline.ingest_indicator_observations()
            print(f"Indicators: {inserted} inserted, {skipped} skipped.")
        elif args.target == "vintages":
            inserted, skipped = pipeline.ingest_vintages()
            print(f"Vintages: {inserted} inserted, {skipped} skipped.")
        elif args.target == "prices":
            inserted, skipped = pipeline.ingest_prices(since=since_date)
            print(f"Prices: {inserted} inserted, {skipped} skipped.")
        elif args.target in ("events", "fomc"):
            inserted, skipped = pipeline.ingest_events()
            print(f"Events: {inserted} inserted, {skipped} skipped.")
    except Exception as e:
        print(f"Ingestion failed with error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
