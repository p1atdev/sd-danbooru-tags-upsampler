import logging
from pathlib import Path
from dataclasses import dataclass

from modules.scripts import basedir

logger = logging.getLogger(__name__)

RATING_TAGS = {
    "GENERAL": "rating:general",
    "SENSITIVE": "rating:sensitive",
    "QUESTIONABLE": "rating:questionable",
    "EXPLICIT": "rating:explicit",
    "SFW": "sfw",
    "NSFW": "nsfw",
}

RATING_TAG_PRIORITY = {
    "rating:general": 0,
    "rating:sensitive": 1,
    "rating:questionable": 2,
    "rating:explicit": 3,
}

RATING_PARENT_TAGS = {
    "SFW": "rating:sfw",
    "NSFW": "rating:nsfw",
}

RATING_PARENT_TAG_PRIORITY = {"sfw": 0, "nsfw": 1}

RATING_DEFAULT_PAIR = RATING_PARENT_TAGS["SFW"], RATING_TAGS["GENERAL"]


def normalize_rating_tags(tags: list[str]) -> tuple[str, str | None]:
    """
    Returns [Parent Rating Tag, Child Rating Tag or None]
    """

    if len(tags) == 0:
        # default
        return RATING_DEFAULT_PAIR

    # only one tag
    if len(tags) == 1:
        tag = tags[0]

        if tag == RATING_TAGS["NSFW"]:
            return RATING_PARENT_TAGS["NSFW"], None
        elif tag == RATING_TAGS["SFW"]:
            return RATING_DEFAULT_PAIR
        elif tag == RATING_TAGS["GENERAL"]:
            return RATING_DEFAULT_PAIR
        elif tag == RATING_TAGS["SENSITIVE"]:
            return RATING_PARENT_TAGS["SFW"], RATING_TAGS["SENSITIVE"]
        elif tag == RATING_TAGS["QUESTIONABLE"]:
            return RATING_PARENT_TAGS["NSFW"], RATING_TAGS["QUESTIONABLE"]
        elif tag == RATING_TAGS["EXPLICIT"]:
            return RATING_PARENT_TAGS["NSFW"], RATING_TAGS["EXPLICIT"]

    # len(tags) >= 2

    # if all of tags are parent tag
    if all([tag in RATING_PARENT_TAGS for tag in tags]):
        logger.warning(
            'Both "sfw" and "nsfw" are specified in positive image prompt! Rating tag fell back to "sfw" for danbooru tag upsampling.'
        )
        return RATING_DEFAULT_PAIR

    # one of the tag is parent tag
    if any([tag in RATING_PARENT_TAGS for tag in tags]):
        parent_tag = RATING_TAGS["SFW"]
        for tag in tags:
            if RATING_PARENT_TAG_PRIORITY[tag] > RATING_PARENT_TAG_PRIORITY[parent_tag]:
                parent_tag = tag
                break
        child_tag = [
            tag
            for tag in tags
            if RATING_TAG_PRIORITY[tag]
            == max([RATING_TAG_PRIORITY[tag] for tag in tags])
        ][0]
        return parent_tag, child_tag

    # both are child tag
    # give priority to the strong
    strongest_tag = [
        tag
        for tag in tags
        if RATING_TAG_PRIORITY[tag] == max([RATING_TAG_PRIORITY[tag] for tag in tags])
    ][0]
    if strongest_tag in [RATING_TAGS["EXPLICIT"], RATING_TAGS["QUESTIONABLE"]]:
        return RATING_PARENT_TAGS["NSFW"], strongest_tag
    else:
        return RATING_PARENT_TAGS["SFW"], strongest_tag


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
    """A class for analyzing provided image prompt for composing umsaple prompt"""

    def __init__(self, extension_dir: str, vocab: list[str], special_vocab: list[str]):
        self.tags_dir = Path(extension_dir) / "tags"

        self.rating_tags = list(RATING_TAGS.values())

        self.copyright_tags = load_tags_in_file(self.tags_dir / "copyright.txt")
        self.character_tags = load_tags_in_file(self.tags_dir / "character.txt")
        self.quality_tags = load_tags_in_file(self.tags_dir / "quality.txt")

        self.vocab = vocab
        self.special_vocab = special_vocab

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
            copyright=", ".join(copyright_tags),
            character=", ".join(character_tags),
            general=", ".join(other_tags),
            quality=", ".join(quality_tags),
            unknown=", ".join(unknown_tags),
        )
