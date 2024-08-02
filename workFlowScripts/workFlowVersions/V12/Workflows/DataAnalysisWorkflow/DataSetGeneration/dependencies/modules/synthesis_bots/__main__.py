"""
Package-level entry point for the Synthesis Bots.

When extending, make sure that a new main function is added for the
instrument type.

"""

import logging
import sys
from importlib.util import find_spec

from synthesis_bots.utils.constants import (
    LOGPATH,
    SETTINGS,
)
from synthesis_bots.utils.entity import (
    Instrument,
    WorkflowEntity,
)

logging.captureWarnings(True)
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    filename=LOGPATH,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s (%(name)s)",
    datefmt="%d-%b-%y %H:%M:%S",
)


def main():
    """Main entry point for the code."""
    if len(sys.argv) != 2:
        print(
            "Please call the programme with LCMS or NMR as the only argument."
        )
        logging.critical("Must supply instrument name as argument!")
        sys.exit(1)

    elif sys.argv[1] == "NMR":
        module = find_spec("fourier_nmr_driver")
        if module is None:
            logger.critical("No NMR driver installed.")
            raise ImportError("fourier_nmr_driver not found.")

        nmr = WorkflowEntity(
            instrument_address=SETTINGS["tcp"]["NMR"],
            host_address=SETTINGS["tcp"]["HOST"],
            instrument=Instrument.NMR,
        )

        nmr.connect()
        sys.exit(nmr.await_command())

    elif sys.argv[1] == "LCMS":
        module = find_spec("lcms_parser")
        if module is None:
            logger.critical("No LCMS parser installed.")
            raise ImportError("lcms_parser not found.")

        lcms = WorkflowEntity(
            instrument_address=SETTINGS["tcp"]["LCMS"],
            host_address=SETTINGS["tcp"]["HOST"],
            instrument=Instrument.LCMS,
        )

        lcms.connect()
        sys.exit(lcms.await_command())

    else:
        logging.critical("Instrument not implemented: please use LCMS or NMR.")
        print("Instrument not implemented: please use LCMS or NMR.")


if __name__ == "__main__":
    logger.info(f"Starting code in {__name__}.")

    main()
