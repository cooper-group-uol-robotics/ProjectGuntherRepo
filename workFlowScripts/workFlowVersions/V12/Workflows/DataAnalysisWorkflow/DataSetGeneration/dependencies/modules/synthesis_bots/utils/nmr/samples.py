"""Classes dealing with NMR samples."""

import json
import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dependencies.modules.synthesis_bots.utils.constants import (
    NMR_DEFAULTS,
    use_settings,
)

logger = logging.getLogger(__name__)


@dataclass
class AcquisitionParameters:
    """A class containing acquisition parameters."""

    parameters: str
    num_scans: int
    l30: int = NMR_DEFAULTS.l30
    pp_threshold: float = NMR_DEFAULTS.pp_threshold
    field_presat: float = NMR_DEFAULTS.field_presat


@dataclass
class NMRSample:
    """A class containing sample information."""

    position: int
    experiments: Iterable[AcquisitionParameters]
    solvent: str
    sample_info: str | dict


class SampleBatch:
    """A class containing a batch of samples."""

    def __init__(self, samples: Iterable[NMRSample]):
        """
        Initialise SampleBatch.

        Parameters
        ----------
        samples
            A list of NMR samples.

        """
        self.samples = list(samples)

    def __getitem__(self, index):
        return self.samples[index]

    def __len__(self):
        return len(self.samples)

    def __iter__(self):
        return iter(self.samples)

    @classmethod
    def from_file(
        cls,
        samples_path: Path,
    ):
        """
        Initialise SampleBatch from a TOML or JSON file.

        Parameters
        ----------
        samples_path
            Path to the file containing batch information.

        """
        match samples_path.suffix:
            case ".toml":
                with open(samples_path, "rb") as f:
                    samples = tomllib.load(f)
                    logger.info(f"Loaded {len(samples)} sample request(s).")

            case ".json":
                with open(samples_path, "r") as f:
                    samples = json.load(f)
                    logger.info(f"Loaded {len(samples)} sample request(s).")

            case _:
                logger.critical("Only TOML or JSON files are supported.")
                raise NotImplementedError(
                    "Only TOML or JSON files are supported."
                )

        return cls.from_dict(samples)

    @classmethod
    @use_settings
    def from_dict(
        cls,
        samples_dict: dict,
    ):
        """
        Generate SampleBatch from a dictionary.

        Parameters
        ----------
        samples_dict
            A dictionary containing batch information.

        """
        samples = []

        for position, info in samples_dict.items():
            experiments = []
            for exp in info["nmr_experiments"]:
                if type(exp) is str:
                    experiment = AcquisitionParameters(
                        parameters=exp, num_scans=NMR_DEFAULTS.num_scans
                    )

                elif type(exp) is dict:
                    try:
                        experiment = AcquisitionParameters(
                            parameters=exp["parameters"],
                            num_scans=NMR_DEFAULTS.num_scans,
                        )

                    except KeyError:
                        logging.error(
                            f"Unknown parameter set for sample {position} "
                            f"- using {NMR_DEFAULTS.parameters}."
                        )
                        experiment = AcquisitionParameters(
                            parameters=NMR_DEFAULTS.parameters,
                            num_scans=NMR_DEFAULTS.num_scans,
                        )

                    if "num_scans" in exp:
                        experiment.num_scans = exp["num_scans"]

                    if experiment.parameters == "MULTISUPPDC_f":
                        if "pp_threshold" in exp:
                            experiment.pp_threshold = exp["pp_threshold"]
                        else:
                            experiment.pp_threshold = NMR_DEFAULTS.pp_threshold

                        if "field_presat" in exp:
                            experiment.field_presat = exp["field_presat"]
                        else:
                            experiment.field_presat = NMR_DEFAULTS.field_presat

                    elif experiment.parameters == "K_WETDC":
                        if "l30" in exp:
                            experiment.l30 = exp["l30"]
                        else:
                            experiment.l30 = NMR_DEFAULTS.l30

                else:
                    logger.error("Wrong experiment format in the batch file.")
                    raise (
                        TypeError(
                            "Experiment must map to a string or a dictionary."
                        )
                    )

                experiments.append(experiment)

            sample = NMRSample(
                position=int(position),
                solvent=info["solvent"]
                if "solvent" in info
                else NMR_DEFAULTS.solvent,
                sample_info=info["sample_info"]
                if "sample_info" in info
                else NMR_DEFAULTS.sample_info,
                experiments=experiments,
            )

            samples.append(sample)

        return cls(samples)
