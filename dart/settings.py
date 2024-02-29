import logging
from typing import Literal, Any

import gradio as gr

from modules import shared
from modules.options import Options

logger = logging.getLogger(__name__)


MODEL_BACKEND_TYPE = {
    "ORIGINAL": "Original",
    "ONNX": "ONNX",
    "ONNX_QUANTIZED": "ONNX (Quantized)",
}

OPTION_NAME = Literal[
    "model_name",
    "tokenizer_name",
    "model_backend_type",
    "model_device",
    "debug_logging",
    "escape_input_brackets",
    "escape_output_brackets",
]

DEFAULT_VALUES: dict[OPTION_NAME, Any] = {
    "model_name": "p1atdev/dart-v1-sft",
    "tokenizer_name": "p1atdev/dart-v1-sft",
    "model_backend_type": MODEL_BACKEND_TYPE["ONNX_QUANTIZED"],
    "model_device": "cpu",
    "escape_input_brackets": True,
    "escape_output_brackets": True,
    "debug_logging": False,
}


def parse_options(opts: Options | None) -> dict[OPTION_NAME, Any]:

    def get_value(key: OPTION_NAME):
        assert opts is not None
        # fallback if the key doest not exist
        return opts.__getattr__(key) if hasattr(opts, key) else DEFAULT_VALUES[key]

    return {
        "model_name": get_value("model_name"),
        "tokenizer_name": get_value("tokenizer_name"),
        "model_backend_type": get_value("model_backend_type"),
        "model_device": get_value("model_device"),
        "escape_input_brackets": get_value("escape_input_brackets"),
        "escape_output_brackets": get_value("escape_output_brackets"),
        "debug_logging": get_value("debug_logging"),
    }


def on_ui_settings():
    section = ("dart_upsampler", "Danbooru Tags Upsampler")
    shared.opts.add_option(
        key="model_name",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["model_name"],
            label="The model to use for upsampling danbooru tags.",
            component=gr.Dropdown,
            component_args={"choices": ["p1atdev/dart-v1-sft"]},
            section=section,
        ),
    )
    shared.opts.add_option(
        key="tokenizer_name",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["tokenizer_name"],
            label="The tokenizer for the upsampling model.",
            component=gr.Dropdown,
            component_args={"choices": ["p1atdev/dart-v1-sft"]},
            section=section,
        ),
    )
    shared.opts.add_option(
        key="model_backend_type",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["model_backend_type"],
            label="The type of model backend.",
            component=gr.Dropdown,
            component_args={"choices": list(MODEL_BACKEND_TYPE.values())},
            section=section,
        ).info(
            "Original = inefficient computation; ONNX = efficient computing but the model size is very large; ONNX (Quantized) = efficient computation, smallest model file size, and fastest"
        ),
    )
    shared.opts.add_option(
        key="model_device",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["model_device"],
            label="The device to run upsampling model on.",
            component=gr.Textbox,
            section=section,
        ),
    )
    shared.opts.add_option(
        key="escape_input_brackets",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["escape_input_brackets"],
            label="Allow escaped brackets in input prompt.",
            component=gr.Checkbox,
            section=section,
        ),
    )
    shared.opts.add_option(
        key="escape_output_brackets",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["escape_output_brackets"],
            label="Escape brackets in upsampled tags.",
            component=gr.Checkbox,
            section=section,
        ),
    )
    shared.opts.add_option(
        key="debug_logging",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["debug_logging"],
            label="Enblae debug logging.",
            component=gr.Checkbox,
            section=section,
        ),
    )
