import logging
from typing import Literal, Any

import gradio as gr

from modules import shared

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
    "default_ban_tags",
    "model_device",
]

DEFAULT_VALUES: dict[OPTION_NAME, Any] = {
    "model_name": "p1atdev/dart-v1-sft",
    "tokenizer_name": "p1atdev/dart-v1-sft",
    "model_backend_type": MODEL_BACKEND_TYPE["ONNX_QUANTIZED"],
    "default_ban_tags": "",
    "model_device": "cpu",
}


def parse_options(opts) -> dict[OPTION_NAME, Any]:
    return {
        "model_name": (
            opts.model_name
            if hasattr(opts, "model_name")
            else DEFAULT_VALUES["model_name"]
        ),
        "tokenizer_name": (
            opts.tokenizer_name
            if hasattr(opts, "tokenizer_name")
            else DEFAULT_VALUES["tokenizer_name"]
        ),
        "model_backend_type": (
            opts.model_backend_type
            if hasattr(opts, "model_backend_type")
            else DEFAULT_VALUES["model_backend_type"]
        ),
        "default_ban_tags": (
            opts.default_ban_tags
            if hasattr(opts, "default_ban_tags")
            else DEFAULT_VALUES["default_ban_tags"]
        ),
        "model_device": (
            opts.default_ban_tags
            if hasattr(opts, "model_device")
            else DEFAULT_VALUES["model_device"]
        ),
    }


def on_ui_settings():
    section = ("dart_upsampler", "Danbooru Tags Upsampler")
    shared.opts.add_option(
        key="model_name",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["model_name"],  # default value
            label="The model to use for upsampling danbooru tags.",
            component=gr.Dropdown,
            component_args={"choices": ["p1atdev/dart-v1-sft"]},
            section=section,
        ),
    )
    shared.opts.add_option(
        key="tokenizer_name",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["tokenizer_name"],  # default value
            label="The tokenizer for the upsampling model.",
            component=gr.Dropdown,
            component_args={"choices": ["p1atdev/dart-v1-sft"]},
            section=section,
        ),
    )
    shared.opts.add_option(
        key="model_backend_type",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["model_backend_type"],  # default value
            label="The type of model backend.",
            component=gr.Dropdown,
            component_args={"choices": list(MODEL_BACKEND_TYPE.values())},
            section=section,
        ),
    )
    shared.opts.add_option(
        key="default_ban_tags",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["default_ban_tags"],  # default value
            label="The list of tags to prevent from appearing in tag upsamping.",
            component=gr.Textbox,
            section=section,
        ),
    )
    shared.opts.add_option(
        key="model_device",
        info=shared.OptionInfo(
            default=DEFAULT_VALUES["model_device"],  # default value
            label="The device to run upsampling model on.",
            component=gr.Textbox,
            section=section,
        ),
    )
