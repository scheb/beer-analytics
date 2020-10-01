from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, List, Iterable

from lxml import etree
from lxml.etree import Element

from recipe_db.format.parser import FormatParser, ParserResult, float_or_none, int_or_none, clean_kind, \
    MalformedDataError, to_lower, string_or_none
from recipe_db.formulas import fluid_ounces_to_liters, ounces_to_gramms, fahrenheit_to_celsius
from recipe_db.models import Recipe, RecipeYeast, RecipeFermentable, RecipeHop


class BeerSmithNode:
    def __init__(self, node: Element) -> None:
        self.node = node
        self.child_by_name = {}
        self.load_children()

    def load_children(self):
        for node in list(self.node):
            node = BeerSmithNode(node)
            if node.tag_name is not None:
                self.child_by_name[node.tag_name] = node

    def get_child(self, tag_name: str) -> Optional[BeerSmithNode]:
        tag_name = tag_name.lower()
        if tag_name in self.child_by_name:
            return self.child_by_name[tag_name]
        return None

    @property
    def children(self) -> iter:
        for node in list(self.node):
            yield BeerSmithNode(node)

    @property
    def text(self):
        return self.node.text or ""

    @property
    def tag_name(self):
        tag_name = to_lower(self.node.tag)
        if tag_name is None:
            return None

        if tag_name == '_mod_':
            return "last_modified"

        search = re.search("f_(\\w{1,2}_)?(.+)", tag_name)
        if search:
            return search.group(2)

        return tag_name

    def int_or_none(self, child_name):
        child_name = child_name.lower()
        child_node = self.get_child(child_name)
        if child_node:
            return int_or_none(child_node.text)
        return None

    def float_or_none(self, child_name):
        child_name = child_name.lower()
        child_node = self.get_child(child_name)
        if child_node:
            return float_or_none(child_node.text)
        return None

    def string_or_none(self, child_name):
        child_name = child_name.lower()
        child_node = self.get_child(child_name)
        if child_node:
            return string_or_none(child_node.text)
        return None


