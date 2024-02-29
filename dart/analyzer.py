import logging
from pathlib import Path
from dataclasses import dataclass

from modules.shared import opts

from dart.settings import parse_options
from dart.utils import (
    escape_webui_special_symbols,
    unescape_webui_special_symbols,
)

logger = logging.getLogger(__name__)


DART_RATING_GENERAL = "rating:general"
DART_RATING_SENSITIVE = "rating:sensitive"
DART_RATING_QUESTIONABLE = "rating:questionable"
DART_RATING_EXPLICIT = "rating:explicit"

INPUT_RATING_GENERAL = DART_RATING_GENERAL
INPUT_RATING_SENSITIVE = DART_RATING_SENSITIVE
INPUT_RATING_QUESTIONABLE = DART_RATING_QUESTIONABLE
INPUT_RATING_EXPLICIT = DART_RATING_EXPLICIT

DART_RATING_SFW = "rating:sfw"
DART_RATING_NSFW = "rating:nsfw"

INPUT_RATING_SFW = "sfw"
INPUT_RATING_NSFW = "nsfw"

ALL_INPUT_RATING_TAGS = [
    INPUT_RATING_GENERAL,
    INPUT_RATING_SENSITIVE,
    INPUT_RATING_QUESTIONABLE,
    INPUT_RATING_EXPLICIT,
    INPUT_RATING_SFW,
    INPUT_RATING_NSFW,
]

RATING_TAG_PRIORITY = {
    INPUT_RATING_GENERAL: 0,
    INPUT_RATING_SENSITIVE: 1,
    INPUT_RATING_QUESTIONABLE: 2,
    INPUT_RATING_EXPLICIT: 3,
}

RATING_PARENT_TAG_PRIORITY = {INPUT_RATING_SFW: 0, INPUT_RATING_NSFW: 1}

DART_RATING_DEFAULT_PAIR = DART_RATING_SFW, DART_RATING_GENERAL


def get_rating_tag_pair(tag: str) -> tuple[str, str]:
    if tag == INPUT_RATING_NSFW:  # nsfw
        return DART_RATING_NSFW, DART_RATING_EXPLICIT

    elif tag == INPUT_RATING_SFW:  # sfw
        return DART_RATING_DEFAULT_PAIR

    elif tag == INPUT_RATING_GENERAL:  # rating:general
        return DART_RATING_DEFAULT_PAIR

    elif tag == INPUT_RATING_SENSITIVE:  # rating:general
        return DART_RATING_SFW, DART_RATING_SENSITIVE

    elif tag == INPUT_RATING_QUESTIONABLE:  # rating:questionable
        return DART_RATING_NSFW, DART_RATING_QUESTIONABLE

    elif tag == INPUT_RATING_EXPLICIT:  # rating:explicit
        return DART_RATING_NSFW, DART_RATING_EXPLICIT

    else:
        raise Exception(f"Unkown rating tag: {tag}")


def get_strongest_rating_tag(tags: list[str]) -> str:
    strongest_tag = INPUT_RATING_GENERAL
    for tag in tags:
        if RATING_TAG_PRIORITY[tag] > RATING_TAG_PRIORITY[strongest_tag]:
            strongest_tag = tag
    return strongest_tag


def normalize_rating_tags(tags: list[str]) -> tuple[str, str]:
    """
    Returns [Parent Rating Tag, Child Rating Tag or None]
    """

    if len(tags) == 0:
        # default
        return DART_RATING_DEFAULT_PAIR

    # only one tag
    if len(tags) == 1:
        tag = tags[0]

        return get_rating_tag_pair(tag)

    # len(tags) >= 2

    # if all of tags are parent tag
    if all([tag in RATING_PARENT_TAG_PRIORITY.keys() for tag in tags]):
        logger.warning(
            'Both "sfw" and "nsfw" are specified in positive image prompt! Rating tag fell back to "sfw" for upsampling.'
        )
        return DART_RATING_DEFAULT_PAIR

    # one of the tag is parent tag
    if any([tag in RATING_PARENT_TAG_PRIORITY.keys() for tag in tags]):
        parent_tag = INPUT_RATING_SFW  # sfw or nsfw
        child_tags = []
        for tag in tags:
            if tag in RATING_PARENT_TAG_PRIORITY:
                if (
                    RATING_PARENT_TAG_PRIORITY[tag]
                    > RATING_PARENT_TAG_PRIORITY[parent_tag]
                ):
                    parent_tag = tag
            else:
                child_tags.append(tag)

        # pick strongest tag
        child_tag = get_strongest_rating_tag(child_tags)

        fallback_pair = get_rating_tag_pair(parent_tag)
        if child_tag != fallback_pair[1]:
            # e.g. rating:general, nsfw
            logger.warning(
                f'Specified rating tag "{child_tag}" mismatches to "{parent_tag}". "{fallback_pair[1]}" will be used for upsampling instead.'
            )
            return fallback_pair
        return parent_tag, child_tag

    # remains are child tag
    # give priority to the strong
    strongest_tag = get_strongest_rating_tag(tags)
    return get_rating_tag_pair(strongest_tag)


