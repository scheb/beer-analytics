from typing import Optional
from xml.etree.ElementTree import Element

from pybeerxml.hop import Hop
from pybeerxml.parser import Parser
from pybeerxml.recipe import Recipe as BeerXMLRecipe

from recipe_db.format.parser import FormatParser, ParserResult, float_or_none, clean_kind, \
    MalformedDataError
from recipe_db.models import Recipe, RecipeYeast, RecipeFermentable, RecipeHop


class BeerXMLParser(FormatParser):
    HOP_USE_MAP = {
        "mash": RecipeHop.MASH,
        "first wort": RecipeHop.FIRST_WORT,
        "boil": RecipeHop.BOIL,
        "aroma": RecipeHop.AROMA,
        "dry hop": RecipeHop.DRY_HOP,
    }

    HOP_TYPE_MAP = {
        "aroma": RecipeHop.AROMA,
        "bittering": RecipeHop.BITTERING,
        "both": RecipeHop.DUAL_PURPOSE,
    }

    HOP_FORM_MAP = {
        "pellet": RecipeHop.PELLET,
        "plug": RecipeHop.PLUG,
        "leaf": RecipeHop.LEAF,
        "extract": RecipeHop.EXTRACT,
    }

    FERMENTABLE_FORM_MAP = {
        "grain": RecipeFermentable.GRAIN,
        "sugar": RecipeFermentable.SUGAR,
        "extract": RecipeFermentable.EXTRACT,
        "dry extract": RecipeFermentable.DRY_EXTRACT,
        "adjunct": RecipeFermentable.ADJUNCT,
        "fruit": RecipeFermentable.ADJUNCT,
    }

    def parse(self, result: ParserResult, file_path: str) -> None:
        try:
            with open(file_path, "rt", encoding='utf-8') as f:
                parser = Parser()
                recipes = parser.parse_from_string(f.read())

        except Exception as e:
            raise MalformedDataError("Cannot process BeerXML file because of {}".format(type(e)))

        if len(recipes) > 1:
            raise MalformedDataError("Cannot process BeerXML file, because it contains more than one recipe")
        beerxml = recipes[0]

        self.parse_recipe(result.recipe, beerxml)
        result.fermentables.extend(self.get_fermentables(beerxml))
        result.hops.extend(self.get_hops(beerxml))
        result.yeasts.extend(self.get_yeasts(beerxml))

    def parse_recipe(self, recipe: Recipe, beerxml: BeerXMLRecipe) -> None:
        recipe.name = beerxml.name
        recipe.author = beerxml.brewer

        # Characteristics
        recipe.style_raw = beerxml.style.name
        recipe.extract_efficiency = beerxml.efficiency
        recipe.og = beerxml.og
        recipe.fg = beerxml.fg
        recipe.abv = self.get_abv(beerxml)
        recipe.ibu = beerxml.ibu
        (recipe.srm, recipe.ebc) = self.get_srm_ebc(beerxml)

        # Mashing
        (recipe.mash_water, recipe.sparge_water) = self.get_mash_water(beerxml)

        # Boiling
        recipe.cast_out_wort = beerxml.batch_size
        recipe.boiling_time = beerxml.boil_time

    def get_srm_ebc(self, beerxml: BeerXMLRecipe):
        (srm, ebc) = self.get_color_metrics(beerxml.color)
        if ebc is not None or srm is not None:
            return srm, ebc

        (srm, ebc) = self.get_color_metrics(beerxml.est_color)
        if ebc is not None or srm is not None:
            return srm, ebc

        # Use calculated value
        return beerxml.color, None

    def get_color_metrics(self, color_value):
        # If it's numeric, it's SRM
        if isinstance(color_value, float) or isinstance(color_value, int):
            return color_value, None

        # If it's a string, check for units
        if isinstance(color_value, str):
            color_value = color_value.strip().lower()
            if color_value.endswith('ebc'):
                ebc = float_or_none(color_value.replace('ebc', '').strip())
                return None, ebc
            elif color_value.endswith('srm'):
                srm = float_or_none(color_value.replace('srm', '').strip())
                return srm, None

        return None, None

    def get_abv(self, beerxml: BeerXMLRecipe):
        abv = beerxml.abv
        if isinstance(abv, str):
            abv = float_or_none(self.strip_abv_unit(abv))

        if isinstance(abv, float):
            return abv

        return None

    def strip_abv_unit(self, value):
        if value is None:
            return None
        return value.replace('%', '').replace('vol', '').strip()

    def child_element_value(self, node: Element, tag_name: str) -> Optional[str]:
        child_node = self.find_child_element(node, tag_name)
        if child_node is not None:
            return child_node.text
        return None

    def find_child_element(self, node: Element, tag_name: str) -> Optional[Element]:
        for child_node in list(node):
            if child_node.tag.lower() == tag_name:
                return child_node
        return None

    def get_mash_water(self, beerxml: BeerXMLRecipe):
        mash = beerxml.mash
        mash_water = 0
        sparge_water = 0
        sparge_temp = 78 if mash.sparge_temp is None else mash.sparge_temp
        if len(mash.steps) > 0:
            first_mash = mash.steps[0]
            amount = first_mash.infuse_amount
            if amount is not None:
                mash_water = amount

        for mash_step in mash.steps:
            temp = mash_step.step_temp
            amount = mash_step.infuse_amount
            if temp is not None and amount is not None:
                if temp >= sparge_temp:
                    sparge_water += amount

        return mash_water if mash_water > 0 else None,\
            sparge_water if sparge_water > 0 else None

    def get_fermentables(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_fermentable in beerxml.fermentables:
            amount = beerxml_fermentable.amount
            if amount is not None:
                amount *= 1000  # convert to grams

            name = clean_kind(beerxml_fermentable.name)

            fermentable = RecipeFermentable()
            fermentable.kind_raw = name
            fermentable.amount = amount
            fermentable.form = self.get_fermentable_form(beerxml_fermentable.type)
            fermentable.origin_raw = clean_kind(beerxml_fermentable.origin)
            fermentable.color_lovibond = beerxml_fermentable.color
            fermentable._yield = beerxml_fermentable._yield

            yield fermentable

    def get_fermentable_form(self, value):
        if value is not None:
            value = clean_kind(value.lower())
            if value in self.FERMENTABLE_FORM_MAP:
                return self.FERMENTABLE_FORM_MAP[value]
        return None

    def get_hops(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_hop in beerxml.hops:
            amount = beerxml_hop.amount
            if amount is not None:
                amount *= 1000  # convert to grams

            name = clean_kind(beerxml_hop.name)

            hop = RecipeHop()
            hop.kind_raw = name
            hop.amount = amount
            hop.use = self.get_hop_use(beerxml_hop)
            hop.alpha = beerxml_hop.alpha
            hop.time = beerxml_hop.time
            hop.type = self.get_hop_type(beerxml_hop.type)
            hop.form = self.get_hop_form(beerxml_hop.form)

            yield hop

    def get_yeasts(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_yeast in beerxml.yeasts:
            yield RecipeYeast(kind_raw=beerxml_yeast.name)

    def get_hop_use(self, beerxml_hop: Hop):
        use_raw = beerxml_hop.use
        if use_raw is not None:
            use_raw = clean_kind(use_raw.lower())
            if use_raw in self.HOP_USE_MAP:
                return self.HOP_USE_MAP[use_raw]

        time = beerxml_hop.time
        if time is not None:
            if time <= 5:
                return RecipeHop.AROMA
            if time > 24*60:
                return RecipeHop.DRY_HOP

        return RecipeHop.BOIL

    def get_hop_type(self, value):
        if value is not None:
            value = clean_kind(value.lower())
            if value in self.HOP_TYPE_MAP:
                return self.HOP_TYPE_MAP[value]
        return None

    def get_hop_form(self, value):
        if value is not None:
            value = clean_kind(value.lower())
            if value in self.HOP_FORM_MAP:
                return self.HOP_FORM_MAP[value]
        return None
