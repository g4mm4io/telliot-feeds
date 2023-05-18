from datetime import datetime
from datetime import timezone
from typing import Optional
from typing import Tuple
from typing import TypeVar


T = TypeVar("T")

# A Time-stamped value tuple
DataPoint = Tuple[T, datetime]

# An optional time-stamped value tuple
OptionalDataPoint = Tuple[Optional[T], Optional[datetime]]

# An optional weighted and time-stamped value tuple
OptionalWeightedDataPoint = Tuple[Optional[T], Optional[datetime], Optional[float]]


def datetime_now_utc() -> datetime:
    """A helper function to get the timestamp for "now" """
    return datetime.now(timezone.utc)
