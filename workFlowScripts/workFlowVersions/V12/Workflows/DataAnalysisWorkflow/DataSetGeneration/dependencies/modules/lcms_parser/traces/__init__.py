"""Modules to deal with experimental traces (TICs, UV, etc.)."""

from dependencies.modules.lcms_parser.traces.analog import (
    AnalogTrace,
    AnalogTracePeak,
)
from dependencies.modules.lcms_parser.traces.ion import (
    TICTrace,
    TICTracePeak,
)

__all__ = [
    "TICTrace",
    "TICTracePeak",
    "AnalogTrace",
    "AnalogTracePeak",
]
