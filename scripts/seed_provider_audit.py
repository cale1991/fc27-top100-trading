from fc27trader.db.session import SessionLocal
from fc27trader.services.provider_audit import seed_provider_audit

with SessionLocal() as session:
    inserted = seed_provider_audit(session)
    session.commit()
print(f"provider audit seeded: {inserted} new records")
