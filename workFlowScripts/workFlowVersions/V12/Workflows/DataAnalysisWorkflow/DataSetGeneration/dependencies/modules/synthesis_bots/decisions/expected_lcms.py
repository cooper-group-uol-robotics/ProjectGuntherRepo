"""Decision maker for having expected m/z value(s) and peaks in LC trace."""

import logging
from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
from lcms_parser import (
    AnalogTracePeak,
    ExpectedResults,
    MassSpectrumExperimentalHit,
    WatersRawFile,
)

from synthesis_bots.utils.constants import SETTINGS

logger = logging.getLogger(__name__)
plt.style.use("synthesis_bots.utils.mpl")


def main(
    raw_path: Path,
    expected_mz: ExpectedResults,
    threshold: float = SETTINGS["defaults"]["MS"]["analog_peak_threshold"],
) -> tuple[
    bool, list[list[MassSpectrumExperimentalHit]], list[AnalogTracePeak]
]:
    """Make the decisions."""
    logger.info(f"Reading results in {raw_path.name}.")
    ms_file = WatersRawFile(raw_path)
    analog = ms_file.get_analog_trace()
    lc_peaks = analog.get_peaks(
        height=SETTINGS["defaults"]["MS"]["analog_peaks_params"]["height"],
        distance=SETTINGS["defaults"]["MS"]["analog_peaks_params"]["distance"],
        solvent_front=SETTINGS["defaults"]["MS"]["solvent_front"],
        run_end=SETTINGS["defaults"]["MS"]["lc_run_end"],
        rel_height=SETTINGS["defaults"]["MS"]["integral_rel_height"],
    )

    experimental_hits = []
    ms_criterion = False
    for peak in lc_peaks:
        if peak.integral >= threshold:
            logger.info(
                f"Peak at {peak.time.total_seconds()/60:.2f} min: "
                f"relative area is {peak.integral:.2f}. Analysing."
            )
            ms_time = timedelta(
                seconds=(
                    peak.time.total_seconds()
                    + SETTINGS["defaults"]["MS"]["lc_ms_flowpath"]
                )
            )
            logger.info(
                f"Analysing MS peak at {ms_time.total_seconds()/60:.2f} min."
            )

            hits = ms_file.identify_hits(
                expected_results=expected_mz,
                mode="ES+",
                atol=SETTINGS["defaults"]["MS"]["peak_match_tolerance"],
                direct_injection=False,
                time=ms_time,
                ms_peak_params=SETTINGS["defaults"]["MS"]["ms_peak_params"],
            )

            if len(hits) > 0:
                experimental_hits.append(hits)
                ms_criterion = True
            else:
                experimental_hits.append([])
            logger.info(f"Found {len(hits)} hits.")

            for hit in hits:
                logger.info(f"Hit for {hit.formula} with {hit.mz_value}.")
        else:
            experimental_hits.append([])
            logger.info(
                f"Peak at {peak.time.total_seconds()/60:.2f} min: "
                f"relative area is {peak.integral:.2f}. Dismissing."
            )

    if ms_criterion:
        logger.info("Expected mass criterion PASSED.")
        return True, experimental_hits, lc_peaks

    else:
        return False, experimental_hits, lc_peaks
