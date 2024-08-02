"""Workflow routine for medicinal chemistry screening."""

import json
import logging
from pathlib import Path
from shutil import copy
from typing import TYPE_CHECKING

import numpy as np
from bruker.api.topspin import PhysicalRange

if TYPE_CHECKING:
    import zmq

import synthesis_bots.decisions.same_as_reference2 as decision_nmr
from synthesis_bots.planners.medchem.scaleup import ScaleupPlanner
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

NAME = PREFIX["Medchem_Screening"]


def analyse_results(
    json_path: Path,
    data_path: Path,
    sm_nmr_data_path: Path,
    archive_path: Path,
    ms_summary_path: Path,
    nmr_summary_path: Path,
):
    samples = SampleBatch.from_file(json_path)

    screening_data = {}

    for sample in samples:
        logger.info(f"Analysing NMR of {NAME}-{sample.position:02d}.")
        nmr_path = data_path / f"{NAME}-{sample.position:02d}"
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))
        nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=1.2,
            reference=True,
        )
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))

        peaks_ppm = nmr.pick_peaks(
            reference_intensity=150,
            minimum_intensity=10,
            sensitivity=1,
        )

        amine = sample.sample_info["amine"].upper()  # type: ignore
        logger.info(f"Amine starting material: {amine}.")
        amine_nmr_path = sm_nmr_data_path / f"{NAME}-SM-{amine}"
        logger.info(f"Starting material path: {amine_nmr_path}.")
        amine_nmr = NMRExperiment(FOURIER.open_experiment(amine_nmr_path))
        amine_nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=1.2,
            reference=True,
        )
        amine_nmr = NMRExperiment(FOURIER.open_experiment(amine_nmr_path))

        cyanate = sample.sample_info["isocyanate"].upper()  # type: ignore
        logger.info(f"Cyanate starting material: {cyanate}.")
        cyanate_nmr_path = sm_nmr_data_path / f"{NAME}-SM-{cyanate}"
        cyanate_nmr = NMRExperiment(FOURIER.open_experiment(cyanate_nmr_path))
        cyanate_nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=1.2,
            reference=True,
        )
        cyanate_nmr = NMRExperiment(FOURIER.open_experiment(cyanate_nmr_path))

        ppm_range = (0.5, 9.5)
        pr = PhysicalRange(min(ppm_range), max(ppm_range))

        nmr_np = np.array(
            nmr.nmr_data.getSpecDataPoints(physRange=[pr])["dataPoints"],
            dtype=np.double,
        )
        cynate_np = np.array(
            cyanate_nmr.nmr_data.getSpecDataPoints(physRange=[pr])[
                "dataPoints"
            ],
            dtype=np.double,
        )
        amine_np = np.array(
            amine_nmr.nmr_data.getSpecDataPoints(physRange=[pr])["dataPoints"],
            dtype=np.double,
        )

        distance, dtw_pass = decision_nmr.main(
            test_nmr=nmr_np,
            reference_nmr=[cynate_np, amine_np],
            distance_threshold=25,
            pruning_threshold=0.2,
            plot_ticks=10,
            ppm_range=ppm_range,
            archive_path=archive_path
            / f"DTW-{NAME}-{sample.position:02d}.svg",
        )

        screening_data[str(sample.position)] = {
            "sample_info": sample.sample_info,  # type: ignore
            "amine": sample.sample_info["amine"],  # type: ignore
            "isocyanate": sample.sample_info["isocyanate"],  # type: ignore
            "peaks_ppm": peaks_ppm,
            "DTW_distance": distance,
            "NMR_PASS": not dtw_pass,
        }
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))
        if archive_path is not None:
            fig, _ = nmr.plot_nmr(
                region=(10.5, -0.5), intensity_region=(10, 6)
            )
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

    with open(ms_summary_path, "r", newline="\n") as f:
        ms_summary = json.load(f)

    for sample in samples:
        idx = str(sample.position)
        screening_data[idx]["lcms_peaks"] = ms_summary[idx]
        if (
            screening_data[idx]["NMR_PASS"]
            and screening_data[idx]["lcms_peaks"]["MS_PASS"]
        ):
            screening_data[idx]["SCALEUP"] = True
            logger.info(f"Sample {sample.position:02d} decision... PASS.")
        else:
            screening_data[idx]["SCALEUP"] = False
            logger.info(f"Sample {sample.position:02d} decision... FAIL.")

    with open(data_path.parent / "SUMMARY_NMR.json", "w", newline="\n") as f:
        json.dump(screening_data, f, indent=4)

    logger.info(f"NMR data summary saved in {data_path.parent}.")

    with open(nmr_summary_path, "w", newline="\n") as f:
        json.dump(screening_data, f, indent=4)

    logger.info(f"NMR data summary archived in {nmr_summary_path.parent}.")


