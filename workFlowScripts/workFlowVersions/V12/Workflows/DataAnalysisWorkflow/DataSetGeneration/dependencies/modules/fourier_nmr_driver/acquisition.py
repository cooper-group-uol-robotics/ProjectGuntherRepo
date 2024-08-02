"""
Acquire a batch of NMRs described by a TOML or JSON file.

Example TOML and JSON can be found in the `examples` folder.

"""

import json
import logging
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Iterable,
    Optional,
)

logger = logging.getLogger(__name__)


def reshim() -> None:
    """
    Reshim the magnet.

    Parameters
    ----------
    shim_sample
        Position of the shim sample in the rack.
    shim_time
        Shimming time.

    """
    from fourier_nmr_driver.__main__ import (
        FOURIER,
        NMR_SETUP,
    )

    FOURIER.change_sample(NMR_SETUP.shim_sample)
    logger.info("Shim sample inserted.")
    time.sleep(NMR_SETUP.wait_time)
    FOURIER.start_shimming()
    logger.info("Shimming procedure started.")
    time.sleep(NMR_SETUP.shim_time)
    FOURIER.stop_shimming()
    logger.info("Quick shim procedure stopped. Resuming acquisition.")


@dataclass
class AcquisitionParameters:
    """A class containing acquisition parameters."""

    parameters: str
    num_scans: int
    l30: Optional[int] = None
    pp_threshold: Optional[float] = None
    field_presat: Optional[float] = None


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
        samples_path = Path(samples_path)
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
        from fourier_nmr_driver.__main__ import NMR_DEFAULTS

        samples = []
        for position, info in samples_dict.items():
            experiments = []
            for exp in info["nmr_experiments"]:
                if type(exp) is str:
                    experiment = AcquisitionParameters(
                        parameters=exp,
                        num_scans=NMR_DEFAULTS.num_scans,
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

                    if exp["parameters"] == "MULTISUPPDC_f":
                        if "pp_threshold" in exp:
                            experiment.pp_threshold = exp["pp_threshold"]
                        else:
                            experiment.pp_threshold = NMR_DEFAULTS.pp_threshold

                        if "field_presat" in exp:
                            experiment.field_presat = exp["field_presat"]
                        else:
                            experiment.field_presat = NMR_DEFAULTS.field_presat

                    elif exp["parameters"] == "K_WETDC":
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
                experiments=experiments,
                solvent=info["solvent"]
                if "solvent" in info
                else NMR_DEFAULTS.solvent,
                sample_info=info["sample_info"]
                if "sample_info" in info
                else NMR_DEFAULTS.sample_info,
            )

            samples.append(sample)

        return cls(samples)


def acquire_batch(
    samples_path: Path,
    name: str,
    data_path: Path,
    dry: bool = False,
) -> None:
    """
    Acquire a batch of NMR spectra.

    Parameters
    ----------
    samples
        SampleBatch containing experiment requirements.
    name
        Name of the samples batch (used for experiment folder names).
    data_path
        Path to where the data will be saved.
    dry, optional
        If True, no actual spectrometer command will be sent.

    """
    from fourier_nmr_driver.__main__ import (
        FOURIER,
        NMR_SETUP,
        RACKS,
    )

    samples = SampleBatch.from_file(samples_path)

    for sample in samples:
        # Re-shim if needed
        if not dry:
            if time.time() - FOURIER.last_shim > NMR_SETUP.reshim_time:
                logger.info("Too much time since last shim - reshimming.")
                reshim()

        if 1 <= sample.position <= len(RACKS):
            pal_position = RACKS[sample.position - 1]
            logger.debug(
                f"Sample will be inserted from PAL position {sample.position}."
            )

        else:
            raise ValueError("No such rack position exists.")

        if not dry:
            FOURIER.change_sample(pal_position)

        logger.info(
            f"Sample {name}-{sample.position:02d} inserted from "
            f"rack position {sample.position:02d}."
        )

        if not dry:
            time.sleep(NMR_SETUP.wait_time)

        for n, experiment in enumerate(sample.experiments):
            title = "\n".join(
                [
                    f"{name}-{sample.position:02d}",
                    f"{sample.sample_info}",
                    experiment.parameters,
                ]
            )

            if not dry:
                exp = FOURIER.new_experiment(
                    path=data_path,
                    exp_name=f"{name}-{sample.position:02d}",
                    exp_num=10 * (n + 1),
                    title=title,
                    solvent=sample.solvent,
                    parameters=experiment.parameters,
                    getprosol=True,
                    overwrite=True,
                )
                FOURIER.lock(exp)
                logger.info("Locking Fourier80 has finished.")
                exp.number_scans = experiment.num_scans
                logger.info(
                    f"Number of scans for experiment {experiment.parameters} "
                    f"(expno {10 * (n + 1)}) on sample "
                    f"{name}-{sample.position:02d} is {experiment.num_scans}."
                )

                match experiment.parameters:
                    case "K_WETDC":
                        exp.nmr_data.launch(f"L30 {experiment.l30}")
                        logger.info(f"K_WETDC: L30 set to {experiment.l30}.")
                        exp.nmr_data.launch("xaua")
                    case "MULTISUPPDC_f":
                        logger.info(
                            "MULTISUPPDC_f: presaturation of "
                            f"{experiment.field_presat} and peak picking "
                            f"threshold {experiment.pp_threshold}."
                        )
                        exp.nmr_data.launch(
                            "multisupp13c --c13_decouple bb "
                            f"--fieldpresat {experiment.field_presat} "
                            f"--threshold_pp {experiment.pp_threshold}"
                        )
                    case _:
                        exp.nmr_data.launch("xaua")
            logger.info(f"Experiment {experiment.parameters} completed.")

        logger.info(
            f"Experiments on sample {name}-{sample.position:02d} completed."
        )
    logger.info(f"All spectra acquired for batch '{name}'.")
