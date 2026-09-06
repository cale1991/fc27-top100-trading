RESTRICTED_AUTOMATED_SOURCES = {
    "futbin": {
        "reason": "Terms prohibit web scraping/data mining without written permission.",
        "mode": "manual_validation_only",
    },
    "futgg": {
        "reason": "Terms prohibit automated access and ML/AI training without prior written consent.",
        "mode": "manual_validation_only",
    },
    "futwiz": {
        "reason": "No automation permission/API contract has been established for this project.",
        "mode": "manual_validation_only",
    },
}


def assert_automation_allowed(source_key: str) -> None:
    if source_key in RESTRICTED_AUTOMATED_SOURCES:
        item = RESTRICTED_AUTOMATED_SOURCES[source_key]
        raise PermissionError(f"{source_key}: {item['reason']}")
