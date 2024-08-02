"""Module to prepare SM NMR summary."""

import json
import logging

from synthesis_bots.utils.constants import (
    DRY,
    LOGPATH,
    PATHS,
    TODAY,
)
from synthesis_bots.utils.nmr.acquisition import (
    FOURIER,
    acquire_batch,
)
from synthesis_bots.utils.nmr.processing import NMRExperiment
from synthesis_bots.utils.nmr.samples import SampleBatch

NAME = "MEDCHEM-SCREENING-SM"

logging.captureWarnings(True)
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    filename=LOGPATH,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s (%(name)s)",
    datefmt="%d-%b-%y %H:%M:%S",
)

if __name__ == "__main__":
    logger.info("Starting SM NMR preparation.")
    json_path = PATHS["NMR_data"] / "INPUT" / f"{NAME}.json"
    data_path = PATHS["NMR_data"] / f"{TODAY}-{NAME}" / "DATA" / "NMR"

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    archive_path = PATHS["NMR_archive"] / f"{NAME}" / "DATA" / "NMR"

    if not archive_path.exists():
        archive_path.mkdir(parents=True, exist_ok=True)

    nmr_summary_path = json_path.with_name(f"{NAME}-NMR.json")

    acquire_batch(
        samples=json_path,
        name=NAME,
        data_path=data_path,
        dry=DRY,
    )
    samples = SampleBatch.from_file(json_path)

    sm_data: dict[str, dict[str, list[float]]] = {}

    for sample in samples:
        logger.info(f"Analysing NMR of {NAME}-{sample.position:02d}.")
        nmr_path = data_path / f"{NAME}-{sample.position:02d}"
        nmr = NMRExperiment(FOURIER.open_experiment(nmr_path))

        nmr.process_spectrum(
            zero_filling="8k",
            line_broadening=1.2,
            reference=True,
        )

        peaks_ppm = nmr.pick_peaks(
            reference_intensity=150,
            minimum_intensity=10,
            sensitivity=1,
        )

        sm_data[str(sample.sample_info)] = {
            "peaks_ppm": peaks_ppm,
        }

        nmr.export_jcampdx(
            export_path=archive_path
            / f"{NAME}-{str(sample.sample_info).upper()}.dx",
            export_all=False,
        )

    with open(nmr_summary_path, "w", newline="\n") as f:
        json.dump(sm_data, f, indent=4)
