from __future__ import annotations

import csv, json
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy.orm import Session
from fc27trader.db.models import HistoricalImportBatch

SUPPORTED_FORMATS={"csv","json"}

def create_import_batch(session: Session, *, provider_key: str, source_format: str, source_uri: str | None,
                        game_year: int, market_segment_id=None, native_historical: bool=True,
                        reconstructed: bool=False, checksum_sha256: str | None=None) -> HistoricalImportBatch:
    fmt=source_format.lower()
    if fmt not in SUPPORTED_FORMATS: raise ValueError(f"unsupported historical format: {source_format}")
    row=HistoricalImportBatch(provider_key=provider_key, source_format=fmt, source_uri=source_uri,
        imported_at=datetime.now(UTC), game_year=game_year, market_segment_id=market_segment_id,
        native_historical=native_historical, reconstructed=reconstructed, rows_seen=0, rows_written=0,
        rows_quarantined=0, checksum_sha256=checksum_sha256, metadata_json={})
    session.add(row); session.flush(); return row

def read_rows(path: str | Path, source_format: str):
    p=Path(path); fmt=source_format.lower()
    if fmt=="csv":
        with p.open(newline='',encoding='utf-8') as f: yield from csv.DictReader(f)
    elif fmt=="json":
        data=json.loads(p.read_text(encoding='utf-8'))
        yield from (data if isinstance(data,list) else data.get("rows",[]))
    else: raise ValueError(fmt)
