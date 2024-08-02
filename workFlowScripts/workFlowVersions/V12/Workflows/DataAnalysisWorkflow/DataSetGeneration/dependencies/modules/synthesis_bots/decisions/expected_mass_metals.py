"""Decision maker for having expected m/z value(s) with multiple metals."""

import logging
from pathlib import Path

from dependencies.modules.lcms_parser import (
    ExpectedResults,
    MassSpectrumExperimentalHit,
    WatersRawFile,
)

from dependencies.modules.synthesis_bots.utils.constants import SETTINGS

logger = logging.getLogger(__name__)


def main(
    raw_path: Path,
    expected_mz: ExpectedResults,
) -> tuple[bool, list[MassSpectrumExperimentalHit]]:
    """Make the decisions."""
    criteria = SETTINGS["workflows"]["decision"]
    logger.info(f"Reading results in {raw_path.name}.")
    print(f'the file is {raw_path.name}')
    ms_file = WatersRawFile(raw_path)
    hits = ms_file.identify_hits(
        expected_results=expected_mz,
        mode="ES+",
        atol=SETTINGS["defaults"]["MS"]["peak_match_tolerance"],
        tic_peak_params=SETTINGS["defaults"]["MS"]["tic_peak_params"],
        ms_peak_params=SETTINGS["defaults"]["MS"]["ms_peak_params"],
    )

    logger.info(f"Found {len(hits)} hits.")
    logger.info("Checking for multiple metals in the hits.")

    multiple_metals = {hit.formula: 0 for hit in hits}

    for hit in hits:
        metals_no = int(hit.formula.split("_")[1][1])
        if metals_no >= criteria["metals_mz"][0]:
            logger.info(f"Multiple metal ions found for {hit.formula}.")
            multiple_metals[hit.formula] += 1

    pruned_hits = []
    for hit in hits:
        metals_no = int(hit.formula.split("_")[1][1])
        if metals_no >= criteria["metals_mz"][0]:
            if multiple_metals[hit.formula] >= criteria["metals_mz"][1]:
                pruned_hits.append(hit)
                logger.info(f"Hit for {hit.formula} with {hit.mz_value}.")
            else:
                pass
        else:
            logger.info(f"Hit for {hit.formula} with {hit.mz_value}.")
            pruned_hits.append(hit)

    if len(pruned_hits) > 0:
        logger.info(
            f"Expected mass criterion PASSED with {len(pruned_hits)} hits."
        )
        return True, pruned_hits

    else:
        return False, pruned_hits
