from __future__ import annotations

import gzip
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import boto3

from fc27trader.collectors.base import RawObservation
from fc27trader.settings import Settings


@dataclass(slots=True)
class StoredRaw:
    checksum_sha256: str
    storage_uri: str
    payload_size: int


class RawStore:
    def put(self, observation: RawObservation) -> StoredRaw:
        raise NotImplementedError


class FileRawStore(RawStore):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, observation: RawObservation) -> StoredRaw:
        digest = hashlib.sha256(observation.body).hexdigest()
        stamp = observation.observed_at.strftime("%Y/%m/%d/%H")
        ct = (observation.content_type or "").lower()
        suffix = ".json.gz" if "json" in ct else (".xml.gz" if "xml" in ct or "rss" in ct else ".html.gz")
        path = self.root / observation.source_key / observation.source_kind / stamp / f"{digest}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with gzip.open(path, "wb", compresslevel=6) as handle:
                handle.write(observation.body)
        return StoredRaw(digest, path.resolve().as_uri(), len(observation.body))


class S3RawStore(RawStore):
    def __init__(self, settings: Settings) -> None:
        if not settings.raw_s3_bucket:
            raise ValueError("RAW_S3_BUCKET is required for S3 raw store")
        self.bucket = settings.raw_s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.raw_s3_endpoint_url,
            region_name=settings.raw_s3_region,
            aws_access_key_id=settings.raw_s3_access_key_id,
            aws_secret_access_key=settings.raw_s3_secret_access_key,
        )

    def put(self, observation: RawObservation) -> StoredRaw:
        digest = hashlib.sha256(observation.body).hexdigest()
        stamp = observation.observed_at.strftime("%Y/%m/%d/%H")
        ct = (observation.content_type or "").lower()
        suffix = ".json.gz" if "json" in ct else (".xml.gz" if "xml" in ct or "rss" in ct else ".html.gz")
        key = f"raw/{observation.source_key}/{observation.source_kind}/{stamp}/{digest}{suffix}"
        body = gzip.compress(observation.body, compresslevel=6)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/gzip",
            Metadata={"sha256": digest},
        )
        return StoredRaw(digest, f"s3://{self.bucket}/{key}", len(observation.body))


def build_raw_store(settings: Settings) -> RawStore:
    if settings.raw_store_mode.lower() == "s3":
        return S3RawStore(settings)
    return FileRawStore(settings.raw_store_path)
