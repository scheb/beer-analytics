import abc
import codecs
import re
from typing import Optional, Iterable

# noinspection PyUnresolvedReferences
import translitcodec

from django.db import transaction

from recipe_db.models import RecipeHop, Hop, Fermentable, RecipeFermentable, Style, Recipe

TRANSLIT_SHORT = 'translit/short'
TRANSLIT_LONG = 'translit/long'


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


class MappingException(Exception):
    pass


class NameObjectMap:
    def __init__(self, name_variants_function: callable) -> None:
        self.mapping = {}
        self.get_name_variants = name_variants_function

    def add(self, name: str, mapped_object: object) -> None:
        for name_variant in self.get_name_variants(name):
            if name_variant in self.mapping:
                if self.mapping[name_variant] != mapped_object:
                    raise MappingException("Cannot map \"{}\" to {}, as it's already mapped to {}".format(name_variant, mapped_object, self.mapping[name_variant]))
            else:
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


class Mapper(object):
    def __init__(self) -> None:
        self.mapping = NameObjectMap(self.get_name_variants)
        self.mapping_cache = {}

    def create_mapping(self, items: Iterable) -> None:
        for item in items:
            # Add names
            self.mapping.add(item.name, item)

            # Add alternative names
            if item.alt_names is not None:
                self.add_alt_names(item.alt_names, item)
            if item.alt_names_extra is not None:
                self.add_alt_names(item.alt_names_extra, item)

    def add_alt_names(self, alt_names: str, item: object):
        alt_names = alt_names.split(",")
        for alt_name in alt_names:
            alt_name = alt_name.strip()
            if alt_name != '':
                self.mapping.add(alt_name, item)

    @transaction.atomic
    def map_list(self, item_list: iter) -> None:
        for item in item_list:
            match = self.map_item(item)
            if match is not None:
                self.save_match(item, match)

    def map_item(self, item: object) -> Optional[object]:
        item_name = self.get_clean_name(item)
        if item_name not in self.mapping_cache:
            self.mapping_cache[item_name] = self.map_item_name(item_name)
        return self.mapping_cache[item_name]

    def map_item_name(self, item_name: str) -> Optional[object]:
        # Exact match
        if match := self.match_extact(item_name):
            return match

        # Substring match
        if match := self.match_substring(item_name):
            return match

        return None

    def match_extact(self, name: str) -> Optional[object]:
        if match := self.mapping.match(name):
            return match
        return None

    def match_substring(self, name: str) -> Optional[object]:
        candidates = list(self.mapping.fuzzy_match(name))

        if len(candidates) > 0:
            candidates = sorted(candidates, key=sort_candidates)
            return candidates.pop().matching_object

    @abc.abstractmethod
    def get_clean_name(self, item: object) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def save_match(self, item: object, match: object) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_name_variants(self, name: str) -> iter:
        raise NotImplementedError


class HopsMapper(Mapper):
    def __init__(self) -> None:
        super().__init__()
        self.create_mapping(Hop.objects.all())

    def map_unmapped(self) -> None:
        hops = RecipeHop.objects.filter(kind_id=None)
        self.map_list(hops)

    def map_all(self) -> None:
        hops = RecipeHop.objects.all()
        self.map_list(hops)

    def get_clean_name(self, item: RecipeHop) -> str:
        value = item.kind_raw.lower()
        value = re.sub("northern\\s+brewer\\s+-\\s+", "", value)  # Producer prefix
        value = re.sub("^hall?ertau(er)?$", "hallertauer mittelfrüh", value)  # Just "Hallertau(er)"
        value = re.sub('\\(?[0-9]+([.,][0-9]+)?\\s+aa\\)?', '', value)
        value = re.sub('/?\\s*[0-9]+([.,][0-9]+)?\\s+(grams|ounces)', '', value)
        value = value.strip()
        return value

    def save_match(self, item: RecipeHop, match: Hop):
        item.kind = match
        item.save()

    def get_name_variants(self, name: str) -> iter:
        for name in self.get_number_variants(get_translit_names(name)):
            yield name

    def get_number_variants(self, names) -> iter:
        for name in names:
            yield name

            # Append numeric parts to the previous/next word
            if re.search('\\s[0-9]+\\b', name):
                yield re.sub('\\s+([0-9]+)\\b', '\\1', name)


