"""Collections of constants for Bruker Topspin."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class NMRSetup:
    """Namespace for NMR setup."""

    shim_sample: int = 1
    wait_time: int = 120
    rack_layout: Literal["PAL", "KUKA"] = "PAL"
    shim_time: int = 1200
    reshim_time: int = 10800


@dataclass
class NMRDefaults:
    """Namespace for default aquisition parameters."""

    samples_file: str = "samples.toml"
    parameters: str = "PROTON_f"
    solvent: str = "CDCL3"
    num_scans: int = 8
    sample_info: str = "NMR_Sample"
    pp_threshold: float = 0.01
    field_presat: int = 10
    l30: int = 2


PARAMS = {
    "C13CPD_f",
    "C13DEPT135_f",
    "C13DEPT45_f",
    "C13DEPT90_f",
    "COSYGP_f",
    "COSYPP_f",
    "COSY_f",
    "HMBC_f",
    "HMBCGP_f",
    "HSQC_f",
    "HSQC_lr_f",
    "HSQCED_f",
    "HSQCEDGP_f",
    "HSQCGP_f",
    "JRES_f",
    "K_WET_f",
    "K_WETDC_f",
    "MULTISUPPDC_f",
    "MULTISUPP_f",
    "PROTON_f",
    "PROTON64_f",
    "Supression_f",
    "T1_f",
    "T2_f",
}

SOLVENTS = {
    "ACETIC",
    "ACETONE",
    "C6D6",
    "CD2CL2",
    "CD3CN",
    "CD3CN_SPE",
    "CD3OD_SPE",
    "CDCL3",
    "CH2CL2",
    "CH3CN",
    "CH3CN+D2O",
    "CH3OH",
    "CH3OH+D2O",
    "D2O",
    "D2O_SALT",
    "DIOXANE",
    "DMF",
    "DMSO",
    "DMSO-H6",
    "ETOD",
    "H2O",
    "H2O+D2O",
    "H2O+D2O_SALT",
    "HDMSO",
    "JUICE",
    "MEOD",
    "NONE",
    "OC6D4CL2",
    "OC6D4BR2",
    "PLASMA",
    "PYR",
    "T_H2O+D2O+ME4NCL",
    "T_H2O+D2O+NAAC",
    "T_H2O+D2O+PIVALATE",
    "T_MEOD",
    "TFE",
    "THF",
    "THF-H8",
    "TOL",
    "TOL-H8",
    "URINE",
}


class RackLayouts:
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
    def get_racks(cls, layout: str) -> list[int]:
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
            Incorrect rack configuration.

        """
        match layout.upper():
            case "KUKA":
                return [*RackLayouts.KUKARACK1, *RackLayouts.KUKARACK2]
            case "PAL":
                return [*RackLayouts.PALRACK1, *RackLayouts.PALRACK2]
            case _:
                raise ValueError("Invalid rack configuration.")
