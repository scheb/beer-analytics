import abc
import codecs
import itertools
import re
from abc import ABC
from typing import Optional, Iterable

# noinspection PyUnresolvedReferences
import translitcodec
from django.db import transaction

from recipe_db.models import RecipeHop, Hop, Fermentable, RecipeFermentable, Style, Recipe, RecipeYeast, Yeast

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


def get_product_id_variants(name: str) -> iter:
    name = re.sub("\\W+", " ", name)  # Split non-word chars
    name = re.sub("([A-Za-z])([0-9])", "\\1 \\2", name)  # Split number + letter
    name = re.sub("([0-9])([A-Za-z])", "\\1 \\2", name)  # Split letter + number
    name = re.sub("\\s+", " ", name).strip()  # Make sure we have single spaces only
    name_parts = name.split(" ")

    parts = []
    first = True
    for name_part in name_parts:
        if first:
            first = False
        else:
            parts.append(["", " "])
        parts.append([name_part])

    for tuple in itertools.product(*parts):
        yield "".join(tuple)


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
        self.ignore_ambiguous = False
        self.mapping = {}
        self.get_name_variants = name_variants_function

    def add(self, name: str, mapped_object) -> None:
        for name_variant in self.get_name_variants(name):
            if name_variant in self.mapping:
                if self.mapping[name_variant] != mapped_object:
                    if self.ignore_ambiguous:
                        self.mapping[name_variant] = None
                    else:
                        raise MappingException(
                            'Cannot map "{}" to "{}", as it\'s already mapped to "{}"'.format(
                                name_variant, mapped_object, self.mapping[name_variant]
                            )
                        )
            else:
                self.mapping[name_variant] = mapped_object

    def all(self) -> dict:
        return self.mapping

    def match(self, name: str) -> Optional:
        for name_variant in self.get_name_variants(name):
            if name_variant in self.mapping:
                return self.mapping[name_variant]
        return None

    def fuzzy_match(self, name: str) -> Iterable[Candidate]:
        for name_variant in self.get_name_variants(name):
            for pattern in self.mapping:
                if pattern in name_variant:
                    yield Candidate(pattern, self.mapping[pattern])


class Mapper:
    @abc.abstractmethod
    def map_item(self, item: object) -> Optional[object]:
        raise NotImplementedError


class GenericMapper(Mapper):
    def __init__(self) -> None:
        self.mapping = NameObjectMap(self.get_name_variants)
        self.mapping_cache = {}

    def create_mapping(self, items: Iterable) -> None:
        for item in items:
            # Add names
            self.mapping.add(item.name, item)

            # Add alternative names
            if hasattr(item, "alt_names") and item.alt_names is not None:
                self.add_alt_names(item.alt_names, item)
            if hasattr(item, "alt_names_extra") and item.alt_names_extra is not None:
                self.add_alt_names(item.alt_names_extra, item)

    def add_alt_names(self, alt_names: str, item: object):
        alt_names = alt_names.split(",")
        for alt_name in alt_names:
            alt_name = alt_name.strip()
            if alt_name != "":
                self.mapping.add(alt_name, item)

    def map_item(self, item: object) -> Optional[object]:
        item_name = self.get_clean_name(item)
        if item_name not in self.mapping_cache:
            self.mapping_cache[item_name] = self.map_item_name(item_name)
        return self.mapping_cache[item_name]

    def map_item_name(self, item_name: str) -> Optional[object]:
        # Exact match
        if match := self.match_exact(item_name):
            return match

        # Substring match
        if match := self.match_substring(item_name):
            return match

        return None

    def match_exact(self, name: str) -> Optional[object]:
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
    def get_name_variants(self, name: str) -> iter:
        raise NotImplementedError


class HopMapper(GenericMapper):
    def __init__(self) -> None:
        super().__init__()
        self.create_mapping(Hop.objects.all())

    def get_clean_name(self, item: RecipeHop) -> str:
        value = item.kind_raw or ""
        value = value.lower()
        value = re.sub("&#039;", "'", value)  # Uptick
        value = re.sub("northern\\s+brewer\\s+-\\s+", "", value)  # Producer prefix
        value = re.sub("^hall?ertau(er)?$", "hallertauer mittelfrüh", value)  # Just "Hallertau(er)"
        value = re.sub("\\(?[0-9]+([.,][0-9]+)?\\s+aa\\)?", "", value)
        value = re.sub("/?\\s*[0-9]+([.,][0-9]+)?\\s+(grams|ounces)", "", value)
        value = value.strip()
        return value

    def get_name_variants(self, name: str) -> iter:
        for name in self.get_number_variants(get_translit_names(name)):
            yield name

    def get_number_variants(self, names) -> iter:
        for name in names:
            yield name

            # Append numeric parts to the previous/next word
            if re.search("\\s[0-9]+\\b", name):
                yield re.sub("\\s+([0-9]+)\\b", "\\1", name)