def next_step(
    nmr_summary_path: Path,
    expected_ms_json: Path,
    json_path: Path,
    cs_csv_input: Path,
    future_cs_csv: Path,
    future_ms_json: Path,
    future_nmr_json: Path,
):
    """
    Decide on the next steps.

    Checks if both NMR and MS criteria have passed and then prepares the
    ChemSpeed CSV, MS JSON and NMR JSON for the subsequent step.

    Parameters
    ----------
    nmr_summary_path
        Path to the NMR summary JSON.
    expected_ms_json
        Path to the MS summary JSON.
    json_path
        Path to the experimental summary JSON.
    cs_csv_input
        Path to the ChemSpeed CSV from the screening run.
    future_cs_csv
        Path to where the future CSV should be saved.
    future_ms_json
        Path to where the future expected MS JSON should be saved.
    future_nmr_json
        Path to where the future NMR sample info JSON should be saved.

    """
    planner = ScaleupPlanner(
        screening_data=nmr_summary_path,
        screening_nmr=json_path,
        predicted_ms=expected_ms_json,
        import_file=cs_csv_input,
    )

    planner.generate(
        csv_path=future_cs_csv,
        ms_path=future_ms_json,
        nmr_path=future_nmr_json,
    )


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
    ms_summary_path = archive_path.parent / "SUMMARY_MS.json"
    archive_inp = PATHS["NMR_archive"] / "INPUT"
    cs_csv_input = archive_inp / f"{NAME}-CHEMSPEED.csv"
    expected_ms_json = archive_inp / f"{NAME}-EXPECTED-MS.json"
    cs_csv_archive = archive_inp / f"{PREFIX['Medchem_Scaleup']}-CHEMSPEED.csv"
    future_ms_json = (
        archive_inp / f"{PREFIX['Medchem_Scaleup']}-EXPECTED-MS.json"
    )
    future_nmr_json = json_path.with_stem(f"{PREFIX['Medchem_Scaleup']}")
    future_nmr_json_archive = archive_inp / f"{PREFIX['Medchem_Scaleup']}.json"

    if not archive_path.exists():
        archive_path.mkdir(parents=True, exist_ok=True)

    sm_nmr_data_path = PATHS["NMR_data"] / f"{NAME}-SM" / "DATA" / "NMR"

    if DRY:
        print(f"json_path is {json_path}.")
        print(f"data_path is {data_path}.")
        print(f"archive_path is {archive_path}.")
        print(f"MS results from: {ms_summary_path}.")
        print(f"Screening summary to: {nmr_summary_path}.")
        print(f'Screening to: {archive_path.parent / "SUMMARY_NMR.json"}.')
        print(f"ChemSpeed CSV from: {cs_csv_input}.")
        print(f"predicted MS from: {expected_ms_json}.")
        print(f'ChemSpeed CSV to: {PATHS["CS_csv_medchem"]}.')
        print(f"ChemSpeed CSV to: {cs_csv_archive}.")
        print(f"Expected MS to: {future_ms_json}.")
        print(f"Next NMR JSON to: {future_nmr_json}.")
        print(f"Next NMR JSON to: {future_nmr_json_archive}.")
        pub.send_string("[NMR] Medchem_Screening Completed\n")

    else:
        acquire_batch(
            samples=json_path,
            name=NAME,
            data_path=data_path,
            dry=DRY,
        )

        analyse_results(
            json_path=json_path,
            data_path=data_path,
            sm_nmr_data_path=sm_nmr_data_path,
            archive_path=archive_path,
            ms_summary_path=ms_summary_path,
            nmr_summary_path=nmr_summary_path,
        )

        next_step(
            nmr_summary_path=nmr_summary_path,
            expected_ms_json=expected_ms_json,
            json_path=json_path,
            cs_csv_input=cs_csv_input,
            future_cs_csv=PATHS["CS_csv_medchem"],
            future_ms_json=future_ms_json,
            future_nmr_json=future_nmr_json,
        )

        copy(PATHS["CS_csv_medchem"], cs_csv_archive)
        copy(future_nmr_json, future_nmr_json_archive)

        pub.send_string("[NMR] Medchem_Screening Completed\n")
