#!/usr/bin/env python3
from __future__ import annotations

from fc27trader.validation.io import load_provider_catalog


def main() -> None:
    catalog = load_provider_catalog("config/provider_catalog_fc26.yaml")
    print("provider\tpc\tterms\tdocumented_freshness\trate_limit\tcost")
    for p in catalog.values():
        print(
            f"{p.key}\t{p.pc_supported}\t{p.terms_state.value}\t"
            f"{p.documented_freshness or '-'}\t{p.documented_rate_limit or '-'}\t{p.cost or '-'}"
        )


if __name__ == "__main__":
    main()