class FermentableMapper(GenericMapper):
    def __init__(self) -> None:
        super().__init__()
        self.create_mapping(Fermentable.objects.all())

    def get_clean_name(self, item: RecipeHop) -> str:
        value = item.kind_raw or ""
        value = value.lower()
        value = self.normalize(value)

        # Remove "type" / "typ"
        value = re.sub("\\s+type?\\s+", " ", value)

        value = value.strip()
        return value

    def map_item_name(self, item_name: str) -> Optional[object]:
        # Exact match
        if match := self.match_exact(item_name):
            return match

        # Match the exact string with "malt" suffixed
        if not item_name.endswith(" malt"):
            if match := self.match_exact(item_name + " malt"):
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

        # Normalize "caramel"
        value = re.sub("\\bcaramell\\b", "caramel", value)
        value = re.sub("\\bcaramelo\\b", "caramel", value)

        return value

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
            if re.search("\\bcara\\s", name):
                yield re.sub("\\bcara\\s+", "cara", name)  # Append with succeeding word

            # "cara" variations
            if re.search("\\bcara\\b", name):
                yield re.sub("\\bcara\\b", "cara malt", name)
                yield re.sub("\\bcara\\b", "caramel", name)
                yield re.sub("\\bcara\\b", "caramel malt", name).replace("malt malt", "malt")
                yield re.sub("\\bcara\\b", "crystal", name)
                yield re.sub("\\bcara\\b", "crystal malt", name).replace("malt malt", "malt")
                yield re.sub("\\bcara\\b", "karamell", name)
                yield re.sub("\\bcara\\b", "karamell malt", name).replace("malt malt", "malt")
                yield re.sub("\\bcara\\b", "caracrystal", name)
                yield re.sub("\\bcara\\b", "cara crystal", name)
                yield re.sub("\\bcara\\b", "crystal cara", name)

    def get_number_variants(self, names) -> iter:
        for name in names:
            yield name

            # Replace roman numerals with arabic numbers
            if re.search("\\si+\\b", name):
                number_name = re.sub("\\siii\\b", " 3", name)
                number_name = re.sub("\\sii\\b", " 2", number_name)
                number_name = re.sub("\\si\\b", " 1", number_name)
                yield number_name


# Map yeasts to their brand
class YeastBrandMapper(GenericMapper):
    def __init__(self) -> None:
        super().__init__()
        self.create_mapping(Yeast.objects.filter())

    def create_mapping(self, yeasts: Iterable[Yeast]) -> None:
        for yeast in yeasts:
            # Add lab name
            if yeast.lab is not None:
                self.mapping.add(yeast.lab, yeast.lab)
                if yeast.alt_lab is not None:
                    self.add_alt_names(yeast.alt_lab, yeast.lab)

            # Add brand name
            if yeast.brand is not None:
                self.mapping.add(yeast.brand, yeast.brand)
                if yeast.alt_brand is not None:
                    self.add_alt_names(yeast.alt_brand, yeast.brand)

    def get_clean_name(self, item: RecipeYeast) -> str:
        value = item.kind_raw or ""

        # Make sure there's meaningful lab name
        if item.lab is not None and len(item.lab) > 2 and item.lab not in value:
            value = "%s %s" % (item.lab, value)

        return self.normalize(value)

    def get_name_variants(self, name: str) -> iter:
        name = self.normalize(name)
        for name in get_translit_names(name):
            yield name

    def normalize(self, value: str) -> str:
        return value.lower().strip()


# Map yeasts within a brand by product id
class YeastProductIdMapper(GenericMapper):
    def __init__(self, yeasts: iter) -> None:
        super().__init__()
        self.create_mapping(yeasts)

    def create_mapping(self, yeasts: Iterable[Yeast]) -> None:
        for yeast in yeasts:
            # Product id
            self.mapping.add(yeast.product_id, yeast)

            # Add alternative product id
            if yeast.alt_product_id is not None:
                self.add_alt_names(yeast.alt_product_id, yeast)

    def get_clean_name(self, item: RecipeYeast) -> str:
        value = item.product_id or item.kind_raw or ""
        return self.normalize(value)

    def get_name_variants(self, name: str) -> iter:
        name = self.normalize(name)
        if re.fullmatch("[\\w-]{2,10}", name):
            yield from get_product_id_variants(name)
        else:
            yield name

    def normalize(self, value: str) -> str:
        return normalize_name(value, TRANSLIT_SHORT)


