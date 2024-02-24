import logging


import gradio as gr
from transformers import set_seed

from modules import script_callbacks
import modules.scripts as scripts
from modules.scripts import basedir
from modules.processing import (
    StableDiffusionProcessingTxt2Img,
    StableDiffusionProcessingImg2Img,
)
from modules.shared import opts

from dart.generator import DartGenerator
from dart.analyzer import DartAnalyzer
from dart.settings import on_ui_settings, parse_options
import dart.utils as utils
from dart.utils import SEED_MAX

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


TOTAL_TAG_LENGTH = {
    "VERY_SHORT": "very short",
    "SHORT": "short",
    "LONG": "long",
    "VERY_LONG": "very long",
}

TOTAL_TAG_LENGTH_TAGS = {
    TOTAL_TAG_LENGTH["VERY_SHORT"]: "<|very_short|>",
    TOTAL_TAG_LENGTH["SHORT"]: "<|short|>",
    TOTAL_TAG_LENGTH["LONG"]: "<|long|>",
    TOTAL_TAG_LENGTH["VERY_LONG"]: "<|very_long|>",
}

PROCESSING_TIMING = {
    "BEFORE": "Before applying styles",
    "AFTER": "After applying styles",
}

extension_dir = basedir()


def _concatnate_texts(prefix: list[str], suffix: list[str]) -> list[str]:
    return [
        ", ".join([part for part in [prompt, suffix[i]] if part.strip() != ""])
        for i, prompt in enumerate(prefix)
    ]


class DartUpsampleScript(scripts.Script):
    generator: DartGenerator
    analyzer: DartAnalyzer

    def __init__(self):
        super().__init__()

        self.options = parse_options(opts)

        self.generator = DartGenerator(
            self.options["model_name"],
            self.options["tokenizer_name"],
            self.options["model_backend_type"],
        )
        self.analyzer = DartAnalyzer(
            extension_dir,
            self.generator.get_vocab_list(),
            self.generator.get_special_vocab_list(),
        )

        if self.options["debug_logging"]:
            # global logger
            logger.setLevel(logging.DEBUG)

        script_callbacks.on_ui_settings(on_ui_settings)

    def title(self):
        return "Danbooru Tags Upsampler"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):

        with gr.Accordion(open=False, label=self.title()):
            with gr.Column():
                enabled_check = gr.Checkbox(label="Enabled", value=False)

                tag_length_radio = gr.Radio(
                    label="Total tag length",
                    choices=list(TOTAL_TAG_LENGTH.values()),
                    value=TOTAL_TAG_LENGTH["LONG"],
                )
                ban_tags_textbox = gr.Textbox(
                    label="Ban tags",
                    value="",
                    placeholder="official alternate costume, english text, ...",
                )

                with gr.Group():
                    with gr.Row():
                        seed_num_input = gr.Number(
                            label="Seed for upsampling tags",
                            minimum=-1,
                            maximum=SEED_MAX,
                            step=1,
                            scale=4,
                            value=-1,
                        )
                        seed_random_btn = gr.Button(value="Randomize")
                        seed_shuffle_btn = gr.Button(value="Shuffle")

                        def click_random_seed_btn():
                            return -1

                        seed_random_btn.click(
                            click_random_seed_btn, outputs=[seed_num_input]
                        )

                        def click_shuffle_seed_btn():
                            return utils.get_random_seed()

                        seed_shuffle_btn.click(
                            click_shuffle_seed_btn, outputs=[seed_num_input]
                        )

                with gr.Group():
                    process_timing_dropdown = gr.Dropdown(
                        label="Upsampling timing",
                        choices=list(PROCESSING_TIMING.values()),
                        value=PROCESSING_TIMING["BEFORE"],
                    )

        return [
            enabled_check,
            tag_length_radio,
            ban_tags_textbox,
            seed_num_input,
            process_timing_dropdown,
        ]

    def process(
        self,
        p: StableDiffusionProcessingTxt2Img | StableDiffusionProcessingImg2Img,
        is_enabled: bool,
        tag_length: str,
        ban_tags: str,
        seed_num: int,
        process_timing: str,
    ):
        if not is_enabled:
            return

        if process_timing != PROCESSING_TIMING["AFTER"]:
            return

        analyzing_results = [self.analyzer.analyze(prompt) for prompt in p.all_prompts]

        upsampling_prompt = [
            self.generator.compose_prompt(
                rating=f"{result.rating_parent}, {result.rating_child}",
                copyright=result.copyright,
                character=result.character,
                general=result.general,
                length=TOTAL_TAG_LENGTH_TAGS[tag_length],
            )
            for result in analyzing_results
        ]
        logger.debug(f"Upsampling prompt: {upsampling_prompt}")
        bad_words_ids = self.generator.get_bad_words_ids(ban_tags)

        num_images = p.n_iter * p.batch_size
        upsampling_seeds = utils.get_upmsapling_seeds(
            p,
            num_images,
            custom_seed=seed_num,
        )

        # this list has only 1 item
        upsampled_tags = self.upsample_tags(
            upsampling_prompt,
            seeds=upsampling_seeds,
            bad_words_ids=bad_words_ids,
        )
        logger.debug(f"Upsampled tags: {upsampled_tags}")

        # set new prompts
        p.all_prompts = _concatnate_texts(p.all_prompts, upsampled_tags)

    def before_process(
        self,
        p: StableDiffusionProcessingTxt2Img | StableDiffusionProcessingImg2Img,
        is_enabled: bool,
        tag_length: str,
        ban_tags: str,
        seed_num: int,
        process_timing: str,
    ):
        if not is_enabled:
            return

        if process_timing != PROCESSING_TIMING["BEFORE"]:
            return

        analyzing_result = self.analyzer.analyze(p.prompt)

        upsampling_prompt = self.generator.compose_prompt(
            rating=f"{analyzing_result.rating_parent}, {analyzing_result.rating_child}",
            copyright=analyzing_result.copyright,
            character=analyzing_result.character,
            general=analyzing_result.general,
            length=TOTAL_TAG_LENGTH_TAGS[tag_length],
        )
        logger.debug(f"Upsampling prompt: {upsampling_prompt}")
        bad_words_ids = self.generator.get_bad_words_ids(ban_tags)

        upsampling_seeds = utils.get_upmsapling_seeds(
            p,
            num_seeds=1,  # only for the first prompt
            custom_seed=seed_num,
        )

        # this list has only 1 item
        upsampled_tags = self.upsample_tags(
            [upsampling_prompt],
            seeds=upsampling_seeds,
            bad_words_ids=bad_words_ids,
        )
        logger.debug(f"Upsampled tags: {upsampled_tags}")

        # set a new prompt
        p.prompt = _concatnate_texts([p.prompt], upsampled_tags)[0]

    def upsample_tags(
        self,
        prompts: list[str],
        seeds: list[int],
        bad_words_ids: list[list[int]] | None = None,
    ) -> list[str]:
        if len(prompts) == 1 and len(prompts) != len(seeds):
            prompts = prompts * len(seeds)

        upsampled_tags = []
        for prompt, seed in zip(prompts, seeds, strict=True):
            set_seed(seed)
            upsampled_tags.append(
                self.generator.generate(prompt, bad_words_ids=bad_words_ids)
            )
        return upsampled_tags
