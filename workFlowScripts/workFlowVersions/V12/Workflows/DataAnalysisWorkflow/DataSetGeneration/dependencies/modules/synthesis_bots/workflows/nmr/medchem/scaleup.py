"""Workflow routine for medicinal chemistry scaleup."""

import json
import logging
from pathlib import Path
from shutil import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import zmq

import synthesis_bots.decisions.same_as_reference as decision_nmr
from synthesis_bots.planners.medchem.diversification import (
    DiversificationPlanner,
)
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

NAME = PREFIX["Medchem_Scaleup"]


def analyse_results(
    json_path: Path,
    data_path: Path,
    screening_data_path: Path,
    archive_path: Path,
    ms_summary_path: Path,
    nmr_summary_path: Path,
):
    samples = SampleBatch.from_file(json_path)
    replication_data = {}

    for sample in samples:
        idx = str(sample.position)
        logger.info(f"Analysing NMR of {NAME}-{sample.position:02d}.")
        logger.info(f"Replicate of {idx}.")
        nmr_path = data_path / f"{NAME}-{sample.position:02d}"
        reference_nmr = (
            screening_data_path
            / f"{PREFIX['Medchem_Screening']}-{sample.position:02d}"
        )
        ref_nmr = NMRExperiment(FOURIER.open_experiment(reference_nmr))
        ref_nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=1.2,
            reference=True,
        )
        # Need to re-load the NMRExperiments to re-import the data.
        ref_nmr = NMRExperiment(FOURIER.open_experiment(reference_nmr))

        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))
        nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=1.2,
            reference=True,
        )
        # Need to re-load the NMRExperiments to re-import the data.
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))

        peaks_ppm = nmr.pick_peaks(
            reference_intensity=150,
            minimum_intensity=10,
            sensitivity=1,
        )

        nmr_criteria = decision_nmr.main(
            test_nmr=nmr,
            reference_nmr=ref_nmr,
            distance_threshold=SETTINGS["workflows"]["decision"][
                "dtw_threshold"
            ],
            archive_path=archive_path
            / f"DTW-{NAME}-{sample.position:02d}.svg",
        )

        replication_data[idx] = {
            "sample_info": sample.sample_info,  # type: ignore
            "peaks_ppm": peaks_ppm,
            "NMR_PASS": nmr_criteria,
        }
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))
        fig, _ = nmr.plot_nmr(region=(10.5, -0.5))
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
        replication_data[idx]["lcms_peaks"] = ms_summary[idx]
        if (
            replication_data[idx]["NMR_PASS"]
            and replication_data[idx]["lcms_peaks"]["MS_PASS"]
        ):
            replication_data[idx]["REPLICATED"] = True
            logger.info(f"Sample {sample.position:02d} decision... PASS.")
        else:
            replication_data[idx]["REPLICATED"] = False
            logger.info(f"Sample {sample.position:02d} decision... FAIL.")

    with open(data_path.parent / "SUMMARY_NMR.json", "w", newline="\n") as f:
        json.dump(replication_data, f, indent=4)

    logger.info(f"NMR data summary saved in {data_path.parent}.")

    with open(nmr_summary_path, "w", newline="\n") as f:
        json.dump(replication_data, f, indent=4)

    logger.info(f"NMR data summary archived in {nmr_summary_path.parent}.")


def next_step(
    nmr_summary_path: Path,
    expected_ms_json: Path,
    json_path: Path,
    cs_csv_input: Path,
    mass_csv_inp: Path,
    future_cs_csv: Path,
    future_ms_json: Path,
    future_nmr_json: Path,
):
    planner = DiversificationPlanner(
        replication_data=nmr_summary_path,
        replication_nmr=json_path,
        replication_ms=expected_ms_json,
        input_file=mass_csv_inp,
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
    screening_data_path = (
        PATHS["NMR_data"]
        / f"{TODAY}-{PREFIX['Medchem_Screening']}"
        / "DATA"
        / "NMR"
    )

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    archive_path = PATHS["NMR_archive"] / f"{TODAY}-{NAME}" / "DATA" / "NMR"
    nmr_summary_path = archive_path.parent / "SUMMARY_NMR.json"
    ms_summary_path = archive_path.parent / "SUMMARY_MS.json"
    archive_inp = PATHS["NMR_archive"] / "INPUT"
    cs_csv_input = archive_inp / f"{NAME}-CHEMSPEED.csv"
    expected_ms_json = (
        archive_inp / f"{PREFIX['Medchem_Scaleup']}-EXPECTED-MS.json"
    )
    cs_csv_archive = (
        archive_inp / f"{PREFIX['Medchem_Diversity']}-CHEMSPEED.csv"
    )
    mass_csv_inp = (
        archive_inp / f"{PREFIX['Medchem_Diversity']}-DIVERSIFICATION-MASS.csv"
    )
    future_ms_json = (
        archive_inp / f"{PREFIX['Medchem_Diversity']}-EXPECTED-MS.json"
    )
    future_nmr_json = json_path.with_stem(f"{PREFIX['Medchem_Diversity']}")
    future_nmr_json_archive = (
        archive_inp / f"{PREFIX['Medchem_Diversity']}.json"
    )

    if not archive_path.exists():
        archive_path.mkdir(parents=True, exist_ok=True)

    if DRY:
        print(f"json_path is {json_path}.")
        print(f"data_path is {data_path}.")
        print(f"archive_path is {archive_path}.")
        print(f"MS results from: {ms_summary_path}.")
        print(f"Screening NMR data from: {screening_data_path}.")
        print(f"Replication summary to: {nmr_summary_path}.")
        print(f'Replication to: {archive_path.parent / "SUMMARY_NMR.json"}.')
        print(f"ChemSpeed CSV from: {cs_csv_input}.")
        print(f'ChemSpeed CSV to: {PATHS["CS_csv_medchem"]}.')
        print(f"ChemSpeed CSV to: {cs_csv_archive}.")
        print(f"Next NMR JSON to: {future_nmr_json}.")
        print(f"Next NMR JSON to: {future_nmr_json_archive}.")
        pub.send_string("[NMR] Medchem_Scaleup Completed\n")

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
            screening_data_path=screening_data_path,
            archive_path=archive_path,
            ms_summary_path=ms_summary_path,
            nmr_summary_path=nmr_summary_path,
        )

        next_step(
            nmr_summary_path=nmr_summary_path,
            expected_ms_json=expected_ms_json,
            json_path=json_path,
            cs_csv_input=cs_csv_input,
            mass_csv_inp=mass_csv_inp,
            future_cs_csv=PATHS["CS_csv_medchem"],
            future_ms_json=future_ms_json,
            future_nmr_json=future_nmr_json,
        )

        copy(PATHS["CS_csv_medchem"], cs_csv_archive)
        copy(future_nmr_json, future_nmr_json_archive)

        pub.send_string("[NMR] Medchem_Scaleup Completed\n")
