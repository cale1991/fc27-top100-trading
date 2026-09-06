from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TimeSplit:
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    test_start: datetime
    test_end: datetime


def validate_split(split: TimeSplit) -> None:
    if not (
        split.train_start < split.train_end <= split.validation_start < split.validation_end
        <= split.test_start < split.test_end
    ):
        raise ValueError("time split is not strictly chronological")