def load_tags_in_file(path: Path):
    if not path.exists():
        logger.error(f"File not found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as file:
        tags = [tag.strip() for tag in file.readlines() if tag.strip() != ""]

    return tags


@dataclass
class ImagePromptAnalyzingResult:
    """A class of the result of analyzing tags"""

    rating_parent: str
    rating_child: str | None
    copyright: str
    character: str
    general: str
    quality: str
    unknown: str


class DartAnalyzer:
    """A class for analyzing provided prompt and composing prompt for upsampling"""

    def __init__(self, extension_dir: str, vocab: list[str], special_vocab: list[str]):
        self.options = parse_options(opts)
        if self.options["debug_logging"]:
            logger.setLevel(logging.DEBUG)

        self.tags_dir = Path(extension_dir) / "tags"

        self.rating_tags = ALL_INPUT_RATING_TAGS

        self.copyright_tags = load_tags_in_file(self.tags_dir / "copyright.txt")
        self.character_tags = load_tags_in_file(self.tags_dir / "character.txt")
        self.quality_tags = load_tags_in_file(self.tags_dir / "quality.txt")

        self.vocab = vocab
        self.special_vocab = special_vocab

        if self.options["escape_input_brackets"]:
            logger.debug("Allows tags with escaped brackets")
            self.copyright_tags += escape_webui_special_symbols(self.copyright_tags)
            self.character_tags += escape_webui_special_symbols(self.character_tags)
            self.vocab += escape_webui_special_symbols(self.vocab)

    def split_tags(self, image_prompt: str) -> list[str]:
        return [tag.strip() for tag in image_prompt.split(",") if tag.strip() != ""]

    def extract_tags(self, input_tags: list[str], extract_tag_list: list[str]):
        matched: list[str] = []
        not_matched: list[str] = []

        for input_tag in input_tags:
            if input_tag in extract_tag_list:
                matched.append(input_tag)
            else:
                not_matched.append(input_tag)

        return matched, not_matched

    def preprocess_tags(self, tags: list[str]) -> str:
        """Preprocess tags to pass to dart model."""

        # \(\) -> ()
        if self.options["escape_output_brackets"]:
            tags = unescape_webui_special_symbols(tags)

        return ", ".join(tags)

    def analyze(self, image_prompt: str) -> ImagePromptAnalyzingResult:
        input_tags = self.split_tags(image_prompt)

        input_tags = list(set(input_tags))  # unique

        rating_tags, input_tags = self.extract_tags(input_tags, self.rating_tags)
        copyright_tags, input_tags = self.extract_tags(input_tags, self.copyright_tags)
        character_tags, input_tags = self.extract_tags(input_tags, self.character_tags)
        quality_tags, input_tags = self.extract_tags(input_tags, self.quality_tags)

        # escape special tags
        _special_tags, input_tags = self.extract_tags(input_tags, self.special_vocab)

        # general tags and unknown tags
        other_tags, unknown_tags = self.extract_tags(input_tags, self.vocab)

        rating_parent, rating_child = normalize_rating_tags(rating_tags)

        return ImagePromptAnalyzingResult(
            rating_parent=rating_parent,
            rating_child=rating_child,
            copyright=self.preprocess_tags(copyright_tags),
            character=self.preprocess_tags(character_tags),
            general=self.preprocess_tags(other_tags),
            quality=self.preprocess_tags(quality_tags),
            unknown=self.preprocess_tags(unknown_tags),
        )
