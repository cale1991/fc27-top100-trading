from pathlib import Path

from fc27trader.scheduler.schedules import build_beat_schedule


def test_only_enabled_mapped_jobs_are_scheduled(tmp_path: Path):
    config = tmp_path / "polling.yaml"
    config.write_text(
        """
jobs:
  ea_news_fc26:
    enabled: true
    queue: content
    every_seconds: 120
  thecoinprinter_recent:
    enabled: false
    queue: reference
    every_seconds: 120
  market_hot:
    enabled: true
    queue: market_hot
    every_seconds: 120
""".strip()
    )
    schedule = build_beat_schedule(config)
    assert list(schedule) == ["ea_news_fc26-every-120s"]
    assert schedule["ea_news_fc26-every-120s"]["task"] == "fc27.collect_ea_news"
