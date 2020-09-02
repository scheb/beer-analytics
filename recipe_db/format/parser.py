import abc
import json
import re

from recipe_db.models import Recipe


class ParserResult:
    def __init__(self, recipe: Recipe, malts: list, hops: list, yeasts: list) -> None:
        self.recipe = recipe
        self.malts = malts
        self.hops = hops
        self.yeasts = yeasts


class FormatParser:
    @abc.abstractmethod
    def parse_recipe(self, file_path: str) -> ParserResult:
        raise NotImplementedError


class JsonParser:
    def __init__(self, json_string) -> None:
        self.json_data = json.loads(json_string)

    def get(self, field_name):
        return self.json_data.get(field_name)

    def int_or_none(self, field_name):
        return int_or_none(self.get(field_name))

    def float_or_none(self, field_name):
        return float_or_none(self.get(field_name))

    def string_or_none(self, field_name):
        return string_or_none(self.get(field_name))


def int_or_none(value):
    float_value = float_or_none(value)
    return None if float_value is None else round(float_value)


def float_or_none(value):
    if value is None:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def string_or_none(value):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return None

    try:
        return str(value)
    except ValueError:
        return None


def greater_than_zero_or_none(value):
    if value is None:
        return None

    if value <= 0:
        return None

    return value


def clean_kind(kind: str) -> str:
    kind = kind.replace("®", "")
    kind = re.sub("\\s+", " ", kind)
    kind = kind.strip()
    return kind
