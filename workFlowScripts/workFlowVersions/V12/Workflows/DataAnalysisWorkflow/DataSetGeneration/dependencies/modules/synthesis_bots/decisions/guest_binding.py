"""Decision maker for comparing if NMR spectra are the same (or similar)."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def main(
    test_nmr: list[float],
    reference_nmr: list[float],
    shift_threshold: float,
) -> tuple[bool, list[float]]:
    """Make the decisions."""
    test_nmr_peaks = np.array(test_nmr)
    ref_nmr_peaks = np.array(reference_nmr)
    hg_bound = False
    trigger_peaks = []
    # Check if there are peaks in the reference that have shifted.
    for peak in ref_nmr_peaks:
        if not np.isclose(test_nmr_peaks, peak, atol=shift_threshold).any():
            logger.info(f"Reference peak at {peak:.02f} is different.")
            hg_bound = True
            trigger_peaks.append(peak)
    return hg_bound, trigger_peaks
