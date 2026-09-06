#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path
PATH = Path("data/validation/provider_prequalification_2026-09-04.csv")

def main() -> int:
    rows=list(csv.DictReader(PATH.open(encoding="utf-8")))
    print("provider\tclassified_roles\thot_reference_status\teffective_staleness_evidence")
    for r in rows:
        print(f"{r['provider']}\t{r.get('classified_roles','')}\t{r.get('hot_reference_status','')}\t{r['effective_staleness_evidence']}")
    hot=[r for r in rows if r.get('hot_reference_status')=='qualified']
    print(f"\nqualified_hot_reference_sources={len(hot)}")
    print("HOT_REFERENCE availability is informational; it is not a global project gate")
    return 0
if __name__ == "__main__": raise SystemExit(main())
