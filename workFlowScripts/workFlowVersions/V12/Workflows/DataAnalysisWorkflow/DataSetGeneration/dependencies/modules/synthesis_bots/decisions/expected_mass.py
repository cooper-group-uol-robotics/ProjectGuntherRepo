"""Decision maker for having expected m/z value(s)."""

import logging
from pathlib import Path

from lcms_parser import (
    ExpectedResults,
    MassSpectrumExperimentalHit,
    WatersRawFile,
)

from synthesis_bots.utils.constants import SETTINGS

logger = logging.getLogger(__name__)


def main(
    raw_path: Path,
    expected_mz: ExpectedResults,
) -> tuple[bool, list[MassSpectrumExperimentalHit]]:
    """Make the decisions."""
    logger.info(f"Reading results in {raw_path.name}.")
    ms_file = WatersRawFile(raw_path)
    hits = ms_file.identify_hits(
        expected_results=expected_mz,
        mode="ES+",
        atol=SETTINGS["defaults"]["MS"]["peak_match_tolerance"],
        tic_peak_params=SETTINGS["defaults"]["MS"]["tic_peak_params"],
        ms_peak_params=SETTINGS["defaults"]["MS"]["ms_peak_params"],
    )

    logger.info(f"Found {len(hits)} hits.")

    for hit in hits:
        logger.info(f"Hit for {hit.formula} with {hit.mz_value}.")

    if len(hits) > 0:
        logger.info("Expected mass criterion PASSED.")
        return True, hits

    else:
        return False, hits
