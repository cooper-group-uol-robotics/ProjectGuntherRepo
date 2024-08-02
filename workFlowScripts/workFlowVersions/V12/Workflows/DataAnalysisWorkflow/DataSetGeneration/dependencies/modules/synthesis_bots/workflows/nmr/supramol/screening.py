"""Workflow routine for supramolecular screening."""

import json
import logging
from pathlib import Path
from shutil import copy
from typing import (
    TYPE_CHECKING,
    Optional,
)

if TYPE_CHECKING:
    import zmq

import dependencies.modules.synthesis_bots.decisions.different_from_reagents as decision_nmr
from dependencies.modules.synthesis_bots.planners.supramol.replication import ReplicationPlanner
from dependencies.modules.synthesis_bots.utils.constants import (
    DRY,
    PATHS,
    PREFIX,
    SETTINGS,
    TODAY,
)
from dependencies.modules.synthesis_bots.utils.nmr.acquisition import (
    FOURIER,
    acquire_batch,
)
from dependencies.modules.synthesis_bots.utils.nmr.processing import NMRExperiment
from dependencies.modules.synthesis_bots.utils.nmr.samples import SampleBatch

logger = logging.getLogger(__name__)

NAME = PREFIX["Supramol_Screening"]


def results_analysis(
    sm_nmr_path: Path,
    json_path: Path,
    data_path: Path,
    ms_summary_path: Path,
    archive_path: Optional[Path] = None,
    nmr_summary_path: Optional[Path] = None,
):
    """
    Analyse screening NMR results.

    1. Load spectrum.
    2. Process spectrum.
    3. Perform pick peaking.
    4. Compare against starting materials.
    5. Save results and plot.

    Parameters
    ----------
    sm_nmr_path
        Path to the starting materials NMR data.
    json_path
        Path to the sample information JSON.
    data_path
        Path to the raw NMR data.
    ms_summary_path
        Path to the MS screening results.
    archive_path
        Data archive path for JDX files.
    nmr_summary_path
        Summary saving path.

    """
    with open(sm_nmr_path, "r") as f:
        sm_nmr_data = json.load(f)

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

        ppm_range = (
            min(SETTINGS["workflows"]["decision"]["ppm_range"]),
            max(SETTINGS["workflows"]["decision"]["ppm_range"]),
        )

        peaks_ppm = nmr.pick_peaks(
            reference_intensity=150,
            minimum_intensity=10,
            sensitivity=1,
            ppm_range=ppm_range,
        )

        amine_ppm = sm_nmr_data[sample.sample_info["amine"]][  # type: ignore
            "peaks_ppm"
        ]
        carbonyl_ppm = sm_nmr_data[
            sample.sample_info["carbonyl"]  # type: ignore
        ]["peaks_ppm"]

        nmr_criteria = decision_nmr.main(
            reaction_peaks=peaks_ppm,
            reagents_list=[amine_ppm, carbonyl_ppm],
        )

        screening_data[str(sample.position)] = {
            "sample_info": sample.sample_info,  # type: ignore
            "amine": sample.sample_info["amine"],  # type: ignore
            "carbonyl": sample.sample_info["carbonyl"],  # type: ignore
            "metal": sample.sample_info["metal"],  # type: ignore
            "peaks_ppm": peaks_ppm,
            "NMR_PASS": nmr_criteria,
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

    with open(ms_summary_path, "r", newline="\n") as f:
        ms_summary = json.load(f)

    for sample in samples:
        idx = str(sample.position)
        screening_data[idx]["MS_PASS"] = ms_summary[idx]["MS_PASS"]
        if screening_data[idx]["NMR_PASS"] and screening_data[idx]["MS_PASS"]:
            screening_data[idx]["REPLICATION"] = True
            screening_data[idx]["mz_peaks"] = ms_summary[idx]["mz_peaks"]
            logger.info(f"Sample {sample.position:02d} decision... PASS.")
        else:
            screening_data[idx]["REPLICATION"] = False
            logger.info(f"Sample {sample.position:02d} decision... FAIL.")

    with open(data_path.parent / "SUMMARY_NMR.json", "w", newline="\n") as f:
        json.dump(screening_data, f, indent=4)

    logger.info(f"NMR data summary saved in {data_path.parent}.")

    if nmr_summary_path is not None:
        with open(nmr_summary_path, "w", newline="\n") as f:
            json.dump(screening_data, f, indent=4)

        logger.info(f"NMR data summary archived in {nmr_summary_path.parent}.")


def next_step(
    nmr_summary_path: Path,
    expected_ms_json: Path,
    cs_csv_supra_input: Path,
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
    cs_csv_supra_input
        Path to the ChemSpeed CSV from the screening run.
    future_cs_csv
        Path to where the future CSV should be saved.
    future_ms_json
        Path to where the future expected MS JSON should be saved.
    future_nmr_json
        Path to where the future NMR sample info JSON should be saved.

    """
    planner = ReplicationPlanner(
        screening_data=nmr_summary_path,
        predicted_ms=expected_ms_json,
        import_file=cs_csv_supra_input,
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
    Execute the Supramol_Screening workflow routine.

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
    cs_csv_supra_input = archive_inp / f"{NAME}-CHEMSPEED.csv"
    expected_ms_json = archive_inp / f"{NAME}-EXPECTED-MS.json"
    cs_csv_supra_archive = (
        archive_inp / f"{PREFIX['Supramol_Replication']}-CHEMSPEED.csv"
    )
    future_ms_json = (
        archive_inp / f"{PREFIX['Supramol_Replication']}-EXPECTED-MS.json"
    )
    future_nmr_json = json_path.with_stem(f"{PREFIX['Supramol_Replication']}")
    future_nmr_json_archive = (
        archive_inp / f"{PREFIX['Supramol_Replication']}.json"
    )

    if not archive_path.exists():
        archive_path.mkdir(parents=True, exist_ok=True)

    sm_nmr_path = json_path.with_name(f"{NAME}-SM-NMR.json")

    if DRY:
        print(f"json_path is {json_path}.")
        print(f"data_path is {data_path}.")
        print(f"archive_path is {archive_path}.")
        print(f"sm_nmr_path is {sm_nmr_path}.")
        print(f"MS results from: {ms_summary_path}.")
        print(f"Screening summary to: {nmr_summary_path}.")
        print(f'Screening to: {archive_path.parent / "SUMMARY_NMR.json"}.')
        print(f"ChemSpeed CSV from: {cs_csv_supra_input}.")
        print(f"predicted MS from: {expected_ms_json}.")
        print(f'ChemSpeed CSV to: {PATHS["CS_csv_supra"]}.')
        print(f"ChemSpeed CSV to: {cs_csv_supra_archive}.")
        print(f"Expected MS to: {future_ms_json}.")
        print(f"Next NMR JSON to: {future_nmr_json}.")
        print(f"Next NMR JSON to: {future_nmr_json_archive}.")
        pub.send_string("[NMR] Supramol_Screening Completed\n")

    else:
        acquire_batch(
            samples=json_path,
            name=NAME,
            data_path=data_path,
            dry=DRY,
        )

        results_analysis(
            sm_nmr_path=sm_nmr_path,
            json_path=json_path,
            data_path=data_path,
            ms_summary_path=ms_summary_path,
            archive_path=archive_path,
            nmr_summary_path=nmr_summary_path,
        )

        next_step(
            nmr_summary_path=nmr_summary_path,
            expected_ms_json=expected_ms_json,
            cs_csv_supra_input=cs_csv_supra_input,
            future_cs_csv=PATHS["CS_csv_supra"],
            future_ms_json=future_ms_json,
            future_nmr_json=future_nmr_json,
        )

        copy(PATHS["CS_csv_supra"], cs_csv_supra_archive)
        copy(future_nmr_json, future_nmr_json_archive)

        pub.send_string("[NMR] Supramol_Screening Completed\n")
