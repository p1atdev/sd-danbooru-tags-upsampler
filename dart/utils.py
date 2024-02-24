import logging
import random


from modules.processing import (
    StableDiffusionProcessingTxt2Img,
    StableDiffusionProcessingImg2Img,
)


logger = logging.getLogger(__name__)

SEED_MIN = 0
SEED_MAX = 2**32 - 1


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
        all_subseeds = [int(custom_seed) + i for i in range(num_seeds)]
    else:
        all_subseeds = [subseed + i for i in range(num_seeds)]

    return all_subseeds
