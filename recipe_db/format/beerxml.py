import locale
from typing import Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from pybeerxml import Parser, Recipe as BeerXMLRecipe
from pybeerxml.hop import Hop

from recipe_db.format.parser import FormatParser, ParserResult, float_or_none, int_or_none, clean_kind, \
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
            parser = Parser()
            recipes = parser.parse(file_path)
        except Exception as e:
            raise MalformedDataError("Cannot process BeerXML file because of {}".format(type(e)))

        if len(recipes) > 1:
            raise MalformedDataError("Cannot process BeerXML file, because it contains more than one recipe")
        beerxml = recipes[0]

        with open(file_path, "rt") as f:
            tree = ElementTree.parse(f)

        recipe_node = None
        for node in tree.iter():
            if node.tag.lower() == "recipe":
                recipe_node = node

        self.parse_recipe(result.recipe, beerxml, recipe_node)
        result.fermentables.extend(self.get_fermentables(beerxml))
        result.hops.extend(self.get_hops(beerxml))
        result.yeasts.extend(self.get_yeasts(beerxml))

    def parse_recipe(self, recipe: Recipe, beerxml: BeerXMLRecipe, recipe_node: Element) -> None:
        recipe.name = self.fix_encoding(beerxml.name)
        recipe.author = self.fix_encoding(beerxml.brewer)

        # Characteristics
        recipe.style_raw = self.fix_encoding(beerxml.style.name)
        recipe.extract_efficiency = beerxml.efficiency
        recipe.og = self.get_og(beerxml, recipe_node)
        recipe.fg = self.get_fg(beerxml, recipe_node)
        recipe.abv = self.get_abv(beerxml, recipe_node)
        recipe.ibu = self.get_ibu(beerxml, recipe_node)
        (recipe.srm, recipe.ebc) = self.get_srm_ebc(beerxml, recipe_node)

        # Mashing
        (recipe.mash_water, recipe.sparge_water) = self.get_mash_water(beerxml)

        # Boiling
        recipe.cast_out_wort = beerxml.batch_size
        recipe.boiling_time = beerxml.boil_time

    def fix_encoding(self, value):
        if value is None:
            return None
        if not isinstance(value, str):
            return str(value)
        return value.encode(locale.getpreferredencoding(False)).decode("utf-8")

    def get_og(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        og = float_or_none(self.child_element_value(recipe_node, 'og'))
        if og is not None:
            return og

        return beerxml.og

    def get_fg(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        og = float_or_none(self.child_element_value(recipe_node, 'fg'))
        if og is not None:
            return og

        return beerxml.fg

    def get_srm_ebc(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        srm = None
        ebc = None

        (srm, ebc) = self.get_color_metrics(recipe_node, 'color')
        if ebc is not None or srm is not None:
            return srm, ebc

        (srm, ebc) = self.get_color_metrics(recipe_node, 'est_color')
        if ebc is not None or srm is not None:
            return srm, ebc

        # Use calculated value
        return beerxml.color, None

    def get_color_metrics(self, recipe_node: Element, element_name: str):
        ebc = None
        srm = None
        color_node_value = self.child_element_value(recipe_node, element_name)
        if color_node_value is not None:
            color_node_value = color_node_value.strip().lower()
            if color_node_value.endswith('ebc'):
                ebc = int_or_none(color_node_value.replace('ebc', '').strip())
            else:
                srm = float_or_none(color_node_value)
        return srm, ebc

    def get_ibu(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        ibu = int_or_none(self.child_element_value(recipe_node, 'ibu'))
        if ibu is not None:
            return ibu

        ibu = beerxml.ibu
        return ibu if ibu > 0 else None

    def get_abv(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        abv = float_or_none(self.strip_abv_unit(self.child_element_value(recipe_node, 'abv')))
        if abv is not None:
            return abv

        abv = float_or_none(self.strip_abv_unit(self.child_element_value(recipe_node, 'est_abv')))
        if abv is not None:
            return abv

        return beerxml.abv

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

            name = clean_kind(self.fix_encoding(beerxml_fermentable.name))

            fermentable = RecipeFermentable()
            fermentable.kind_raw = name
            fermentable.amount = amount
            fermentable.form = self.get_fermentable_form(self.getattr(beerxml_fermentable, 'type'))
            fermentable.origin_raw = clean_kind(self.fix_encoding(self.getattr(beerxml_fermentable, 'origin')))
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

            name = clean_kind(self.fix_encoding(beerxml_hop.name))

            hop = RecipeHop()
            hop.kind_raw = name
            hop.amount = amount
            hop.use = self.get_hop_use(beerxml_hop)
            hop.alpha = beerxml_hop.alpha
            hop.time = beerxml_hop.time
            hop.type = self.get_hop_type(self.getattr(beerxml_hop, 'type'))
            hop.form = self.get_hop_form(self.getattr(beerxml_hop, 'form'))

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

    def getattr(self, object, attribute):
        try:
            return getattr(object, attribute)
        except AttributeError:
            return None

