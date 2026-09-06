from pathlib import Path
import yaml

def test_strategy_library_is_research_not_watchlist():
    data=yaml.safe_load(Path("config/strategies.yaml").read_text(encoding="utf-8"))
    assert "not a fixed trading universe" in data.get("note", "").lower()
