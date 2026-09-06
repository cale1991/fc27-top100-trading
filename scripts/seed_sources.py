from sqlalchemy import select

from fc27trader.db.models import Source
from fc27trader.db.session import SessionLocal

SOURCES = [
    dict(key="futzip", name="FUTZIP", source_class="public_feed", automation_policy="allowed_public_rss", training_policy="provider_context_with_provenance", terms_url="https://futzip.com/feeds", metadata_json={"roles":["content","market_context"],"market_semantics":"rss_unspecified"}),
    dict(key="ea_official", name="EA SPORTS FC Official", source_class="official", automation_policy="allowed_public_html", training_policy="allowed_for_facts_and_events", terms_url="https://www.ea.com/legal", metadata_json={"roles":["content"]}),
    dict(key="futbin", name="FUTBIN", source_class="community", automation_policy="prohibited_without_written_permission", training_policy="manual_validation_only", terms_url="https://www.futbin.com/tos", metadata_json={"roles":["manual_benchmark"]}),
    dict(key="futgg", name="FUT.GG", source_class="community", automation_policy="prohibited_without_written_permission", training_policy="prohibited_without_written_consent", terms_url="https://stormstrike.gg/terms", metadata_json={"roles":["manual_benchmark"]}),
    dict(key="futwiz", name="FUTWIZ", source_class="community", automation_policy="permission_required", training_policy="manual_validation_only", terms_url="https://www.futwiz.com/privacy/", metadata_json={"roles":["manual_benchmark"]}),
    dict(key="futdb", name="FUT-DB", source_class="api", automation_policy="api_key_supported", training_policy="verify_account_terms", terms_url="https://fut-db.com/terms", metadata_json={"roles":["metadata","reference","historical"],"price_access":"premium"}),
    dict(key="parse_futbin", name="Parse.bot FUTBIN wrapper", source_class="commercial_structured_api", automation_policy="optional_authenticated_api", training_policy="reference_with_provenance", terms_url="https://parse.bot/marketplace/1b6234f9-0dfb-4cca-99b4-2d6d37aec6a7/futbin-com-api", metadata_json={"roles":["metadata","reference","content"],"enabled_by_default":False,"upstream":"futbin","official_futbin_api":False}),
    dict(key="thecoinprinter", name="The Coin Printer", source_class="api", automation_policy="approved_partner_api_key", training_policy="verify_plan_terms", terms_url="https://www.thecoinprinter.com/terms", metadata_json={"roles":["metadata","reference","historical"],"price_access":"partner_key"}),
]

with SessionLocal() as session:
    for item in SOURCES:
        if not session.scalar(select(Source).where(Source.key == item["key"])):
            session.add(Source(**item, enabled=True))
    session.commit()
print("sources seeded")
