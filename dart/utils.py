import logging
import random
import re

from modules.processing import (
    StableDiffusionProcessingTxt2Img,
    StableDiffusionProcessingImg2Img,
)


logger = logging.getLogger(__name__)

SEED_MIN = 0
SEED_MAX = 2**32 - 1

# webuiの特殊な挙動をするタグ
SPECIAL_SYMBOL_PATTERN = re.compile(r"([()])")

# escaped and unescaped symbols pair to unescaping processing
ESCAPED_SYMBOL_PATTERNS = {re.compile(r"\\\("): "(", re.compile(r"\\\)"): ")"}


def get_random_seed():
    return random.randint(SEED_MIN, SEED_MAX)


# ref: https://github.com/adieyal/sd-dynamic-prompts/blob/main/sd_dynamic_prompts/helpers.py
def get_upmsapling_seeds(
    p: StableDiffusionProcessingTxt2Img | StableDiffusionProcessingImg2Img,
    num_seeds: int,
    custom_seed: int,
) -> list[int]:
    if p.subseed_strength != 0:
        subseed = int(p.all_subseeds[0])
    else:
        subseed = int(p.subseed)

    if subseed == -1:
        subseed = get_random_seed()

    if custom_seed != -1:
        # if custom_seed is specified, use the same seeds for prompts
        all_subseeds = [int(custom_seed)] * num_seeds
    else:
        # increase randomness by adding images' seeds
        all_subseeds = [
            (int(p.seed) + subseed + i) % SEED_MAX for i in range(num_seeds)
        ]

    return all_subseeds


def escape_special_symbols(tags: list[str]) -> list[str]:
    """Returns tags only which has brackets escaped."""

    escaped_tags = [SPECIAL_SYMBOL_PATTERN.sub(r"\\\1", tag) for tag in tags]

    return escaped_tags


def unescape_special_symbols(tags: list[str]) -> list[str]:
    """Returns all tags after unescaping."""
    unescaped_tags = []

    for tag in tags:
        for pattern, replace_to in ESCAPED_SYMBOL_PATTERNS.items():
            tag = pattern.sub(replace_to, tag)

        unescaped_tags.append(tag)

    return unescaped_tags
