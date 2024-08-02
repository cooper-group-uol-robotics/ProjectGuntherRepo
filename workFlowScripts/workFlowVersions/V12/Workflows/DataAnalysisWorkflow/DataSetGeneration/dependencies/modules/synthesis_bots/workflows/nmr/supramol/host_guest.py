"""Workflow routine for supramolecular host-guest identification."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import zmq

import synthesis_bots.decisions.guest_binding as decision_nmr
from synthesis_bots.utils.constants import (
    DRY,
    PATHS,
    PREFIX,
    SETTINGS,
    TODAY,
)
from synthesis_bots.utils.nmr.acquisition import (
    FOURIER,
    acquire_batch,
)
from synthesis_bots.utils.nmr.processing import NMRExperiment
from synthesis_bots.utils.nmr.samples import SampleBatch

logger = logging.getLogger(__name__)

NAME = PREFIX["Supramol_HostGuest"]


def results_analysis(
    json_path: Path,
    data_path: Path,
    archive_path: Path,
    replication_data_path: Path,
    nmr_summary_path: Path,
):
    samples = SampleBatch.from_file(json_path)
    hg_data = {}

    for sample in samples:
        idx = str(sample.position)
        logger.info(f"Analysing NMR of {NAME}-{sample.position:02d}.")

        nmr_path = data_path / f"{NAME}-{sample.position:02d}"
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))
        nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=SETTINGS["workflows"]["decision"]["hg_lb"],
            reference=True,
        )
        ppm_range = (
            min(SETTINGS["workflows"]["decision"]["ppm_range"]),
            max(SETTINGS["workflows"]["decision"]["ppm_range"]),
        )
        peaks_ppm = nmr.pick_peaks(
            reference_intensity=150,
            minimum_intensity=3,
            ppm_range=ppm_range,
        )

        ref_nmr_path = (
            replication_data_path
            / f"{PREFIX['Supramol_Replication']}-{sample.position:02d}"
        )
        ref_nmr = NMRExperiment(FOURIER.open_experiment(ref_nmr_path))
        ref_nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=SETTINGS["workflows"]["decision"]["hg_lb"],
            reference=True,
        )
        ppm_range = (
            min(SETTINGS["workflows"]["decision"]["ppm_range"]),
            max(SETTINGS["workflows"]["decision"]["ppm_range"]),
        )
        ref_peaks_ppm = ref_nmr.pick_peaks(
            reference_intensity=150,
            minimum_intensity=75,
            ppm_range=ppm_range,
        )

        nmr_criteria, triggers = decision_nmr.main(
            test_nmr=peaks_ppm,
            reference_nmr=ref_peaks_ppm,
            shift_threshold=SETTINGS["workflows"]["decision"]["hg_shift"],
        )

        hg_data[idx] = {
            "sample_info": sample.sample_info,  # type: ignore
            "peaks_ppm": peaks_ppm,
            "HG_BOUND": nmr_criteria,
            "trigger_peaks": triggers,
        }
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))
        fig, _ = nmr.plot_nmr(region=(10.5, -1.5), intensity_region=(10, 8))
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

    with open(data_path.parent / "SUMMARY_NMR.json", "w", newline="\n") as f:
        json.dump(hg_data, f, indent=4)

    logger.info(f"NMR data summary saved in {data_path.parent}.")

    with open(nmr_summary_path, "w", newline="\n") as f:
        json.dump(hg_data, f, indent=4)

    logger.info(f"NMR data summary archived in {nmr_summary_path.parent}.")


def main(
    pub: "zmq.Socket",
    sub: "zmq.Socket",
):
    """
    Execute the Supramol_Replication workflow routine.

    1. Acquire NMR spectra.
    2. Process each spectrum and pick peaks.
    3. Archive results.
    4. Call "same_as_reference" decision maker.
    5. Check the results of the MS screening: NMR is the slow step.

    """
    logger.info(f"Starting NMR workflow: {NAME}.")
    json_path = PATHS["NMR_data"] / "INPUT" / f"{NAME}.json"
    data_path = PATHS["NMR_data"] / f"{TODAY}-{NAME}" / "DATA" / "NMR"

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    archive_path = PATHS["NMR_archive"] / f"{TODAY}-{NAME}" / "DATA" / "NMR"
    replication_data_path = (
        PATHS["NMR_archive"]
        / f"{TODAY}-{PREFIX['Supramol_Replication']}"
        / "DATA"
        / "NMR"
    )
    nmr_summary_path = archive_path.parent / "SUMMARY_NMR.json"

    if not archive_path.exists():
        archive_path.mkdir(parents=True, exist_ok=True)

    if DRY:
        print(f"json_path is {json_path}.")
        print(f"data_path is {data_path}.")
        print(f"archive_path is {archive_path}.")
        print(f"Replication summary to: {nmr_summary_path}.")
        print(f'Replication to: {archive_path.parent / "SUMMARY_NMR.json"}.')
        pub.send_string("[NMR] Supramol_HostGuest Completed\n")

    else:
        acquire_batch(
            samples=json_path,
            name=NAME,
            data_path=data_path,
            dry=DRY,
        )

        results_analysis(
            json_path=json_path,
            data_path=data_path,
            archive_path=archive_path,
            replication_data_path=replication_data_path,
            nmr_summary_path=nmr_summary_path,
        )

        pub.send_string("[NMR] Supramol_Replication Completed\n")
