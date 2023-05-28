from __future__ import annotations

import abc
import json
import re
from typing import Optional

from recipe_db.models import Recipe


class MalformedDataError(Exception):
    pass


class ParserResult:
    def __init__(self) -> None:
        self.recipe = Recipe()
        self.fermentables = []
        self.hops = []
        self.yeasts = []


class FormatParser:
    @abc.abstractmethod
    def parse(self, result: ParserResult, file_path: str) -> None:
        raise NotImplementedError


class JsonParser:
    def __init__(self, json_data: dict) -> None:
        self.json_data = json_data

    @classmethod
    def from_string(cls, json_string: str) -> JsonParser:
        return JsonParser(json.loads(json_string))

    def has(self, field_name: str) -> bool:
        return field_name in self.json_data

    def get(self, field_name: str):
        return self.json_data.get(field_name)

    def int_or_none(self, field_name: str) -> Optional[int]:
        return int_or_none(self.get(field_name))

    def float_or_none(self, field_name: str) -> Optional[float]:
        return float_or_none(self.get(field_name))

    def string_or_none(self, field_name: str) -> Optional[str]:
        return string_or_none(self.get(field_name))

    def get_structure(self, field_name: str) -> JsonParser:
        data = self.json_data.get(field_name)
        if isinstance(data, dict):
            return JsonParser(self.json_data.get(field_name))
        return JsonParser({})

    def get_dict_iterator(self, field_name):
        dict_field = self.json_data.get(field_name)
        keys = dict_field.keys()
        for key in keys:
            yield JsonParser(dict_field[key])

    def get_list(self, field_name) -> iter:
        data = self.json_data.get(field_name)
        if isinstance(data, list):
            for list_item in data:
                yield JsonParser(list_item)


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
        if value == "":
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


def clean_kind(kind) -> Optional[str]:
    if kind is None:
        return None

    kind = str(kind)
    kind = kind.replace("®", "")
    kind = re.sub("\\s+", " ", kind)
    kind = kind.strip()

    return kind


def to_lower(string):
    if isinstance(string, str):
        return string.lower()
    return None