class YeastProductNameMapper(GenericMapper):
    def __init__(self, yeasts: iter) -> None:
        super().__init__()
        self.mapping.ignore_ambiguous = True
        self.create_mapping(yeasts)

    def get_clean_name(self, item: RecipeHop) -> str:
        value = item.kind_raw or ""
        value = value.lower()
        value = value.strip()
        return value

    def get_name_variants(self, name: str) -> iter:
        for name in self.get_yeast_variants(get_translit_names(name)):
            yield name

    def get_yeast_variants(self, names: iter):
        for name in names:
            yield name
            if " yeast" in name:
                yield name.replace(" yeast", "")


# Map yeast based on brand and product id
class YeastBrandProductIdMapper(Mapper):
    def __init__(self) -> None:
        self.brand_mapper = YeastBrandMapper()
        self.brand_id_mappers = {}

        brand_yeasts = {}
        yeasts = Yeast.objects.all()
        for yeast in yeasts:
            if yeast.product_id is None:
                continue  # No product id available, skip

            # Lab name
            if yeast.lab not in brand_yeasts:
                brand_yeasts[yeast.lab] = []
            brand_yeasts[yeast.lab].append(yeast)

            # Brand name
            if yeast.brand is not None:
                if yeast.brand not in brand_yeasts:
                    brand_yeasts[yeast.brand] = []
                brand_yeasts[yeast.brand].append(yeast)

        for brand in brand_yeasts:
            self.brand_id_mappers[brand] = YeastProductIdMapper(brand_yeasts[brand])

    def map_item(self, item: RecipeYeast) -> Optional[object]:
        brand = self.brand_mapper.map_item(item)
        if brand is None:
            return None

        if brand in self.brand_id_mappers:
            yeast = self.brand_id_mappers[brand].map_item(item)
            if yeast is not None:
                return yeast

        return None


# Map yeast based on brand and product id
class YeastBrandProductNameMapper(Mapper):
    def __init__(self) -> None:
        self.brand_mapper = YeastBrandMapper()
        self.brand_name_mappers = {}

        brand_yeasts = {}
        yeasts = Yeast.objects.all()
        for yeast in yeasts:
            # Lab name
            if yeast.lab not in brand_yeasts:
                brand_yeasts[yeast.lab] = []
            brand_yeasts[yeast.lab].append(yeast)

            # Brand name
            if yeast.brand is not None:
                if yeast.brand not in brand_yeasts:
                    brand_yeasts[yeast.brand] = []
                brand_yeasts[yeast.brand].append(yeast)

        for brand in brand_yeasts:
            self.brand_name_mappers[brand] = YeastProductNameMapper(brand_yeasts[brand])

    def map_item(self, item: RecipeYeast) -> Optional[object]:
        brand = self.brand_mapper.map_item(item)
        if brand is None:
            return None

        if brand in self.brand_name_mappers:
            yeast = self.brand_name_mappers[brand].map_item(item)
            if yeast is not None:
                return yeast

        return None


class GenericStyleMapper(GenericMapper, ABC):
    def __init__(self, styles: iter) -> None:
        super().__init__()
        self.create_mapping(styles)

    def clean_name(self, value: str) -> str:
        if value is None:
            return ""

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

    def get_name_variants(self, name: str) -> iter:
        name = self.normalize(name)
        for name in self.lager_variants(self.expand_ipa(get_translit_names(name))):
            yield name

    def expand_ipa(self, names) -> iter:
        for name in names:
            yield name
            if re.search("\\bipa\\b", name):
                yield re.sub("\\bipa\\b", "india pale ale", name)

    def lager_variants(self, names) -> iter:
        for name in names:
            yield name
            if re.search("\\blager\\b", name):
                yield re.sub("\\blager\\b", "pilsner", name)


class AssignedStyleMapper(GenericStyleMapper):
    def __init__(self) -> None:
        # Exclude top-level style categories in the mapping
        super().__init__(Style.objects.filter().exclude(parent_style=None))

    def get_clean_name(self, item: Recipe) -> str:
        return self.clean_name(item.style_raw or "")


