import re

import translitcodec
import codecs

from django.db import transaction

from recipe_db.models import RecipeHop, Hop


TRANSLIT_SHORT = 'translit/short'
TRANSLIT_LONG = 'translit/long'


def normalize_name(value: str, translit: str) -> str:
    value = codecs.encode(value, translit)
    value = re.sub('[\\s-]+', ' ', re.sub('[^\\w\\s-]', '', value))
    value = value.strip().lower()
    return value


def create_hops_mapping() -> dict:
    mapping = {}
    for hop in Hop.objects.all():
        normalized_name_long = normalize_name(hop.name, TRANSLIT_LONG)
        mapping[normalized_name_long] = hop

        normalized_name_short = normalize_name(hop.name, TRANSLIT_SHORT)
        if normalized_name_short != normalized_name_long:
            mapping[normalized_name_short] = hop

        if hop.alt_names is not None:
            alt_names = hop.alt_names.split(",")
            for alt_name in alt_names:
                normalized_name_long = normalize_name(alt_name, TRANSLIT_LONG)
                mapping[normalized_name_long] = hop

                normalized_name_short = normalize_name(alt_name, TRANSLIT_SHORT)
                if normalized_name_short != normalized_name_long:
                    mapping[normalized_name_short] = hop

    return mapping


def clean_name(value: str) -> str:
    value = re.sub("Northern\\s+Brewer\\s+-\\s+", "", value)  # Producer prefix
    value = re.sub('\\(?[0-9]+([.,][0-9]+)?\\s+AA\\)?', '', value)
    value = re.sub('/?\\s*[0-9]+([.,][0-9]+)?\\s+(Grams|Ounces)', '', value)
    value = value.strip().lower()
    return value


@transaction.atomic
def map_hops():
    hops_mapping = create_hops_mapping()
    for hop in RecipeHop.objects.all():
        hop_name = clean_name(hop.kind_raw)

        # Exact match (long translit)
        hop_name_long = normalize_name(hop_name, TRANSLIT_LONG)
        if hop_name_long in hops_mapping:
            hop.kind = hops_mapping[hop_name_long]
            hop.save()
            continue

        # Exact match (short translit)
        hop_name_short = normalize_name(hop_name, TRANSLIT_SHORT)
        if hop_name_short != hop_name_long and hop_name_short in hops_mapping:
            hop.kind = hops_mapping[hop_name_short]
            hop.save()
            continue

        num_candidates = 0
        candidates = []
        for pattern in hops_mapping:
            if pattern in hop_name_long or pattern in hop_name_short:
                match = pattern, hops_mapping[pattern]
                candidates.append(match)
                num_candidates += 1

        if num_candidates == 1:
            (_, hop.kind) = candidates.pop()
            hop.save()
            continue

        if num_candidates > 1:
            candidates = sorted(candidates, key=sort_candidates)
            (_, hop.kind) = candidates.pop()
            hop.save()
            continue

        hop.kind = None
        hop.save()


def sort_candidates(match):
    (pattern, _) = match
    num_words = pattern.count("_") + 1
    length = len(pattern)
    return num_words * 1000 + length
