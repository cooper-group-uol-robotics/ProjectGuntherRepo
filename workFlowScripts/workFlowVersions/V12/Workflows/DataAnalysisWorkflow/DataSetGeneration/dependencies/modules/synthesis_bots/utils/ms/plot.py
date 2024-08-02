"""Plot MS and LCMS traces."""

import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
from dependencies.modules.lcms_parser import (
    AnalogTracePeak,
    WatersRawFile,
)

from dependencies.modules.synthesis_bots.utils.constants import SETTINGS

logger = logging.getLogger(__name__)
plt.style.use("dependencies.modules.synthesis_bots.utils.mpl")


def plot_ms(
    raw_path: Path,
    ms_time: Optional[timedelta] = None,
    mz_limits: Optional[tuple[float, float]] = None,
):
    """
    Plot MS spectrum.

    Parameters
    ----------
    raw_path
        A Path to the Waters .RAW file.
    ms_time
        Time at with the MS spectrum should be plotted.

    Returns
    -------
        Matplotlib Figure and Axes.

    """
    ms_file = WatersRawFile(raw_path)

    if ms_time is None:
        trace = ms_file.get_trace(mode="ES+")
        tic_peaks = trace.get_peaks(
            **SETTINGS["defaults"]["MS"]["tic_peak_params"]
        )
        ms_time = tic_peaks[0].time

    spectrum = ms_file.get_mass_spectrum(mode="ES+", time=ms_time)
    fig, ax = plt.subplots(figsize=(16.5, 3.5))

    scaled_int = spectrum.intensities / max(spectrum.intensities)
    threshold = SETTINGS["defaults"]["MS"]["ms_peak_params"]["height"]

    if mz_limits is None:
        mz_limits = (250, 1000)

    ax.vlines(
        x=spectrum.masses,
        ymax=scaled_int,
        ymin=0,
        linewidth=0.8,
        color="#0072B2",
    )
    ax.axhline(y=threshold, linestyle="--")
    ax.text(
        max(mz_limits),
        threshold + 0.02,
        "INTENSITY THRESHOLD",
        size="smaller",
        horizontalalignment="right",
        verticalalignment="bottom",
        color=ax.lines[0].get_color(),
    )

    ax.set_xlim(min(mz_limits), max(mz_limits))

    ax.set_ylabel("Rel. Intensity / A.U.")
    ax.set_xlabel("Mass-to-charge ratio")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return fig, ax


def plot_lc(
    raw_path: Path,
    lc_peaks: Optional[list[AnalogTracePeak]] = None,
):
    """
    Plot LC chromatogram.

    Parameters
    ----------
    raw_path
        A Path to the Waters .RAW file.
    ms_time
        Time at with the MS spectrum should be plotted.

    Returns
    -------
        Matplotlib Figure and Axes.

    """
    ms_file = WatersRawFile(raw_path)
    analog = ms_file.get_analog_trace()

    fig, ax = plt.subplots(figsize=(16.5, 3.5))
    ax.plot(
        analog.times[
            : analog.get_scan_index(SETTINGS["defaults"]["MS"]["lc_run_end"])
        ],
        analog.intensities[
            : analog.get_scan_index(SETTINGS["defaults"]["MS"]["lc_run_end"])
        ],
        linewidth=2.5,
        color="k",
    )

    if lc_peaks is None:
        lc_peaks = analog.get_peaks(
            height=SETTINGS["defaults"]["MS"]["analog_peaks_params"]["height"],
            distance=SETTINGS["defaults"]["MS"]["analog_peaks_params"][
                "distance"
            ],
            solvent_front=SETTINGS["defaults"]["MS"]["solvent_front"],
            run_end=SETTINGS["defaults"]["MS"]["lc_run_end"],
            rel_height=SETTINGS["defaults"]["MS"]["integral_rel_height"],
        )

    for peak in lc_peaks:
        lhs_idx = analog.get_scan_index(peak.lhs)
        rhs_idx = analog.get_scan_index(peak.rhs)

        ax.fill_between(
            analog.times[lhs_idx:rhs_idx],
            peak.relative_height,
            analog.intensities[lhs_idx:rhs_idx],
        )

    ax.axvline(SETTINGS["defaults"]["MS"]["solvent_front"])
    ax.axvline(SETTINGS["defaults"]["MS"]["lc_run_end"])
    ax.set_xlabel("Retention time / min")
    ax.set_ylabel("Rel. Intensity")
    ax.text(
        SETTINGS["defaults"]["MS"]["solvent_front"] - 0.01,
        0.5,
        "ANALYSIS",
        horizontalalignment="right",
        verticalalignment="center",
        rotation="vertical",
        size="smaller",
        color=ax.lines[1].get_color(),
    )

    ax.text(
        SETTINGS["defaults"]["MS"]["solvent_front"] + 0.02,
        0.5,
        "START",
        horizontalalignment="left",
        verticalalignment="center",
        rotation="vertical",
        size="smaller",
        color=ax.lines[1].get_color(),
    )

    ax.text(
        SETTINGS["defaults"]["MS"]["lc_run_end"] - 0.01,
        0.5,
        "ANALYSIS",
        horizontalalignment="right",
        verticalalignment="center",
        rotation="vertical",
        size="smaller",
        color=ax.lines[2].get_color(),
    )

    ax.text(
        SETTINGS["defaults"]["MS"]["lc_run_end"] + 0.02,
        0.5,
        "END",
        horizontalalignment="left",
        verticalalignment="center",
        rotation="vertical",
        size="smaller",
        color=ax.lines[2].get_color(),
    )

    return fig, ax
