"""Workflow routine for medicinal chemistry diversification."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import zmq

from synthesis_bots.utils.constants import (
    DRY,
    PATHS,
    PREFIX,
    TODAY,
)
from synthesis_bots.utils.nmr.acquisition import (
    FOURIER,
    acquire_batch,
)
from synthesis_bots.utils.nmr.processing import NMRExperiment
from synthesis_bots.utils.nmr.samples import SampleBatch

logger = logging.getLogger(__name__)

NAME = PREFIX["Medchem_Diversity"]


def process_results(
    json_path: Path,
    data_path: Path,
    archive_path: Path,
    nmr_summary_path: Path,
):
    """
    Process the spectra from Medchem Diversification.

    Parameters
    ----------
    json_path
        Path to the sample info JSON.
    data_path
        Path to the NMR data.
    archive_path
        Path to the archive.
    nmr_summary_path
        Path to the summary JSON.

    """
    samples = SampleBatch.from_file(json_path)

    diversity_data = {}

    for sample in samples:
        logger.info(f"Analysing NMR of {NAME}-{sample.position:02d}.")
        nmr_path = data_path / f"{NAME}-{sample.position:02d}"
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))

        nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=0.8,
            reference=True,
            ai_baseline_phase=False,
        )

        peaks_ppm = nmr.pick_peaks(
            reference_intensity=150,
            minimum_intensity=10,
            sensitivity=1,
        )

        diversity_data[str(sample.position)] = {
            "sample_info": sample.sample_info,  # type: ignore
            "urea": sample.sample_info["urea"],  # type: ignore
            "reagent": sample.sample_info["reagent"],  # type: ignore
            "peaks_ppm": peaks_ppm,
        }

        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))
        fig, _ = nmr.plot_nmr(region=(10.5, -0.5), intensity_region=(10, 6))
        if not (archive_path / "PLOTS").exists():
            (archive_path / "PLOTS").mkdir(parents=True)
        fig.savefig(
            archive_path / "PLOTS" / f"{NAME}-{sample.position:02d}.svg"
        )
        fig.savefig(
            archive_path / "PLOTS" / f"{NAME}-{sample.position:02d}.png",
            dpi=600,
        )
        nmr.export_jcampdx(
            export_path=archive_path / f"{NAME}-{sample.position:02d}.dx",
            export_all=False,
        )

        nmr.export_jcampdx(
            export_path=archive_path / f"{NAME}-{sample.position:02d}.dx",
            export_all=False,
        )

    with open(data_path.parent / "SUMMARY_NMR.json", "w", newline="\n") as f:
        json.dump(diversity_data, f, indent=4)

    logger.info(f"NMR data summary saved in {data_path.parent}.")

    with open(nmr_summary_path, "w", newline="\n") as f:
        json.dump(diversity_data, f, indent=4)

    logger.info(f"NMR data summary archived in {nmr_summary_path.parent}.")


def main(
    pub: "zmq.Socket",
    sub: "zmq.Socket",
):
    """
    Execute the Medchem_Screening workflow routine.

    1. Acquire NMR spectra.
    2. Process each spectrum and pick peaks.
    3. Archive results.
    4. Call "different_from_reagents" decision maker.
    5. Check the results of the MS screening: NMR is the slow step.

    """
    logger.info(f"Starting NMR workflow: {NAME}.")
    json_path = PATHS["NMR_data"] / "INPUT" / f"{NAME}.json"
    data_path = PATHS["NMR_data"] / f"{TODAY}-{NAME}" / "DATA" / "NMR"

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    archive_path = PATHS["NMR_archive"] / f"{TODAY}-{NAME}" / "DATA" / "NMR"
    nmr_summary_path = archive_path.parent / "SUMMARY_NMR.json"

    if not archive_path.exists():
        archive_path.mkdir(parents=True, exist_ok=True)

    if DRY:
        print(f"json_path is {json_path}.")
        print(f"data_path is {data_path}.")
        print(f"archive_path is {archive_path}.")
        print(f"Screening summary to: {nmr_summary_path}.")
        print(f'Screening to: {archive_path.parent / "SUMMARY_NMR.json"}.')
        pub.send_string("[NMR] Medchem_Diversity Completed\n")

    else:
        acquire_batch(
            samples=json_path,
            name=NAME,
            data_path=data_path,
            dry=DRY,
        )

        process_results(
            json_path=json_path,
            data_path=data_path,
            archive_path=archive_path,
            nmr_summary_path=nmr_summary_path,
        )

        pub.send_string("[NMR] Medchem_Diversity Completed\n")
