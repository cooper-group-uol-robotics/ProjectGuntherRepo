"""Decision maker for being different from the reagents."""

import logging
from itertools import chain

from dependencies.modules.synthesis_bots.utils.constants import SETTINGS

logger = logging.getLogger(__name__)


def main(
    reaction_peaks: list[float],
    reagents_list: list[list[float]],
) -> bool:
    """Make the decisions."""
    criteria = SETTINGS["workflows"]["decision"]
    reagents_peaks = list(set(chain(*reagents_list)))

    # Check if there are too many or too few peaks.
    if (diff := abs(len(reagents_peaks) - len(reaction_peaks))) > criteria[
        "peak_number"
    ]:
        logger.info(f"Peak number criterion FAILED: {diff} peaks difference.")
        return False

    logger.info(f"Peak number criterion PASSED: {diff} peaks difference.")

    # Check if peaks have shifted in values.
    reaction_set = {round(x, 2) for x in reaction_peaks}

    for peak in reagents_peaks:
        reaction_set.discard(round(peak, 2))
        logger.debug(f"Removing {round(peak, 2)}.")

    if len(reaction_set) < 0.5 * len(reagents_peaks):
        logger.info(
            f"Not enough peaks moved: {len(reaction_set)} are different."
        )
        return False

    logger.info(
        f"Peak shift criterion PASSED: {len(reaction_set)} are different."
    )

    return True