class FermentablesMapper(Mapper):
    def __init__(self) -> None:
        super().__init__()
        self.create_mapping(Fermentable.objects.all())

    def map_unmapped(self) -> None:
        hops = RecipeFermentable.objects.filter(kind_id=None)
        self.map_list(hops)

    def map_all(self) -> None:
        hops = RecipeFermentable.objects.all()
        self.map_list(hops)

    def get_clean_name(self, item: RecipeHop) -> str:
        value = item.kind_raw.lower()
        value = self.normalize(value)

        # Remove "type" / "typ"
        value = re.sub("\\s+type?\\s+", " ", value)

        value = value.strip()
        return value

    def map_item_name(self, item_name: str) -> Optional[object]:
        # Exact match
        if match := self.match_extact(item_name):
            return match

        # Match the exact string with "malt" suffixed
        if not item_name.endswith(" malt"):
            if match := self.match_extact(item_name+" malt"):
                return match

        # Substring match
        if match := self.match_substring(item_name):
            return match

        return None

    def normalize(self, value: str) -> str:
        value = value.lower()

        # Ensure "malt" is always used and its own word
        value = re.sub("\\bmalz\\b", "malt", value)
        value = re.sub("(\w)malt\\b", "\\1 malt", value)
        value = re.sub("(\w)malz\\b", "\\1 malt", value)

        # Normalized "münchner"
        value = re.sub("\\bmünchener\\b", "münchner", value)

        # Normalize "pilsner"
        value = re.sub("\\bpilsener\\b", "pilsner", value)
        value = re.sub("\\bpilsen\\b", "pilsner", value)

        return value

    def save_match(self, item: RecipeFermentable, match: Fermentable):
        item.kind = match
        item.save()

    def get_name_variants(self, name: str) -> iter:
        name = self.normalize(name)
        # Cara variants must be executed after malt variants
        for name in self.get_number_variants(self.get_cara_variants(self.get_malt_variants(get_translit_names(name)))):
            yield name

    def get_malt_variants(self, names: iter) -> iter:
        for name in names:
            yield name

            # When "malt" is in the middle of the name, add a variant without "malt" included
            if " malt " in name:
                yield name.replace(" malt ", " ")

    def get_cara_variants(self, names: iter) -> iter:
        for name in names:
            yield name

            # "cara" appended to next word
            if re.search('\\bcara\\s', name):
                yield re.sub('\\bcara\\s+', 'cara', name)  # Append with succeeding word

            # "cara" variations
            if re.search('\\bcara\\b', name):
                yield re.sub('\\bcara\\b', 'cara malt', name)
                yield re.sub('\\bcara\\b', 'caramel', name)
                yield re.sub('\\bcara\\b', 'caramel malt', name).replace("malt malt", "malt")
                yield re.sub('\\bcara\\b', 'crystal', name)
                yield re.sub('\\bcara\\b', 'crystal malt', name).replace("malt malt", "malt")
                yield re.sub('\\bcara\\b', 'karamell', name)
                yield re.sub('\\bcara\\b', 'karamell malt', name).replace("malt malt", "malt")
                yield re.sub('\\bcara\\b', 'caracrystal', name)
                yield re.sub('\\bcara\\b', 'cara crystal', name)
                yield re.sub('\\bcara\\b', 'crystal cara', name)

    def get_number_variants(self, names) -> iter:
        for name in names:
            yield name

            # Replace roman numerals with arabic numbers
            if re.search('\\si+\\b', name):
                number_name = re.sub('\\siii\\b', ' 3', name)
                number_name = re.sub('\\sii\\b', ' 2', number_name)
                number_name = re.sub('\\si\\b', ' 1', number_name)
                yield number_name


class StylesMapper(Mapper):
    def __init__(self) -> None:
        super().__init__()
        # Exclude top-level style categories in the mapping
        self.create_mapping(Style.objects.filter().exclude(parent_style=None))

    def map_unmapped(self) -> None:
        recipes = Recipe.objects.filter(style_id=None)
        self.map_list(recipes)

    def map_all(self) -> None:
        recipes = Recipe.objects.all()
        self.map_list(recipes)

    def get_clean_name(self, item: Recipe) -> str:
        value = item.style_raw
        if value is None:
            return ''

        value = value.lower()
        value = self.normalize(value)
        value = value.strip()
        return value

    def normalize(self, value: str) -> str:
        value = value.lower()

        # Normalized "münchner"
        value = re.sub("\\bmünchener\\b", "münchner", value)

        # Normalize "pilsner"
        value = re.sub("\\bpilsener\\b", "pilsner", value)
        value = re.sub("\\bpilsen\\b", "pilsner", value)

        return value

    def save_match(self, item: Recipe, match: Style):
        item.style = match
        item.save()

    def get_name_variants(self, name: str) -> iter:
        name = self.normalize(name)
        for name in self.expand_ipa(get_translit_names(name)):
            yield name

    def expand_ipa(self, names) -> iter:
        for name in names:
            yield name
            if re.search('\\bipa\\b', name):
                yield re.sub('\\bipa\\b', 'india pale ale', name)