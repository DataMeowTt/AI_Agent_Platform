from __future__ import annotations

import argparse
import json

from src.pipelines.batch import run_all_analytics


def _parse_cluster_years(values: list[str] | None) -> list[int] | None:
    if not values:
        return None

    years: list[int] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            years.append(int(part))
    return years


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run analytics batch jobs.")
    parser.add_argument(
        "--target",
        default="postgres",
        choices=["postgres"],
        help="Analytics write target. Only postgres is supported in this chunk.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan analytics work without reading from or writing to the database.",
    )
    parser.add_argument("--table", help="Optional gold table name filter.")
    parser.add_argument("--indicator", help="Optional indicator code filter.")
    parser.add_argument(
        "--skip-clusters",
        action="store_true",
        help="Skip clustering tasks.",
    )
    parser.add_argument(
        "--cluster-year",
        action="append",
        help="Cluster target year. Repeat or pass comma-separated values.",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=5,
        help="Number of clusters for clustering tasks.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    result = run_all_analytics(
        target=args.target,
        dry_run=args.dry_run,
        table=args.table,
        indicator=args.indicator,
        skip_clusters=args.skip_clusters,
        cluster_years=_parse_cluster_years(args.cluster_year),
        n_clusters=args.n_clusters,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
