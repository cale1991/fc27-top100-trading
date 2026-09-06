from __future__ import annotations

from pathlib import Path

import yaml


TASK_MAP: dict[str, tuple[str, tuple]] = {
    "ea_news_fc26": ("fc27.collect_ea_news", (26,)),
    "ea_news_fc27": ("fc27.collect_ea_news", (27,)),
    "futzip_movers": ("fc27.collect_futzip_feed", ("movers",)),
    "futzip_new": ("fc27.collect_futzip_feed", ("new",)),
    "futzip_sbc": ("fc27.collect_futzip_feed", ("sbc",)),
    "thecoinprinter_recent": ("fc27.collect_thecoinprinter_recent", ()),
    "futdb_universe": ("fc27.sync_futdb_universe", ()),
    "futdb_reference_prices": ("fc27.collect_futdb_reference_prices", ()),
    "parse_futbin_catalogue": ("fc27.collect_parse_futbin_catalogue", ()),
    "parse_futbin_hot": ("fc27.collect_parse_futbin_hot", ()),
    "opportunity_discovery": ("fc27.run_opportunity_discovery", ()),
    "attention_reallocation": ("fc27.reallocate_attention", ()),
    "community_reputation": ("fc27.recalculate_trader_reputation", ()),
    "strategy_backtests": ("fc27.run_strategy_backtests", ()),
    "strategy_trader_reputation": ("fc27.recalculate_strategy_trader_reputation", ()),
}


def load_polling_config(path: str | Path = "config/polling.yaml") -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_beat_schedule(path: str | Path = "config/polling.yaml") -> dict[str, dict]:
    """Translate enabled polling jobs into Celery Beat entries.

    Jobs that require a not-yet-connected primary market provider intentionally have no
    TASK_MAP entry and therefore cannot accidentally run under a misleading cadence.
    """
    config = load_polling_config(path)
    schedule: dict[str, dict] = {}
    for key, job in config.get("jobs", {}).items():
        if not job.get("enabled", False):
            continue
        task = TASK_MAP.get(key)
        if task is None:
            continue
        task_name, args = task
        schedule[f"{key}-every-{job['every_seconds']}s"] = {
            "task": task_name,
            "schedule": float(job["every_seconds"]),
            "args": args,
            "options": {"queue": job["queue"]},
        }
    return schedule