class StyleMapper(Mapper):
    def __init__(self) -> None:
        self.assigned_style_mapper = AssignedStyleMapper()
        self.sub_style_mappers = {}

        styles = Style.objects.filter().exclude(parent_style=None)
        for style in styles:
            if style.has_sub_styles:
                self.sub_style_mappers[style.id] = RecipeNameSubStyleMapper(style.sub_styles)

    def map_item(self, item: Recipe) -> Optional[object]:
        main_style = self.assigned_style_mapper.map_item(item)
        if main_style is None:
            return None

        assert isinstance(main_style, Style)
        main_style_id = main_style.id
        if main_style_id not in self.sub_style_mappers:
            return main_style

        sub_style = self.sub_style_mappers[main_style_id].map_item(item)
        if sub_style is not None:
            return sub_style

        return main_style


class RecipeNameStyleExactMatchMapper(GenericStyleMapper):
    def __init__(self) -> None:
        # Exclude top-level style categories in the mapping
        super().__init__(Style.objects.filter().exclude(parent_style=None))

    def map_item_name(self, item_name: str) -> Optional[object]:
        # Exact match only!
        if match := self.match_exact(item_name):
            return match
        return None

    def get_clean_name(self, item: Recipe) -> str:
        return self.clean_name(item.name or "")


class RecipeNameStyleMapper(GenericStyleMapper):
    def __init__(self) -> None:
        # Exclude top-level style categories in the mapping
        super().__init__(Style.objects.filter().exclude(parent_style=None))

    def get_clean_name(self, item: Recipe) -> str:
        return self.clean_name(item.name or "")


class RecipeNameSubStyleMapper(GenericStyleMapper):
    def __init__(self, sub_styles: iter) -> None:
        super().__init__(sub_styles)

    def get_clean_name(self, item: Recipe) -> str:
        return self.clean_name(item.name or "")


class TransactionalProcessor:
    def __init__(self, mappers: list) -> None:
        self.mappers = mappers

    @transaction.atomic
    def map_list(self, item_list: iter) -> None:
        for item in item_list:
            for mapper in self.mappers:
                match = mapper.map_item(item)
                if match is not None:
                    self.save_match(item, match)
                    break

    @abc.abstractmethod
    def save_match(self, item: object, match: object) -> str:
        raise NotImplementedError


class HopsProcessor(TransactionalProcessor):
    def map_unmapped(self) -> None:
        hops = RecipeHop.objects.filter(kind_id=None)
        self.map_list(hops)

    def map_all(self) -> None:
        hops = RecipeHop.objects.all()
        self.map_list(hops)

    def save_match(self, item: RecipeHop, match: Hop):
        item.kind = match
        item.save()


class FermentablesProcessor(TransactionalProcessor):
    def map_unmapped(self) -> None:
        hops = RecipeFermentable.objects.filter(kind_id=None)
        self.map_list(hops)

    def map_all(self) -> None:
        hops = RecipeFermentable.objects.all()
        self.map_list(hops)

    def save_match(self, item: RecipeFermentable, match: Fermentable):
        item.kind = match
        item.save()


class StylesProcessor(TransactionalProcessor):
    def map_unmapped(self) -> None:
        recipes = Recipe.objects.filter(style_id=None)
        self.map_list(recipes)

    def map_all(self) -> None:
        recipes = Recipe.objects.all()
        self.map_list(recipes)

    def save_match(self, item: Recipe, style: Style):
        if not self.is_within_limits("abv", item, style):
            style = None
        elif not self.is_within_limits("ibu", item, style):
            style = None
        elif not self.is_within_limits("srm", item, style):
            style = None

        item.style = style
        item.save()

    def is_within_limits(self, property: str, recipe: Recipe, style: Style):
        min = getattr(style, property + "_min")
        max = getattr(style, property + "_max")
        value = getattr(recipe, property)

        if property == "srm" and max is not None and max >= 40:
            max = None

        if value is None:
            return True

        if min is not None and value < (min * 0.9):
            return False

        if max is not None and value > (max * 1.1):
            return False

        return True


class YeastsProcessor(TransactionalProcessor):
    def map_unmapped(self) -> None:
        yeasts = RecipeYeast.objects.filter(kind_id=None)
        self.map_list(yeasts)

    def map_all(self) -> None:
        yeasts = RecipeYeast.objects.all()
        self.map_list(yeasts)

    def save_match(self, item: RecipeYeast, match: Yeast):
        item.kind = match
        item.save()
