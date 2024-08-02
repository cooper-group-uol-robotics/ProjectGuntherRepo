"""Workflow routine for supramolecular screening."""

import json
import logging
from dataclasses import asdict
from pathlib import Path
from shutil import move
from typing import (
    TYPE_CHECKING,
    Any,
)

from dependencies.modules.lcms_parser import ExpectedResults

from dependencies.modules.synthesis_bots.utils.ms.acquisition import acquire_lcms
from dependencies.modules.synthesis_bots.utils.ms.csv_writer import write_csv
from dependencies.modules.synthesis_bots.utils.ms.plot import plot_ms

if TYPE_CHECKING:
    import zmq

import dependencies.modules.synthesis_bots.decisions.expected_mass_metals as expected_mass_metals
from dependencies.modules.synthesis_bots.utils.constants import (
    DRY,
    PATHS,
    PREFIX,
    TODAY,
)

logger = logging.getLogger(__name__)

NAME = PREFIX["Supramol_Screening"]


def results_analysis(
    expected_json: Path,
    archive_path: Path,
    summary_path: Path,
) -> None:
    """
    Analyse screening LCMS results.

    1. Load the expected results.
    2. Identify hits.
    3. Save summary.
    4. Save plots.

    Parameters
    ----------
    expected_json
        Expected results path.
    archive_path
        Data archive path.
    summary_path
        Summary saving path.

    """
    with open(expected_json, "r") as f:
        predicted_structures = json.load(f)

    logger.info(f"Loaded {expected_json.name}.")
    logger.debug(f"Full path is {expected_json.resolve()}.")

    expected_results = {
        exp_id: ExpectedResults.from_dict(prediction)
        for exp_id, prediction in predicted_structures.items()
    }
    print(expected_results)

    screening_data: dict[int, Any] = {}


    for exp_id, expected in expected_results.items():
        screening_data[exp_id] = {}
        ms_criteria, ms_results = expected_mass_metals.main(
            raw_path=(PATHS["LCMS_data"] / f"{exp_id}.raw"),
            expected_mz=expected,
        )

        screening_data[exp_id]["MS_PASS"] = ms_criteria
        screening_data[exp_id]["mz_peaks"] = [
            asdict(hit) for hit in ms_results
        ]

        fig, _ = plot_ms(raw_path=(PATHS["LCMS_data"] / f"{exp_id}.raw"))

        if not (archive_path / "PLOTS").exists():
            (archive_path / "PLOTS").mkdir(parents=True)

        fig.savefig(archive_path / "PLOTS" / f"{exp_id}.svg")
        fig.savefig(archive_path / "PLOTS" / f"{exp_id}.png", dpi=600)

    logger.info("Finished analysing the RAW files.")

    screening_data = dict(sorted(screening_data.items()))

    with open(summary_path, "w", newline="\n") as f:
        json.dump(screening_data, f, indent=4)

    logger.info(f"Hits saved in {summary_path}.")


def main(
    pub: "zmq.Socket",
    sub: "zmq.Socket",
) -> None:
    """
    Execute the Supra1 workflow routine.

    1. Acquire LCMS.
    2. Analyse the results.
    3. Clean up the working directory.

    """
    csv_source = PATHS["LCMS_archive"] / "INPUT" / f"{NAME}.csv"
    archive_path = PATHS["LCMS_archive"] / f"{TODAY}-{NAME}" / "DATA" / "LCMS"
    if not archive_path.exists():
        archive_path.mkdir(parents=True, exist_ok=True)

    summary_path = archive_path.parent / "SUMMARY_MS.json"
    expected_json = csv_source.with_name(f"{NAME}-EXPECTED-MS.json")

    if DRY:
        print(__name__)
        print(f"CSV source is: {csv_source}")
        print(f"expected_json is in: {expected_json}")
        print(f'Raw files are in: {PATHS["LCMS_data"]}')
        print(f"archive_path is in: {archive_path}")
        print(f"Will save summary to: {summary_path}")
        pub.send_string("[LCMS] Supra1 Completed\n")

    else:
        logger.info(f"Starting LCMS workflow: {NAME}.")
        write_csv(
            samples_json=expected_json,
            csv_path=csv_source,
            tune_file="SupraChemCage",
        )
        acquire_lcms(queue_csv=csv_source)

        results_analysis(
            expected_json=expected_json,
            summary_path=summary_path,
            archive_path=archive_path,
        )

        for raw_file in PATHS["LCMS_data"].glob("*.raw"):
            move(raw_file, archive_path)

        logger.info(f"Moved RAW files to {archive_path}.")
        logger.info("LCMS analysis completed.")
        pub.send_string("[LCMS] Supra1 Completed\n")
