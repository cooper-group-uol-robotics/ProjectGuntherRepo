"""Main NMR acquisition functions."""

import logging
import time
from pathlib import Path

from dependencies.modules.fourier_nmr_driver import Fourier80

from dependencies.modules.synthesis_bots.utils.constants import (
    DRY,
    NMR_SETUP,
    use_settings,
)
from dependencies.modules.synthesis_bots.utils.nmr.samples import (
    AcquisitionParameters,
    NMRSample,
    SampleBatch,
)

logger = logging.getLogger(__name__)

FOURIER = Fourier80()


@use_settings
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
    FOURIER.change_sample(NMR_SETUP.shim_sample)
    logger.info("Shim sample inserted.")
    time.sleep(NMR_SETUP.wait_time)
    FOURIER.start_shimming()
    logger.info("Shimming procedure started.")
    time.sleep(NMR_SETUP.shim_time)
    FOURIER.stop_shimming()
    logger.info("Quick shim procedure stopped. Resuming acquisition.")


def acquire_nmr(
    experiment: AcquisitionParameters,
    sample: NMRSample,
    experiment_name: str,
    data_path: Path,
    expno: int = 10,
    dry: bool = DRY,
) -> None:
    """
    Acquire an NMR spectrum.

    Parameters
    ----------
    experiment
        Experiment containing the acquisiton parameters.
    sample
        Sample information.
    experiment_name
        Name of the experiment (used for TopSpin path creation).
    data_path
        Path to the directory where the data will be saved.
    expno, optional
        Experiment number (TopSpin expno parameter), by default 10.
    dry, optional
        If dry, no spectra will be run, by default False

    """
    title = "\n".join(
        [
            experiment_name,
            f"{sample.sample_info}",
            experiment.parameters,
        ]
    )

    if not dry:
        exp = FOURIER.new_experiment(
            path=data_path,
            exp_name=experiment_name,
            exp_num=expno,
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
            f"(expno {expno}) on sample "
            f"{experiment_name} is {experiment.num_scans}."
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


def acquire_batch(
    samples: Path,
    name: str,
    data_path: Path,
    dry: bool = DRY,
) -> None:
    """
    Acquire a batch of NMR spectra.

    Parameters
    ----------
    samples
        Path to a JSON or TOML describing the sample batch.
    name
        Name of the samples batch (used for experiment folder names).
    data_path
        Path to where the data will be saved.
    dry, optional
        If True, no actual spectrometer command will be sent.

    """
    logger.info(
        f"Shim sample in reference rack position {NMR_SETUP.shim_sample}."
    )
    logger.info(f"Shimming every {NMR_SETUP.reshim_time / 3600:.2f} hours.")
    logger.info(
        f"Shimming time will be {NMR_SETUP.shim_time / 60:.2f} minutes."
    )
    if not dry:
        FOURIER.stop_shimming()
        logger.info("Quickshim procedure completed.")

    for sample in SampleBatch.from_file(samples):
        # Re-shim if needed
        if not dry:
            if time.time() - FOURIER.last_shim > NMR_SETUP.reshim_time:
                logger.info("Too much time since last shim - reshimming.")
                reshim()

        if 1 <= sample.position <= len(NMR_SETUP.rack_layout):
            pal_position = NMR_SETUP.rack_layout[sample.position - 1]
            logger.debug(
                f"Sample will be inserted from PAL position {pal_position}."
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
            acquire_nmr(
                experiment=experiment,
                sample=sample,
                experiment_name=f"{name}-{sample.position:02d}",
                data_path=data_path,
                expno=10 * (n + 1),
                dry=dry,
            )
            time.sleep(5)

    logger.info(f"All spectra acquired for batch '{name}'.")

    if not dry:
        FOURIER.change_sample(NMR_SETUP.shim_sample)
        logger.info(
            f"Shim sample inserted (position {NMR_SETUP.shim_sample})."
        )
        FOURIER.start_shimming()
        logger.info("Started the quickshim procedure.")
