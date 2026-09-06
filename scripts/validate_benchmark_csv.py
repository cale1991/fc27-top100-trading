#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter

from fc27trader.validation.io import load_basket, load_benchmark_csv


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--basket", default="config/validation_basket_fc26.yaml")
    args = ap.parse_args()
    cards = load_basket(args.basket)
    quotes = load_benchmark_csv(args.csv)
    card_map = {c.key: c for c in cards}
    missing = [c.key for c in cards if c.key not in quotes]
    counts = Counter(card_map[k].category.value for k in quotes if k in card_map)
    print(f"benchmark_rows={len(quotes)}/{len(cards)}")
    print(f"categories={dict(counts)}")
    if missing:
        print("missing:")
        for key in missing:
            print(f"- {key}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
