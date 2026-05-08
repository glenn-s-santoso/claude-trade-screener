#!/usr/bin/env python3
"""Unified coin screener — dispatches to pluggable sources."""

import argparse
import json
import logging
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    parser = argparse.ArgumentParser(description="Fetch and filter top crypto coins")
    parser.add_argument(
        "--source",
        default="cmc",
        choices=["cmc", "santiment", "coinglass"],
        help="Screening source (default: cmc)",
    )
    parser.add_argument("--limit", type=int, default=20, help="Max coins to return (default: 20)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    # Import here so we only load the source we need
    from sources import SOURCES

    source_cls = SOURCES[args.source]
    source = source_cls()
    coins = source.fetch(limit=args.limit)

    output_file = OUTPUT_DIR / f"screening_results_{args.source}.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [c.to_dict() for c in coins]
    output_file.write_text(json.dumps(records, indent=2))
    print(f"Saved {len(records)} coins to {output_file}")

    for i, c in enumerate(coins, 1):
        ratio_str = f"  ratio={c.vol_mcap_ratio:.4f}" if c.vol_mcap_ratio is not None else ""
        change_str = f"  24h={c.percent_change_24h:+.1f}%" if c.percent_change_24h is not None else ""
        print(f"  {i:2}. {c.symbol:>8}{ratio_str}{change_str}")


if __name__ == "__main__":
    main()
