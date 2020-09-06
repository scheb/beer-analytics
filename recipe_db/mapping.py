import codecs
import re
from typing import Optional, Iterable

import translitcodec

from django.db import transaction

from recipe_db.models import RecipeHop, Hop


TRANSLIT_SHORT = 'translit/short'
TRANSLIT_LONG = 'translit/long'


def clean_hop_name(value: str) -> str:
    value = value.lower()
    value = re.sub("northern\\s+brewer\\s+-\\s+", "", value)  # Producer prefix
    value = re.sub("^hall?ertau(er)?$", "hallertauer mittelfrüh", value)  # Just "Hallertau(er)"
    value = re.sub('\\(?[0-9]+([.,][0-9]+)?\\s+aa\\)?', '', value)
    value = re.sub('/?\\s*[0-9]+([.,][0-9]+)?\\s+(grams|ounces)', '', value)
    value = value.strip()
    return value


def normalize_name(value: str, translit: str) -> str:
    value = codecs.encode(value, translit)
    value = re.sub('[\\s-]+', ' ', re.sub('[^\\w\\s-]', '', value))
    value = value.strip().lower()
    return value


class Candidate:
    def __init__(self, pattern: str, matching_object: object) -> None:
        self.pattern = pattern
        self.matching_object = matching_object
        super().__init__()

    def get_weight(self) -> int:
        num_words = self.pattern.count("_") + 1
        length = len(self.pattern)
        return num_words * 1000 + length


def sort_candidates(match: Candidate) -> int:
    return match.get_weight()


class ObjectMap:
    def __init__(self) -> None:
        self.mapping = {}

    def add(self, name: str, mapped_object: object) -> None:
        for name_variant in self.get_name_variants(name):
            self.mapping[name_variant] = mapped_object

    def all(self) -> dict:
        return self.mapping

    def match(self, name: str) -> Optional[object]:
        for name_variant in self.get_name_variants(name):
            if name_variant in self.mapping:
                return self.mapping[name_variant]
        return None

    def fuzzy_match(self, name: str) -> Iterable[Candidate]:
        for name_variant in self.get_name_variants(name):
            for pattern in self.mapping:
                if pattern in name_variant:
                    yield Candidate(pattern, self.mapping[pattern])

    def get_name_variants(self, name: str) -> iter:
        names = set()

        # Long translit name
        normalized_name_long = normalize_name(name, TRANSLIT_LONG)
        names.add(normalized_name_long)

        # Short translit name
        normalized_name_short = normalize_name(name, TRANSLIT_SHORT)
        names.add(normalized_name_short)

        # Append numeric parts to the previous/next word
        if re.search('\\s[0-9]+\\b', normalized_name_long):
            names.add(re.sub('\\s+([0-9]+)\\b', '\\1', normalized_name_long))
            names.add(re.sub('\\s+([0-9]+)\\b', '\\1', normalized_name_short))
        if re.search('\\b[0-9]+\\s', normalized_name_long):
            names.add(re.sub('\\b([0-9]+)\\s+', '\\1', normalized_name_long))
            names.add(re.sub('\\b([0-9]+)\\s+', '\\1', normalized_name_short))

        yield from names


class HopsMapper:
    def __init__(self) -> None:
        self.mapping = self.create_hops_mapping()

    def create_hops_mapping(self) -> ObjectMap:
        mapping = ObjectMap()
        for hop in Hop.objects.all():
            mapping.add(hop.name, hop)

            if hop.alt_names is not None:
                alt_names = hop.alt_names.split(",")
                for alt_name in alt_names:
                    mapping.add(alt_name, hop)

        return mapping

    def map_unmapped(self):
        hops = RecipeHop.objects.filter(kind_id=None)
        self.map_hops(hops)

    def map_all(self):
        hops = RecipeHop.objects.all()
        self.map_hops(hops)

    @transaction.atomic
    def map_hops(self, recipe_hops: iter) -> None:
        for recipe_hop in recipe_hops:
            hop_name = self.clean_name(recipe_hop.kind_raw)

            # Exact match
            if hop := self.mapping.match(hop_name):
                recipe_hop.kind = hop
                recipe_hop.save()
                continue

            # Substring match
            candidates = list(self.mapping.fuzzy_match(hop_name))

            if len(candidates) > 0:
                candidates = sorted(candidates, key=sort_candidates)
                recipe_hop.kind = candidates.pop().matching_object
                recipe_hop.save()
                continue

            # Otherwise no match
            recipe_hop.kind = None
            recipe_hop.save()

    def clean_name(self, name: str):
        return clean_hop_name(name)
