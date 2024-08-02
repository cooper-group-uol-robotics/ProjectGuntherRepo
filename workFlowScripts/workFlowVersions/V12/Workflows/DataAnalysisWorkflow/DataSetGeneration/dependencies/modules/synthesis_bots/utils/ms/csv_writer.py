"""Writer for queue CSV filed read by Acquity LC-MS."""

import csv
import json
import logging
from pathlib import Path

from dependencies.modules.synthesis_bots.utils.constants import SETTINGS

logger = logging.getLogger(__name__)


def write_csv(
    samples_json: Path,
    csv_path: Path,
    tune_file: str,
    blank: bool = False,
) -> None:
    """
    Write CSV for the LC-MS queue.

    Parameters
    ----------
    samples_json
        A path to the JSON file with sample information.
    csv_path
        A path to where the queue CSV is to be saved.
    tune_file
        LC-MS tune file name.

    """
    with open(samples_json, "r") as f:
        samples = json.load(f)

        logger.info(
            f"Loaded {samples_json.name} " f"with {len(samples)} experiments."
        )

        logger.info(f"Using tune file: {tune_file}.")

        with open(csv_path, "w", newline="") as file:
            fields = [
                "INDEX",
                "FILE_NAME",
                "FILE_TEXT",
                "MS_FILE",
                "MS_TUNE_FILE",
                "INLET_FILE",
                "SAMPLE_LOCATION",
                "INJ_VOL",
            ]
            writer = csv.DictWriter(file, fieldnames=fields)

            writer.writeheader()

            index = 1
            for sample in samples.keys():
                if blank:
                    writer.writerow(
                        {
                            "INDEX": index,
                            "FILE_NAME": f"BLANK{index}",
                            "FILE_TEXT": f"BLANK{index}",
                            "MS_FILE": tune_file,
                            "MS_TUNE_FILE": tune_file,
                            "INLET_FILE": tune_file,
                            "SAMPLE_LOCATION": "2:48",
                            "INJ_VOL": SETTINGS["defaults"]["MS"][
                                "injection_volume"
                            ],
                        }
                    )
                    index += 1

                sample_id = int(sample)
                writer.writerow(
                    {
                        "INDEX": index,
                        "FILE_NAME": sample_id,
                        "FILE_TEXT": sample_id,
                        "MS_FILE": tune_file,
                        "MS_TUNE_FILE": tune_file,
                        "INLET_FILE": tune_file,
                        "SAMPLE_LOCATION": f"2:{sample_id:02d}",
                        "INJ_VOL": SETTINGS["defaults"]["MS"][
                            "injection_volume"
                        ],
                    }
                )
                index += 1

        logger.info(f"Finished writing the queue to {csv_path}.")
