"""
Main NMR processing functions (using TopSpin).

These should in the future extend the `fourier_nmr_driver` NMRExperiment class.

"""

import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from bruker.api.topspin import PhysicalRange
from dependencies.modules.fourier_nmr_driver import NMRExperiment as FourierNMRExperiment

from dependencies.modules.synthesis_bots.utils.constants import NMR_SETUP

logger = logging.getLogger(__name__)
plt.style.use("dependencies.modules.synthesis_bots.utils.mpl")


class NMRExperiment(FourierNMRExperiment):
    """Functions to expand the NMRExperiment from the NMR driver."""

    def __init__(
        self,
        nmr_experiment: FourierNMRExperiment,
    ):
        """Initalise NMRExperiment."""
        self.top = nmr_experiment.top
        self.data_provider = nmr_experiment.data_provider
        self.path = nmr_experiment.path
        self.nmr_data = nmr_experiment.nmr_data
        self.display = nmr_experiment.display
        self.display.show(dataset=self.nmr_data, newWindow=False)

    def process_spectrum(
        self,
        zero_filling: Optional[str] = None,
        line_broadening: Optional[float] = None,
        ai_baseline_phase: bool = True,
        baseline: bool = False,
        phase: bool = False,
        reference: bool = True,
    ) -> None:
        """
        Process NMR spectrum.

        Simple processing of the NMR spectrum.

        Parameters
        ----------
        nmr_experiment
            The NMRExperiment to analyse.
        zero_filling, optional
            Size of the real spectrum (to be zero-filled), by default None.
        line_broadening, optional
            Line broadening (in Hz), by default None
        ai_baseline_phase, optional
            If True, performs AI-powered automated phase and baseline
            correction as implemented in TopSpin (apbk), by default True.
        phase, optional
            If True, performs simple automated phase correction
            as implemented in TopSpin (abs and apk), by default False.
        baseline, optional
            If True, performs simple automated baseline correction
            as implemented in TopSpin (abs and apk), by default False.
        reference, optional
            Perform automated referencing using the edlock table, default True.

        """
        logger.info(f"Processing spectrum in {self.path}.")
        if zero_filling is not None:
            self.nmr_data.launch(f"si {zero_filling}")
            logger.info(
                f"Modified size of the real spectrum to {zero_filling}."
            )

        if line_broadening is not None:
            self.nmr_data.launch(f"lb {line_broadening}")
            logger.info(f"Line broadening changed to {line_broadening} Hz.")

        self.nmr_data.launch("efp")
        logger.info("Performed exponential multiplication and forward FT.")

        if ai_baseline_phase:
            self.nmr_data.launch("apbk -n")
            logger.info("Automated AI phase and baseline corrections applied.")

        if baseline:
            self.nmr_data.launch("abs n")
            logger.info("Automated phase and baseline corrections applied.")

        if phase:
            self.nmr_data.launch("apk")
            logger.info("Automated phase and baseline corrections applied.")

        if reference:
            unsuppressed = self.data_provider.getNMRData(
                str(
                    (
                        self.path.parents[2]
                        / f"100{self.path.parents[1].name}01"
                        / self.path.parent.name
                        / self.path.name
                    )
                )
            )
            unsuppressed.launch("sref")
            spectrum_ref = unsuppressed.getPar("SR")
            self.nmr_data.launch(f"sr {spectrum_ref}")
            logger.info(
                f"Referenced to the solvent peak (SR = {spectrum_ref} Hz)."
            )
        logger.info("Processing routine finished.")

    def pick_peaks(
        self,
        reference_intensity: Optional[float] = None,
        minimum_intensity: Optional[float] = None,
        maximum_intensity: Optional[float] = None,
        sensitivity: Optional[float] = None,
        ppm_range: tuple[float, float] = (-2, 12),
    ) -> list[float]:
        """
        Pick peaks in the spectrum using TopSpin's automated algorithm.

        There seems to be a limit on how small the minimum intensity can be
        set best to set reference intensity (tallest peak) to a large number
        (e.g., 100) instead of the default and then set the minimum intensity.

        Parameters
        ----------
        nmr_experiment
            The NMRExperiment to analyse.
        reference_intensity, optional
            Relative intensity of the highest intensity peak, by default None.
        minimum_intensity, optional
            Minimum intensity for peak picking, by default None.
        maximum_intensity, optional
            Maximum intensity for peak picking, by default None.
        sensitivity, optional
            Peak detection sensitivity, by default None.
        ppm_range, optional
            Range of ppm values of interest, by default (-2, 12).

        Returns
        -------
            Numpy array of chemical shifts of the peaks (ppm).

        """
        logger.info(f"Picking peaks of spectrum in {self.path}.")

        if reference_intensity is not None:
            self.nmr_data.launch(f"cy {reference_intensity}")
            logger.info(f"Reference intensity set to {reference_intensity}.")

        if minimum_intensity is not None:
            self.nmr_data.launch(f"mi {minimum_intensity}")
            logger.info(
                f"Minimum picking intensity set to {minimum_intensity}."
            )

        if maximum_intensity is not None:
            self.nmr_data.launch(f"maxi {maximum_intensity}")
            logger.info(
                f"Maximum picking intensity set to {maximum_intensity}."
            )

        if sensitivity is not None:
            self.nmr_data.launch(f"pc {sensitivity}")
            logger.info(f"Peak picking sensitivity set to {sensitivity}.")

        self.nmr_data.launch("ppf")
        logger.info("Peak picking routine (ppf) completed.")

        peak_list = self.nmr_data.getPeakList()
        peaks = sorted(
            [
                d["position"][0]
                for d in peak_list
                if min(ppm_range) <= d["position"][0] <= max(ppm_range)
            ],
            reverse=True,
        )

        return peaks

    def export_jcampdx(
        self,
        export_path: Path,
        export_all: bool = True,
    ):
        """
        Export the NMR data to JCAMP-DX.

        Using IUPAC standard JCAMP-DX to store data for archiving. Contains the
        FID, as well as real and imaginary spectrum data.

        Parameters
        ----------
        nmr_experiment
            NMRExperiment to export.
        export_path
            Path to the resulting JCAMP-DX file.
        export_all, optional
            Whether all PROCNOs should be exported, by default True.

        """
        # Data ID = 6 is all EXPNOs (FIDs) and PROCNOs.
        # Data ID = 4 i just current EXPNOs (FID).
        data_id = 6 if export_all else 4

        # Option "3" is for a compressed JCAMP-DX (not really human-readable).
        self.nmr_data.launch(
            f'tojdx {str(export_path)} {data_id} 3 "{self.name}" '
            f'"{NMR_SETUP.origin}" "{NMR_SETUP.owner}"'
        )

        logger.info(f"JCAMP-DX of {self.name} exported to {export_path}.")

    def plot_nmr(
        self,
        region: tuple[float, float] = (10.5, -0.5),
        intensity_region: Optional[tuple[float, float]] = None,
    ):
        """
        Plot NMR spectrum.

        Parameters
        ----------
        region, optional
            Region to plot, by default (10.5,-0.5).
        intensity_region, optional
            Region which should be used for scaling for maximum intensity.

        Returns
        -------
            Matplotlib Figure and Axes.

        """
        left_x = max(region)
        right_x = min(region)

        nmr_spectrum = self.nmr_data

        fig, ax = plt.subplots(figsize=(16.5, 3.5))
        data = nmr_spectrum.getSpecDataPoints(
            physRange=[PhysicalRange(left_x, right_x)]
        )
        delta = nmr_spectrum.getSW() / int(nmr_spectrum.getPar("status SI"))
        pr = data["physicalRanges"][0]
        ppm = np.linspace(
            float(pr["start"]),
            float(pr["start"]) - delta * (len(data["dataPoints"]) - 1),
            len(data["dataPoints"]),
        )
        ax.plot(ppm, data["dataPoints"], color="black")

        ax.set_xlim(left_x, right_x)
        bottom = ax.get_ylim()[0]
        ax.set_xlabel("Chemical Shift / ppm")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_yticks([])
        if right_x > 0:
            ax.set_xticks(np.arange(int(right_x) + 1, int(left_x) + 1, step=1))
        else:
            ax.set_xticks(np.arange(int(right_x), int(left_x) + 1, step=1))

        if intensity_region is not None:
            left_x = max(intensity_region)
            right_x = min(intensity_region)
            zoom = nmr_spectrum.getSpecDataPoints(
                physRange=[PhysicalRange(left_x, right_x)]
            )
            top = max(zoom["dataPoints"])
            bottom = -max(zoom["dataPoints"]) * 0.05
            ax.set_ylim(bottom=bottom, top=top)

        return fig, ax
