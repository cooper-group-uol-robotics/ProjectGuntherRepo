"""Decision maker for comparing if NMR spectra are the same (or similar)."""

import logging
from pathlib import Path
from typing import Optional

import dtw
import matplotlib.pyplot as plt
import numpy as np
from bruker.api.topspin import PhysicalRange

from synthesis_bots.utils.nmr.processing import NMRExperiment

logger = logging.getLogger(__name__)
plt.style.use("synthesis_bots.utils.mpl")


def main(
    test_nmr: NMRExperiment,
    reference_nmr: NMRExperiment,
    distance_threshold: float,
    ppm_range: tuple[float, float] = (-2, 12),
    archive_path: Optional[Path] = None,
) -> bool:
    """Make the decisions."""
    logger.info("Starting spectrum comparison routine.")
    pr = PhysicalRange(min(ppm_range), max(ppm_range))
    logger.info(f"Test NMR from {test_nmr.path}.")
    logger.info(f"Reference NMR from {reference_nmr.path}.")
    test_np = np.array(
        test_nmr.nmr_data.getSpecDataPoints(physRange=[pr])["dataPoints"],
        dtype=np.double,
    )
    ref_np = np.array(
        reference_nmr.nmr_data.getSpecDataPoints(physRange=[pr])["dataPoints"],
        dtype=np.double,
    )
    ppm_np = np.linspace(
        max(ppm_range),
        min(ppm_range),
        num=len(ref_np),
    )

    # Conversion of indices to ppm values.
    spacing = round(len(ref_np) / 11)
    idxs = np.linspace(0, len(ref_np), num=len(ref_np))
    ppms = []
    for ppm in ppm_np:
        ppms.append(f"{ppm:.1f}")

    # Min-max scaling for thresholding.
    test_np = (test_np - test_np.min()) / (test_np.max() - test_np.min())
    ref_np = (ref_np - ref_np.min()) / (ref_np.max() - ref_np.min())
    logger.debug(
        "After minimisation test values are between:"
        f" {test_np.min()} and {test_np.max()}."
    )
    logger.debug(
        "After minimisation reference values are between:"
        f" {ref_np.min()} and {ref_np.max()}."
    )
    # Prune < 0.05 intensity to remove noise.
    ref_pruned = []

    for point in ref_np:
        if point > 0.05:
            ref_pruned.append(point)
        else:
            ref_pruned.append(0)
    ref_np_pruned = np.array(ref_pruned)

    test_pruned = []

    for point in test_np:
        if point > 0.05:
            test_pruned.append(point)
        else:
            test_pruned.append(0)
    test_np_pruned = np.array(test_pruned)

    logger.debug(
        "Reference and test dataset lengths: "
        f"{len(ref_np_pruned)} and {len(test_np_pruned)}."
    )

    alignment = dtw.dtw(
        ref_np_pruned,
        test_np_pruned,
        keep_internals=True,
    )

    logger.info(
        "DTW alignment distance is "
        f"{alignment.distance:.1f}."  # type: ignore
    )

    if archive_path is not None:
        plot = alignment.plot(type="twoway", offset=1.5)
        plot.set_xlabel("Chemical shift / ppm")
        plot.set_xticks(idxs[::spacing])
        plot.set_xticklabels(ppms[::spacing])
        plot.set_ylabel("")
        plot.set_title(
            "Distance between spectra: "
            f"{alignment.distance:.1f}"  # type: ignore
        )
        fig = plot.get_figure()
        ax1, ax2 = fig.get_axes()  # type: ignore
        ax1.set_yticks([])
        ax1.set_ylabel("")
        ax2.set_yticks([])
        fig.savefig(archive_path)  # type: ignore

    if alignment.distance < distance_threshold:  # type: ignore
        logger.info("Replication: SUCCESS.")
        return True

    else:
        logger.info("Replication: FAIL.")
        return False
