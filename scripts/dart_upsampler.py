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
    "BEFORE": "Before applying other prompt processings",
    "AFTER": "After applying other prompt processings",
}

VARIETY_OPTIONS = {
    "VERY_UNVARIED": "very unvaried",
    "UNVARIED": "unvaried",
    "NORMAL": "normal",
    "VARIED": "varied",
    "VERY_VARIED": "very varied",
}
# value: kye
VARIETY_OPTIONS_VK = {v: k for k, v in VARIETY_OPTIONS.items()}

VARIETY_PRESETS = {
    # [temperature, top_p, top_k, num_beams]
    "VERY_UNVARIED": [0.85, 0.9, 20, 2],
    "UNVARIED": [0.9, 0.95, 20, 1],
    "NORMAL": [1.0, 1, 30, 1],
    "VARIED": [1.5, 1, 50, 1],
    "VERY_VARIED": [2.0, 0.9, 100, 1],
}

extension_dir = basedir()


def _join_texts(prefix: str, suffix: str) -> str:
    return ", ".join([part for part in [prefix, suffix] if part.strip() != ""])


def _concatnate_texts(prefix: list[str], suffix: list[str]) -> list[str]:
    return [_join_texts(prompt, suffix[i]) for i, prompt in enumerate(prefix)]


class DartUpsampleScript(scripts.Script):
    generator: DartGenerator
    analyzer: DartAnalyzer

    def __init__(self):
        super().__init__()

        self.options = parse_options(opts)
        if self.options["debug_logging"]:
            logger.setLevel(logging.DEBUG)

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
                    info='Using "*" matches to any characters (e.g. "* ears" matches to "animal ears", "cat ears", ...)',
                    value="",
                    placeholder="umbrella, official *, * text, * background, ...",
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
                        value=PROCESSING_TIMING["AFTER"],
                    )

                    def on_process_timing_dropdown_changed(timing: str):
                        if timing == PROCESSING_TIMING["BEFORE"]:
                            return "_Prompt upsampling will be applied to **only the first image in batch**, **before** sd-dynamic-promps and the webui's styles feature are applied_"
                        elif timing == PROCESSING_TIMING["AFTER"]:
                            return "_Prompt upsampling will be applied to **all images in batch**, **after** sd-dynamic-promps and the webui's styles feature are applied_"
                        raise Exception(f"Unknown timing: {timing}")

                    process_timing_md = gr.Markdown(
                        on_process_timing_dropdown_changed(
                            process_timing_dropdown.value
                        )
                    )

                    process_timing_dropdown.change(
                        on_process_timing_dropdown_changed,
                        inputs=[process_timing_dropdown],
                        outputs=[process_timing_md],
                    )

                with gr.Group():
                    variety_preset_radio = gr.Radio(
                        label="Variety level",
                        info="Just easy presets of generation config below",
                        choices=list(VARIETY_OPTIONS.values()),
                        value=VARIETY_OPTIONS["NORMAL"],
                    )

                with gr.Accordion(label="Generation config", open=False):
                    do_cfg_check = gr.Checkbox(
                        label="Do CFG",
                        info="Enables classifier-free guidance, this takes double of computation",
                        visible=False,
                    )
                    negative_prompt_textbox = gr.Textbox(
                        label="Negative tags",
                        placeholder="simple background, ...",
                        value="",
                        visible=False,
                    )
                    cfg_scale_slider = gr.Slider(
                        label="CFG scale",
                        minimum=0.1,
                        maximum=3.0,
                        value=1.5,
                        step=0.1,
                        visible=False,
                    )

                    temperature_slider = gr.Slider(
                        label="Temperature",
                        info="← less random | more random →",
                        maximum=4.0,
                        minimum=0.1,
                        step=0.01,
                        value=1.0,
                    )
                    top_p_slider = gr.Slider(
                        label="Top p",
                        info="← less random | more random →",
                        maximum=1.0,
                        minimum=0.0,
                        step=0.01,
                        value=1.0,
                    )
                    top_k_slider = gr.Slider(
                        label="Top k",
                        info="← less random | more random →",
                        maximum=1000,
                        minimum=10,
                        step=1,
                        value=20,
                    )

                    num_beams_slider = gr.Slider(
                        label="Num beams",
                        info="← more random, less computation | less random, more computation →",
                        maximum=20,
                        minimum=1,
                        step=1,
                        value=1,
                    )

                # update generation config when the preset is changed
                def on_variety_preset_radio_change(level: str):
                    if level in VARIETY_OPTIONS.values():
                        return VARIETY_PRESETS[VARIETY_OPTIONS_VK[level]]
                    else:
                        raise Exception(f"Unknown variety level: {level}")

                variety_preset_radio.change(
                    on_variety_preset_radio_change,
                    inputs=[variety_preset_radio],
                    outputs=[
                        temperature_slider,
                        top_p_slider,
                        top_k_slider,
                        num_beams_slider,
                    ],
                )

        return [
            enabled_check,
            tag_length_radio,
            ban_tags_textbox,
            seed_num_input,
            process_timing_dropdown,
            # generation config
            do_cfg_check,
            negative_prompt_textbox,
            cfg_scale_slider,
            temperature_slider,
            top_p_slider,
            top_k_slider,
            num_beams_slider,
        ]

    def process(
        self,
        p: StableDiffusionProcessingTxt2Img | StableDiffusionProcessingImg2Img,
        is_enabled: bool,
        tag_length: str,
        ban_tags: str,
        seed_num: int,
        process_timing: str,
        # generation config
        do_cfg: bool,
        negative_prompt: str,
        cfg_scale: float,
        temperature: float,
        top_p: float,
        top_k: int,
        num_bemas: int,
    ):
        """This method will be called after sd-dynamic-prompts and the styles are applied."""

        if not is_enabled:
            return

        if process_timing != PROCESSING_TIMING["AFTER"]:
            return

        analyzing_results = [self.analyzer.analyze(prompt) for prompt in p.all_prompts]
        logger.debug(f"Analyzed: {analyzing_results}")

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

        upsampling_negative_prompts = []
        if do_cfg and negative_prompt is not None:
            negative_analyzing_result = self.analyzer.analyze(negative_prompt)
            logger.debug(f"Analyzed (negative): {negative_analyzing_result}")

            for analyzing_result in analyzing_results:
                upsampling_negative_prompt = self.generator.compose_prompt(
                    rating=f"{analyzing_result.rating_parent}, {analyzing_result.rating_child}",
                    copyright=_join_texts(
                        analyzing_result.copyright, negative_analyzing_result.copyright
                    ),
                    character=_join_texts(
                        analyzing_result.character, negative_analyzing_result.character
                    ),
                    general=negative_analyzing_result.general,
                    length=TOTAL_TAG_LENGTH_TAGS[tag_length],
                )
                upsampling_negative_prompts.append(upsampling_negative_prompt)

        num_images = p.n_iter * p.batch_size
        upsampling_seeds = utils.get_upmsapling_seeds(
            p,
            num_images,
            custom_seed=seed_num,
        )

        # this list has only 1 item
        upsampled_tags = self._upsample_tags(
            upsampling_prompt,
            seeds=upsampling_seeds,
            temperature=float(temperature),
            top_p=float(top_p),
            top_k=int(top_k),
            num_bemas=int(num_bemas),
            bad_words_ids=bad_words_ids,
            negative_prompts=upsampling_negative_prompts if do_cfg else None,
            cfg_scale=float(cfg_scale),
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
        # generation config
        do_cfg: bool,
        negative_prompt: str,
        cfg_scale: float,
        temperature: float,
        top_p: float,
        top_k: int,
        num_bemas: int,
    ):
        """This method will be called before sd-dynamic-prompts and the styles are applied."""

        if not is_enabled:
            return

        if process_timing != PROCESSING_TIMING["BEFORE"]:
            return

        analyzing_result = self.analyzer.analyze(p.prompt)
        logger.debug(f"Analyzed: {analyzing_result}")

        upsampling_prompt = self.generator.compose_prompt(
            rating=f"{analyzing_result.rating_parent}, {analyzing_result.rating_child}",
            copyright=analyzing_result.copyright,
            character=analyzing_result.character,
            general=analyzing_result.general,
            length=TOTAL_TAG_LENGTH_TAGS[tag_length],
        )
        logger.debug(f"Upsampling prompt: {upsampling_prompt}")
        bad_words_ids = self.generator.get_bad_words_ids(ban_tags)

        upsampling_negative_prompt = None
        if do_cfg and negative_prompt is not None:
            negative_analyzing_result = self.analyzer.analyze(p.prompt)
            logger.debug(f"Analyzed (negative): {analyzing_result}")

            upsampling_negative_prompt = self.generator.compose_prompt(
                rating=f"{analyzing_result.rating_parent}, {analyzing_result.rating_child}",
                copyright=_join_texts(
                    analyzing_result.copyright, negative_analyzing_result.copyright
                ),
                character=_join_texts(
                    analyzing_result.character, negative_analyzing_result.character
                ),
                general=negative_analyzing_result.general,
                length=TOTAL_TAG_LENGTH_TAGS[tag_length],
            )

        upsampling_seeds = utils.get_upmsapling_seeds(
            p,
            num_seeds=1,  # only for the first prompt
            custom_seed=seed_num,
        )

        # this list has only 1 item
        upsampled_tags = self._upsample_tags(
            [upsampling_prompt],
            seeds=upsampling_seeds,
            temperature=float(temperature),
            top_p=float(top_p),
            top_k=int(top_k),
            num_bemas=int(num_bemas),
            bad_words_ids=bad_words_ids,
            negative_prompts=(
                [upsampling_negative_prompt]
                if upsampling_negative_prompt is not None
                else None
            ),
            cfg_scale=float(cfg_scale),
        )
        logger.debug(f"Upsampled tags: {upsampled_tags}")

        # set a new prompt
        p.prompt = _concatnate_texts([p.prompt], upsampled_tags)[0]

    def _upsample_tags(
        self,
        prompts: list[str],
        seeds: list[int],
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = 20,
        num_bemas: int = 1,
        bad_words_ids: list[list[int]] | None = None,
        negative_prompts: list[str] | None = None,
        cfg_scale: float = 1.5,
    ) -> list[str]:
        """Upsamples tags using provided prompts and returns added tags."""

        if len(prompts) == 1 and len(prompts) != len(seeds):
            prompts = prompts * len(seeds)

        upsampled_tags = []
        for i, (prompt, seed) in enumerate(zip(prompts, seeds, strict=True)):
            set_seed(seed)
            upsampled_tags.append(
                self.generator.generate(
                    prompt,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    num_beams=num_bemas,
                    bad_words_ids=bad_words_ids,
                    negative_prompt=(
                        negative_prompts[i] if negative_prompts is not None else None
                    ),
                    cfg_scale=cfg_scale,
                )
            )
        return upsampled_tags