class BeerSmithParser(FormatParser):
    HOP_TYPE_MAP = [RecipeHop.BITTERING, RecipeHop.AROMA, RecipeHop.DUAL_PURPOSE]
    HOP_FORM_MAP = [RecipeHop.PELLET, RecipeHop.PLUG, RecipeHop.LEAF]
    HOP_USE_MAP = [RecipeHop.BOIL, RecipeHop.DRY_HOP, RecipeHop.MASH, RecipeHop.FIRST_WORT, RecipeHop.AROMA]
    FERMENTABLE_FORM_MAP = [RecipeFermentable.GRAIN, RecipeFermentable.EXTRACT, RecipeFermentable.SUGAR, RecipeFermentable.ADJUNCT, RecipeFermentable.DRY_EXTRACT]
    MISC_USE_MAP = ["Boil", "Mash", "Primary", "Secondary", "Bottling", "Sparge"]
    YEAST_FLOCCULATION_MAP = [RecipeYeast.LOW, RecipeYeast.MEDIUM, RecipeYeast.HIGH, RecipeYeast.VERY_HIGH]
    YEAST_TYPE_MAP = [RecipeYeast.ALE, RecipeYeast.LAGER, RecipeYeast.WINE, RecipeYeast.CHAMPAGNE, RecipeYeast.WHEAT]
    YEAST_FORM_MAP = [RecipeYeast.LIQUID, RecipeYeast.DRY, RecipeYeast.SLANT, RecipeYeast.CULTURE]

    def parse(self, result: ParserResult, file_path: str) -> None:
        try:
            with open(file_path, "rt") as f:
                parser = etree.XMLParser(recover=True, resolve_entities=True, encoding='utf-8')
                tree = etree.parse(file_path, parser)
        except Exception as e:
            raise MalformedDataError("Cannot process xml file because of {}: {}".format(type(e), str(e)))

        recipe_node = None
        for node in tree.iter():
            if to_lower(node.tag) == "recipe":
                recipe_node = node
                break

        if recipe_node is None:
            raise MalformedDataError("Could not find recipe node in BeerSmith XML")

        bs_recipe = BeerSmithNode(recipe_node)
        self.parse_recipe(result.recipe, bs_recipe)
        result.fermentables.extend(self.get_fermentables(bs_recipe))
        result.hops.extend(self.get_hops(bs_recipe))
        result.yeasts.extend(self.get_yeasts(bs_recipe))
        self.parse_misc(file_path, bs_recipe)

        # Calculated values
        if result.recipe.og is None:
            result.recipe.og = self.calc_og(result.recipe, result.fermentables)
        if result.recipe.fg is None:
            result.recipe.fg = self.calc_fg(result.recipe, result.yeasts)
        result.recipe.srm = self.calc_srm(result.recipe, result.fermentables)
        result.recipe.ibu = self.calc_ibu(result.recipe, result.hops)

    def parse_recipe(self, recipe: Recipe, bs_recipe: BeerSmithNode) -> None:
        recipe.name = bs_recipe.string_or_none('name')
        recipe.author = bs_recipe.string_or_none('brewer')
        creation_date = bs_recipe.string_or_none('date')

        if creation_date is None or creation_date == '1969-12-31':
            creation_date = bs_recipe.string_or_none('last_modified')

        # Style
        bs_style = bs_recipe.get_child('style')
        if bs_style:
            recipe.style_raw = clean_kind(bs_style.string_or_none('name'))

        # Recipe
        recipe.og = bs_recipe.float_or_none('og_measured')
        recipe.fg = bs_recipe.float_or_none('fg_measured')
        if recipe.og == 1.046 and recipe.fg == 1.010:
            # These seem to be default values, so they're meaningless
            recipe.og = None
            recipe.fg = None

        (recipe.mash_water, recipe.sparge_water) = self.get_mash_water(bs_recipe)

        # Equipment values
        cast_out_ounces = None
        bs_equipment = bs_recipe.get_child('equipment')
        if bs_equipment:
            if creation_date is None or creation_date == '1969-12-31':
                creation_date = bs_equipment.string_or_none('last_modified')
            recipe.boiling_time = bs_equipment.float_or_none('boil_time')
            recipe.extract_efficiency = bs_equipment.float_or_none('efficiency')
            cast_out_ounces = bs_equipment.float_or_none('batch_vol')

        if recipe.extract_efficiency is None:
            recipe.extract_efficiency = bs_recipe.float_or_none('old_efficiency')

        # Boiling
        if cast_out_ounces is None or cast_out_ounces == 0.0:
            cast_out_ounces = bs_recipe.float_or_none('volume_measured')
        if cast_out_ounces is None or cast_out_ounces == 0.0:
            cast_out_ounces = bs_recipe.float_or_none('final_vol_measured')
        if cast_out_ounces == 0.0:
            cast_out_ounces = None

        recipe.cast_out_wort = fluid_ounces_to_liters(cast_out_ounces) if cast_out_ounces is not None else None

        # Hopefully we've found a creation date
        if creation_date is not None and creation_date != '1969-12-31':
            try:
                recipe.created = datetime.strptime(creation_date, '%Y-%m-%d')
            except ValueError:
                pass

    def get_mash_water(self, bs_recipe: BeerSmithNode):
        bs_mash = bs_recipe.get_child('mash')
        if bs_mash is None:
            return None, None

        mash_water = None
        sparge_water = None
        sparge_temp = bs_mash.float_or_none('sparge_temp')
        mash_steps = self.get_mash_steps(bs_recipe)

        # Mash water
        if len(mash_steps) > 0:
            mash_water = mash_steps[0].float_or_none('infusion')
            if mash_water is not None:
                mash_water = fluid_ounces_to_liters(mash_water)

        # Sparge water
        if sparge_temp is not None:
            sparge_water = 0
            for mash_step in mash_steps:
                temp = mash_step.float_or_none('step_temp')
                water = mash_step.float_or_none('infusion')
                if temp is not None and water is not None and temp >= sparge_temp:
                    sparge_water += water
            sparge_water = None if sparge_water == 0 else fluid_ounces_to_liters(sparge_water)

        return mash_water, sparge_water

    def calc_og(self, recipe: Recipe, fermentables: List[RecipeFermentable]):
        if recipe.cast_out_wort is None:
            return None

        og = 1.0

        # Calculate gravities from fermentables
        for fermentable in fermentables:
            efficiency = fermentable.extract_efficiency

            gu = fermentable.gu(recipe.cast_out_wort)
            if gu is None:
                return None

            og += gu * efficiency / 1000.0

        return og

    def calc_fg(self, recipe: Recipe, yeasts: List[RecipeYeast]):
        if recipe.og is None:
            return None

        # Get attenuation for final gravity
        attenuation = 0
        for yeast in yeasts:
            if yeast.attenuation is not None and yeast.attenuation > attenuation:
                attenuation = yeast.attenuation

        if attenuation <= 0:
            attenuation = 75

        return recipe.og - ((recipe.og - 1.0) * attenuation / 100.0)

    def calc_srm(self, recipe: Recipe, fermentables: List[RecipeFermentable]) -> Optional[float]:
        if recipe.cast_out_wort is None or len(fermentables) == 0:
            return None

        mcu = 0.0
        for fermentable in fermentables:
            if fermentable.amount is not None and fermentable.color_lovibond is not None:
                # 8.3454 is conversion factor from kg/L to lb/gal
                mcu += (fermentable.amount / 1000) * fermentable.color_lovibond * 8.3454 / recipe.cast_out_wort
        return 1.4922 * (mcu ** 0.6859)

    def calc_ibu(self, recipe: Recipe, hops: List[RecipeHop]) -> Optional[float]:
        if (ibu := self.calc_ibu_contrib(hops)) is not None:
            return ibu
        if (ibu := self.calc_ibu_tinseth(recipe, hops)) is not None:
            return ibu
        return None

    def calc_ibu_contrib(self, hops: List[RecipeHop]) -> Optional[float]:
        ibu = 0.0
        for hop in hops:
            if hasattr(hop, 'ibu_contrib'):
                ibu += getattr(hop, 'ibu_contrib')
        return None if ibu == 0.0 else ibu

    def calc_ibu_tinseth(self, recipe: Recipe, hops: List[RecipeHop]) -> Optional[float]:
        if recipe.og is None or recipe.cast_out_wort is None or len(hops) == 0:
            return None

        ibu = 0.0
        for hop in hops:
            if hop.alpha and hop.use != RecipeHop.DRY_HOP:
                ibu += hop.ibu_tinseth(recipe.og, recipe.cast_out_wort)

        return None if ibu == 0.0 else ibu

    def get_mash_steps(self, bs_recipe: BeerSmithNode) -> List[BeerSmithNode]:
        try:
            return list(bs_recipe.get_child('mash').get_child('steps').get_child('data').children)
        except AttributeError:
            return []

    def parse_misc(self, file_path, bs_recipe: BeerSmithNode) -> None:
        # TODO: Decide what to do with miscs
        # for bs_misc in self.get_ingredients_of_type(bs_recipe, ['misc']):
        #     use = bs_misc.int_or_none('use')
        pass

    def get_fermentables(self, bs_recipe: BeerSmithNode) -> iter:
        for bs_fermentable in self.get_ingredients_of_type(bs_recipe, ['grain']):
            amount = bs_fermentable.float_or_none('amount')
            if amount is not None:
                amount = ounces_to_gramms(amount)

            name = clean_kind(bs_fermentable.string_or_none('name'))

            fermentable = RecipeFermentable()
            fermentable.kind_raw = name
            fermentable.amount = amount
            fermentable.form = self.get_fermentable_form(bs_fermentable)
            fermentable.origin_raw = clean_kind(bs_fermentable.string_or_none('origin'))
            fermentable.color_lovibond = bs_fermentable.float_or_none('color')
            fermentable._yield = bs_fermentable.float_or_none('yield')

            yield fermentable

    def get_fermentable_form(self, bs_fermentable: BeerSmithNode):
        if bs_fermentable.tag_name == 'grain':
            value = bs_fermentable.int_or_none('type')
            if value is not None and value < len(self.FERMENTABLE_FORM_MAP):
                return self.FERMENTABLE_FORM_MAP[value]
        return None

    def get_hops(self, bs_recipe: BeerSmithNode) -> iter:
        for bs_hop in self.get_ingredients_of_type(bs_recipe, ['hops']):
            amount = bs_hop.float_or_none('amount')
            if amount is not None:
                amount = ounces_to_gramms(amount)

            name = clean_kind(bs_hop.string_or_none('name'))

            hop = RecipeHop()
            hop.kind_raw = name
            hop.amount = amount
            hop.use = self.get_hop_use(bs_hop)
            hop.type = self.get_hop_type(bs_hop)
            hop.form = self.get_hop_form(bs_hop)

            hop.alpha = bs_hop.float_or_none('alpha')
            hop.beta = bs_hop.float_or_none('beta')
            hop.hsi = bs_hop.float_or_none('hsi')

            notes = bs_hop.string_or_none('notes')
            sub_search = re.search('Subst\w*:(.+)', notes)
            if sub_search:
                hop.substitutes = sub_search.group(1).strip()

            # Add an extra attribute to pass the value around
            hop.ibu_contrib = bs_hop.float_or_none('ibu_contrib') or 0.0

            if hop.use != RecipeHop.DRY_HOP:
                hop.time = bs_hop.float_or_none('boil_time')

            # Force dry hop use when dry hop time is set
            dry_hop_time = bs_hop.float_or_none('dry_hop_time')
            if dry_hop_time is not None and dry_hop_time > 0:
                hop.use = RecipeHop.DRY_HOP
                hop.time = dry_hop_time * 24 * 60  # Days to minutes

            # Force Aroma use when boil time is low
            if hop.use == RecipeHop.BOIL and hop.time is not None and hop.time <= 5:
                hop.use = RecipeHop.AROMA

            yield hop

    def get_hop_use(self, bs_hop: BeerSmithNode):
        value = bs_hop.int_or_none('use')
        if value is not None and value < len(self.HOP_USE_MAP):
            return self.HOP_USE_MAP[value]
        return RecipeHop.BOIL

    def get_hop_type(self, bs_hop: BeerSmithNode):
        value = bs_hop.int_or_none('type')
        if value is not None and value < len(self.HOP_TYPE_MAP):
            return self.HOP_TYPE_MAP[value]
        return None

    def get_hop_form(self, bs_hop: BeerSmithNode):
        value = bs_hop.int_or_none('form')
        if value is not None and value < len(self.HOP_FORM_MAP):
            return self.HOP_FORM_MAP[value]
        return None

    def get_yeasts(self, bs_recipe: BeerSmithNode) -> iter:
        for bs_yeast in self.get_ingredients_of_type(bs_recipe, ['yeast']):
            name = clean_kind(bs_yeast.string_or_none('name'))
            yeast = RecipeYeast(kind_raw=name)

            yeast.lab = bs_yeast.string_or_none('lab')
            yeast.product_id = bs_yeast.string_or_none('product_id')
            yeast.form = self.get_yeast_form(bs_yeast)
            yeast.type = self.get_yeast_type(bs_yeast)
            yeast.min_attenuation = bs_yeast.float_or_none('min_attenuation')
            yeast.max_attenuation = bs_yeast.float_or_none('max_attenuation')
            yeast.flocculation = self.get_yeast_flocculation(bs_yeast)

            min_temp = bs_yeast.float_or_none('min_temp')
            max_temp = bs_yeast.float_or_none('max_temp')
            yeast.min_temperature = None if min_temp is None else fahrenheit_to_celsius(min_temp)
            yeast.max_temperature = None if max_temp is None else fahrenheit_to_celsius(max_temp)

            yield yeast

    def get_yeast_type(self, bs_yeast: BeerSmithNode):
        value = bs_yeast.int_or_none('type')
        if value is not None and value < len(self.YEAST_TYPE_MAP):
            return self.YEAST_TYPE_MAP[value]
        return None

    def get_yeast_form(self, bs_yeast: BeerSmithNode):
        value = bs_yeast.int_or_none('form')
        if value is not None and value < len(self.YEAST_FORM_MAP):
            return self.YEAST_FORM_MAP[value]
        return None

    def get_yeast_flocculation(self, bs_yeast: BeerSmithNode):
        value = bs_yeast.int_or_none('flocculation')
        if value is not None and value < len(self.YEAST_FLOCCULATION_MAP):
            return self.YEAST_FLOCCULATION_MAP[value]
        return None

    def get_ingredients_of_type(self, bs_recipe: BeerSmithNode, types: list) -> Iterable[BeerSmithNode]:
        for ingredient in self.get_ingredients(bs_recipe):
            if ingredient.tag_name in types:
                yield ingredient

    def get_ingredients(self, bs_recipe: BeerSmithNode) -> List[BeerSmithNode]:
        try:
            return list(bs_recipe.get_child('ingredients').get_child('data').children)
        except AttributeError:
            return []
