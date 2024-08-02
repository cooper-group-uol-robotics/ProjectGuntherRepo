"""Constants shared across Synthesis Bots."""

import functools
import logging
import tomllib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


#Getting the current working directory.
rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])

logger = logging.getLogger(__name__)

TODAY = datetime.today().strftime("%Y-%m-%d")

tomlPath = strCWD + '/Data/settings.toml'
with open(Path(tomlPath), "rb") as f:
    SETTINGS = tomllib.load(f)

LOGPATH = Path(f"{TODAY}.log")
try:
    WORKFLOWS: dict[str, dict[str, str]] = SETTINGS["workflows"]
    DRY = SETTINGS["dry"]["dry"]
    PATHS = {str(name): Path(path) for name, path in SETTINGS["paths"].items()}
    PREFIX = SETTINGS["workflows"]["PREFIX"]

except KeyError as e:
    logger.error(f"Cannot find setting for {e}.")
    raise KeyError(e)


class NMRRackLayouts:
    """Constants namespace for rack layouts."""

    __slots__ = ()
    KUKARACK1 = [
        *range(40, 46),
        *range(48, 54),
        *range(56, 62),
    ]

    KUKARACK2 = [
        *range(16, 22),
        *range(24, 30),
        *range(32, 38),
    ]

    PALRACK1 = [*range(15, 39)]
    PALRACK2 = [*range(39, 63)]

    @classmethod
    def get_racks(cls, layout: str) -> tuple[int, ...]:
        """
        Get rack layout.

        Returns actual PAL gripper positions for each rack position.

        Parameters
        ----------
        layout
            Currently implemented "KUKA" and "PAL" racks.

        Returns
        -------
            List of lists with the corresponding sample positions.

        Raises
        ------
        ValueError
            Incorrect rackk configuration.

        """
        match layout.upper():
            case "KUKA":
                return (*NMRRackLayouts.KUKARACK1, *NMRRackLayouts.KUKARACK2)
            case "PAL":
                return (*NMRRackLayouts.PALRACK1, *NMRRackLayouts.PALRACK2)
            case _:
                raise ValueError("Invalid rack configuration.")


def use_settings(function):
    """Wrapper to handle missing settings keys."""

    @functools.wraps(function)
    def __wrapper_use_settings(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except KeyError as e:
            logger.error(f"Cannot find setting for {e}.")
            raise KeyError(e)

    return __wrapper_use_settings


@dataclass
class NMRDefaults:
    """Namespace for default aquisition parameters."""

    try:
        parameters: str = SETTINGS["defaults"]["NMR"]["parameters"]
        solvent: str = SETTINGS["defaults"]["NMR"]["solvent"]
        num_scans: int = SETTINGS["defaults"]["NMR"]["num_scans"]
        sample_info: str = "NMR_Sample"
        pp_threshold: float = SETTINGS["defaults"]["NMR"]["pp_threshold"]
        field_presat: int = SETTINGS["defaults"]["NMR"]["field_presat"]
        l30: int = SETTINGS["defaults"]["NMR"]["l30"]
    except KeyError as e:
        logger.error(f"Cannot find setting for {e}.")
        raise KeyError(e)


@dataclass
class NMRSetup:
    """Namespace for NMR setup."""

    try:
        shim_sample: int = SETTINGS["defaults"]["NMR"]["shim_sample"]
        wait_time: int = SETTINGS["defaults"]["NMR"]["wait_time"]
        rack_layout: tuple[int, ...] = NMRRackLayouts.get_racks(
            layout=SETTINGS["defaults"]["NMR"]["rack_layout"]
        )
        shim_time: int = SETTINGS["defaults"]["NMR"]["shim_time"]
        reshim_time: int = SETTINGS["defaults"]["NMR"]["reshim_time"]
        owner: str = SETTINGS["defaults"]["NMR"]["owner"]
        origin: str = SETTINGS["defaults"]["NMR"]["origin"]
    except KeyError as e:
        logger.error(f"Cannot find setting for {e}.")
        raise KeyError(e)


NMR_SETUP = NMRSetup()
NMR_DEFAULTS = NMRDefaults()
