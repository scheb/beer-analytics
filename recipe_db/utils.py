import codecs
import re

# noinspection PyUnresolvedReferences
import translitcodec


TRANSLIT_SHORT = "translit/short"
TRANSLIT_LONG = "translit/long"


def get_translit_names(name: str) -> iter:
    # Long translit name
    normalized_name_long = normalize_name(name, TRANSLIT_LONG)
    yield normalized_name_long

    # Short translit name
    normalized_name_short = normalize_name(name, TRANSLIT_SHORT)
    if normalized_name_short != normalized_name_long:
        yield normalized_name_short


def normalize_name(value: str, translit: str) -> str:
    value = codecs.encode(value, translit)
    value = re.sub("[\\s-]+", " ", re.sub("[^\\w\\s-]", "", value))
    value = value.strip().lower()
    return value
