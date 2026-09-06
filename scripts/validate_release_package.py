from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(rb"(?im)^(FUTDB_API_KEY|THECOINPRINTER_API_KEY|PARSE_API_KEY|X_USER_ACCESS_TOKEN)[ \t]*=[ \t]*([^\r\n]*)$"),
    re.compile(rb"tcp_[A-Za-z0-9-]{20,}"),
]

REQUIRED_FILES = {
    "scripts/seed_strategies.py",
    "scripts/collect_once.py",
    "scripts/realdata_status.py",
    "migrations/env.py",
    "migrations/versions/0008_fc26_multisource_multimarket.py",
    "src/fc27trader/db/alembic_bootstrap.py",
    "src/fc27trader/db/json_safe.py",
    "src/fc27trader/collectors/futzip.py",
    "src/fc27trader/collectors/parse_futbin.py",
    "src/fc27trader/services/futzip_ingestion.py",
    "src/fc27trader/services/parse_futbin_ingestion.py",
    "src/fc27trader/services/card_identity.py",
    "tests/test_parse_futbin_r2_regression.py",
    "src/fc27trader/services/cross_market_verification.py",
    "scripts/phase2_runtime_check.ps1",
    "config/provider_audit_fc26.yaml",
    "docs/FC26_REAL_MARKET_PHASE2_2026-09-04.md",
    ".env.example",
    "infra/sql/bootstrap.sql",
}


def _strip_root(name: str) -> str:
    parts = Path(name).parts
    if parts and parts[0] == "fc27-top100-trading":
        return str(Path(*parts[1:])).replace("\\", "/")
    return str(Path(name)).replace("\\", "/")


def validate_zip(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as zf:
        members = {_strip_root(n): n for n in zf.namelist() if not n.endswith("/")}
        missing = sorted(REQUIRED_FILES - set(members))
        if missing:
            errors.append(f"missing required release files: {', '.join(missing)}")
            return errors

        def read(rel: str) -> str:
            return zf.read(members[rel]).decode("utf-8")

        seed = read("scripts/seed_strategies.py")
        if "seed_strategy_library" not in seed:
            errors.append("strategy seed does not call seed_strategy_library")
        if re.search(r"\bseed_strategy_research\b", seed):
            errors.append("obsolete seed_strategy_research is present in packaged strategy seed")

        env = read("migrations/env.py")
        if "ensure_alembic_version_capacity(connection)" not in env:
            errors.append("Alembic environment does not widen version_num before migrations")

        bootstrap_py = read("src/fc27trader/db/alembic_bootstrap.py")
        match = re.search(r"ALEMBIC_VERSION_LENGTH\s*=\s*(\d+)", bootstrap_py)
        width = int(match.group(1)) if match else 0
        revision_ids: list[str] = []
        for rel, actual in members.items():
            if rel.startswith("migrations/versions/") and rel.endswith(".py"):
                txt = zf.read(actual).decode("utf-8")
                m = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', txt, re.MULTILINE)
                if m:
                    revision_ids.append(m.group(1))
        longest = max((len(x) for x in revision_ids), default=0)
        if width < max(64, longest):
            errors.append(f"Alembic version_num width {width} is too small for revision length {longest}")

        bootstrap_sql = read("infra/sql/bootstrap.sql")
        if "alembic_version" not in bootstrap_sql or "VARCHAR(255)" not in bootstrap_sql.upper():
            errors.append("PostgreSQL bootstrap does not pre-create/widen alembic_version to VARCHAR(255)")

        phase2 = read("migrations/versions/0008_fc26_multisource_multimarket.py")
        if "0007_fc26_real_market_phase1" not in phase2 or "market_segments" not in phase2:
            errors.append("Phase-2 migration does not cleanly descend from Phase 1 / seed market segments")
        env_example = read(".env.example")
        if "PARSE_API_KEY=" not in env_example or "PARSE_FUTBIN_ENABLED=false" not in env_example:
            errors.append("Parse/FUTBIN must ship disabled by default with a blank key placeholder")
        if re.search(r"PARSE_API_KEY=\S+", env_example):
            errors.append(".env.example contains a populated Parse API key")

        runtime = read("scripts/phase2_runtime_check.ps1")
        for required in (
            'Wait-HttpReady "API" "http://localhost:8080/health"',
            'Invoke-RequiredNative "Application smoke test"',
            'Invoke-RequiredNative "Required FUTZIP collection: $feed"',
            'if ($script:Failures.Count -gt 0)',
            'exit 1',
            'Mode = "Auto"',
        ):
            if required not in runtime:
                errors.append(f"runtime gate missing required failure/readiness behavior: {required}")
        if "Phase 2 runtime check complete" in runtime:
            errors.append("runtime gate still contains the old false-success completion message")
        parse_ingest = read("src/fc27trader/services/parse_futbin_ingestion.py")
        for required in (
            "_normalize_single_position",
            "_parse_position_metadata",
            "with session.begin_nested()",
            "parse_position_raw",
        ):
            if required not in parse_ingest:
                errors.append(f"Parse/FUTBIN r2 ingestion fix missing required behavior: {required}")
        identity = read("src/fc27trader/services/card_identity.py")
        if "Card.primary_position == primary_position" in identity:
            errors.append("card identity still depends on provider position metadata")
        r2_test = read("tests/test_parse_futbin_r2_regression.py")
        if "CAMCDM, RM, CM, 1" not in r2_test:
            errors.append("packaged tests are missing the live Parse/FUTBIN composite-position regression fixture")

        json_safe = read("src/fc27trader/db/json_safe.py")
        for required in ("datetime", "date", "Decimal", "Enum", "isoformat"):
            if required not in json_safe:
                errors.append(f"JSON-safe persistence helper missing {required} support")

        # Secrets must never ship. .env.example is allowed only with blank placeholders.
        forbidden_envs = [rel for rel in members if Path(rel).name == ".env"]
        if forbidden_envs:
            errors.append(f"release contains credential env file(s): {', '.join(forbidden_envs)}")
        for rel, actual in members.items():
            if not rel.endswith((".py", ".yaml", ".yml", ".json", ".toml", ".md", ".txt", ".env.example")):
                continue
            data = zf.read(actual)
            for pattern in SECRET_PATTERNS:
                for match in pattern.finditer(data):
                    value = match.group(match.lastindex or 0).strip()
                    if b"=" in match.group(0) and value in {b"", b"<blank>", b"changeme", b"your_key_here"}:
                        continue
                    if rel.endswith(".env.example") and b"=" in match.group(0) and value == b"":
                        continue
                    # Key assignments with a non-empty value are always forbidden.
                    errors.append(f"possible provider credential in {rel}")
                    break
                if errors and errors[-1].startswith("possible provider credential"):
                    break

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip", type=Path)
    args = parser.parse_args()
    errors = validate_zip(args.zip)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {args.zip.name} install-regression package checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
