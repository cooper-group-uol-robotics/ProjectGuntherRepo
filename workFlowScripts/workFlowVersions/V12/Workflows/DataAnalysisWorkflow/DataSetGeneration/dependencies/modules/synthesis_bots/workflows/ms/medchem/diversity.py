"""Workflow routine for medicinal chemistry diversification."""

import json
import logging
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path
from shutil import move
from typing import (
    TYPE_CHECKING,
    Any,
)

from lcms_parser import (
    ExpectedResults,
    WatersRawFile,
)

from synthesis_bots.utils.ms.acquisition import acquire_lcms
from synthesis_bots.utils.ms.csv_writer import write_csv
from synthesis_bots.utils.ms.plot import (
    plot_lc,
    plot_ms,
)

if TYPE_CHECKING:
    import zmq

import synthesis_bots.decisions.expected_lcms as expected_lcms
from synthesis_bots.utils.constants import (
    DRY,
    PATHS,
    PREFIX,
    SETTINGS,
    TODAY,
)

logger = logging.getLogger(__name__)

NAME = PREFIX["Medchem_Screening"]


def results_analysis(
    expected_json: Path,
    archive_path: Path,
    summary_path: Path,
):
    """
    Analyse screening LCMS results.

    1. Identify LC peaks above thresholds.
    2. Identify hits in corresponding MS spectra.
    3. Save plots and summary.

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

    screening_data: dict[int, Any] = {}

    for exp_id, expected in expected_results.items():
        screening_data[int(exp_id)] = {}
        ms_file = WatersRawFile(PATHS["LCMS_data"] / f"{exp_id}.raw")
        analog = ms_file.get_analog_trace()
        ms_criteria, ms_results, lc_peaks = expected_lcms.main(
            raw_path=(PATHS["LCMS_data"] / f"{exp_id}.raw"),
            expected_mz=expected,
            threshold=SETTINGS["defaults"]["MS"]["analog_peak_threshold2"],
        )

        fig, ax = plot_lc(
            raw_path=(PATHS["LCMS_data"] / f"{exp_id}.raw"),
            lc_peaks=lc_peaks,
        )

        if not (archive_path / "PLOTS").exists():
            (archive_path / "PLOTS").mkdir(parents=True)

        for n, (lc, ms) in enumerate(zip(lc_peaks, ms_results)):
            time = f"{lc.time.total_seconds()/60:.2f}"
            screening_data[int(exp_id)][time] = {}
            screening_data[int(exp_id)][time]["LC_Area"] = lc.integral
            screening_data[int(exp_id)][time]["MS_Hits"] = [
                asdict(hit) for hit in ms
            ]
            ms_time = timedelta(
                seconds=(
                    lc.time.total_seconds()
                    + SETTINGS["defaults"]["MS"]["lc_ms_flowpath"]
                )
            )

            if len(ms) > 0:
                logger.info(
                    "Plotting MS at " f"{ms_time.total_seconds()/60:.2f} min."
                )
                ms_fig, _ = plot_ms(
                    raw_path=(PATHS["LCMS_data"] / f"{exp_id}.raw"),
                    ms_time=ms_time,
                    mz_limits=(200, 650),
                )

                ms_fig.savefig(
                    archive_path / "PLOTS" / f"{int(exp_id):02d}_MS{n}.svg"
                )
                ms_fig.savefig(
                    archive_path / "PLOTS" / f"{int(exp_id):02d}_MS{n}.png",
                    dpi=600,
                )

                ax.scatter(
                    float(time),
                    analog.intensities[analog.get_scan_index(float(time))]
                    + 0.1,
                    s=180,
                    color="k",
                    marker="*",
                    linewidth=1.5,
                )

        fig.savefig(archive_path / "PLOTS" / f"{int(exp_id):02d}.svg")
        fig.savefig(archive_path / "PLOTS" / f"{int(exp_id):02d}.png", dpi=600)

        screening_data[int(exp_id)]["MS_PASS"] = ms_criteria

    logger.info("Finished analysing the RAW files.")

    screening_data = dict(sorted(screening_data.items()))

    with open(summary_path, "w", newline="\n") as f:
        json.dump(screening_data, f, indent=4)

    logger.info(f"Hits saved in {summary_path}.")


def main(
    pub: "zmq.Socket",
    sub: "zmq.Socket",
):
    """
    Execute the Medchem3 workflow routine.

    1. Acquire LCMS.
    2. Call expected LCMS decision maker.
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
        pub.send_string("[LCMS] Medchem2 Completed\n")

    else:
        logger.info(f"Starting LCMS workflow: {NAME}.")
        write_csv(
            samples_json=expected_json,
            csv_path=csv_source,
            tune_file="MedChem",
            blank=True,
        )
        acquire_lcms(queue_csv=csv_source)

        results_analysis(
            expected_json=expected_json,
            archive_path=archive_path,
            summary_path=summary_path,
        )

        for raw_file in PATHS["LCMS_data"].glob("*.raw"):
            move(raw_file, archive_path)

        logger.info(f"Moved RAW files to {archive_path}.")
        logger.info("LCMS analysis completed.")

        pub.send_string("[LCMS] Medchem3 Completed\n")
