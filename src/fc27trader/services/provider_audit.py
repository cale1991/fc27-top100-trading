from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import ProviderAuditRecord


def seed_provider_audit(session: Session, config_path: str | Path = "config/provider_audit_fc26.yaml") -> int:
    payload = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    checked_at = datetime.fromisoformat(str(payload["checked_at"]))
    inserted = 0
    for provider_key, item in (payload.get("providers") or {}).items():
        existing = session.scalar(select(ProviderAuditRecord).where(
            ProviderAuditRecord.provider_key == provider_key,
            ProviderAuditRecord.checked_at == checked_at,
        ))
        if existing is not None:
            continue
        session.add(ProviderAuditRecord(
            provider_key=provider_key,
            checked_at=checked_at,
            tier=str(item.get("tier") or "D"),
            integration_status=str(item.get("integration_status") or "NOT_VERIFIED"),
            capabilities_json=item.get("capabilities") or [],
            markets_json=item.get("markets") or {},
            access_json=item.get("access") or {},
            rights_json=item.get("rights") or {},
            economics_json=item.get("economics") or {},
            source_urls_json=item.get("source_urls") or [],
            evidence_notes=item.get("evidence_notes"),
            blockers_json=item.get("blockers") or [],
            metadata_json={"seeded_from": str(config_path), "game_year": 26},
        ))
        inserted += 1
    session.flush()
    return inserted
