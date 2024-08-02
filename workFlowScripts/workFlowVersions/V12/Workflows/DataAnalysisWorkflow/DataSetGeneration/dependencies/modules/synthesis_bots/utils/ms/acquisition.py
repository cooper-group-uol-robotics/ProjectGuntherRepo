"""Main LCMS acquisition functions."""

import logging
import time
from pathlib import Path
from shutil import copy

from dependencies.modules.synthesis_bots.utils.constants import PATHS

logger = logging.getLogger(__name__)


def acquire_lcms(queue_csv: Path) -> None:
    """
    Acquire LC-MS spectra (exectue queue instructions).

    Acquity LC-MS watches the Queue folder and executes any new csv file
    added there. Once the queue execution has finished, the csv file is moved.

    Parameters
    ----------
    queue_csv
        Path to the CSV containing queue information.

    """
    logger.info(f"Loading LC-MS queue information from {queue_csv}.")
    copy(queue_csv, PATHS["LCMS_queue"] / queue_csv.name)

    while True:
        time.sleep(10)
        if not any(PATHS["LCMS_queue"].iterdir()):
            logger.info("LCMS queue execution completed.")
            return None
        else:
            continue
