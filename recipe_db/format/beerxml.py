import locale
from typing import Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from pybeerxml import Parser, Recipe as BeerXMLRecipe
from pybeerxml.hop import Hop

from recipe_db.format.parser import FormatParser, ParserResult, float_or_none, int_or_none
from recipe_db.models import Recipe, RecipeYeast, RecipeMalt, RecipeHop


class MalformedDataError(Exception):
    pass


class BeerXMLParser(FormatParser):
    USE_MAP = {
        "Mash": RecipeHop.MASH,
        "First Wort": RecipeHop.FIRST_WORT,
        "Boil": RecipeHop.BOIL,
        "Aroma": RecipeHop.AROMA,
        "Dry Hop": RecipeHop.DRY_HOP,
    }

    def parse_recipe(self, file: str) -> ParserResult:
        parser = Parser()
        recipes = parser.parse(file)
        if len(recipes) > 1:
            raise MalformedDataError("Cannot process BeerXML file, because it contains more than one recipe")
        beerxml = recipes[0]

        with open(file, "rt") as f:
            tree = ElementTree.parse(f)

        recipe_node = None
        for node in tree.iter():
            if node.tag.lower() == "recipe":
                recipe_node = node

        return ParserResult(
            self.get_recipe(beerxml, recipe_node),
            list(self.get_malts(beerxml)),
            list(self.get_hops(beerxml)),
            list(self.get_yeasts(beerxml)),
        )

    def get_recipe(self, beerxml: BeerXMLRecipe, recipe_node: Element) -> Recipe:
        recipe = Recipe()
        recipe.name = self.fix_encoding(beerxml.name)

        # Characteristics
        recipe.style_raw = self.fix_encoding(beerxml.style.name)
        recipe.extract_efficiency_percent = beerxml.efficiency
        recipe.extract_plato = self.get_og_plato(beerxml, recipe_node)
        recipe.alc_percent = self.get_abv(beerxml, recipe_node)
        recipe.ebc = self.get_ebc(beerxml, recipe_node)
        recipe.ibu = self.get_ibu(beerxml, recipe_node)

        # Mashing
        (recipe.mash_water, recipe.sparge_water) = self.get_mash_water(beerxml)

        # Boiling
        recipe.cast_out_wort = beerxml.batch_size
        recipe.boiling_time = beerxml.boil_time

        return recipe

    def fix_encoding(self, value):
        if value is None:
            return None
        return value.encode(locale.getpreferredencoding(False)).decode("utf-8")

    def get_og_plato(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        sg = self.get_og_sg(beerxml, recipe_node)
        return round((-616.868) + (1111.14 * sg) - (630.272 * sg ** 2) + (135.997 * sg ** 3), 2)

    def get_og_sg(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        og = float_or_none(self.child_element_value(recipe_node, 'og'))
        if og is not None:
            return og

        return beerxml.og

    def get_ebc(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        color_node_value = self.child_element_value(recipe_node, 'est_color')
        if color_node_value is not None:
            color_node_value = color_node_value.strip().lower()
            if color_node_value.endswith('ebc'):
                ebc = int_or_none(color_node_value.replace('ebc', '').strip())
                if ebc is not None:
                    return ebc

        # SRM to EBC, http://www.hillybeer.com/color/
        srm_color = beerxml.color
        return srm_color * 1.97 if srm_color > 0 else None

    def get_ibu(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        ibu = int_or_none(self.child_element_value(recipe_node, 'ibu'))
        if ibu is not None:
            return ibu

        ibu = beerxml.ibu
        return ibu if ibu > 0 else None

    def get_abv(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        abv = float_or_none(self.strip_unit(self.child_element_value(recipe_node, 'abv')))
        if abv is not None:
            return abv

        abv = float_or_none(self.strip_unit(self.child_element_value(recipe_node, 'est_abv')))
        if abv is not None:
            return abv

        return beerxml.abv

    def strip_unit(self, value):
        if value is None:
            return None
        return value.replace('%vol', '')

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
        for mash_step in mash.steps:
            temp = mash_step.step_temp
            amount = mash_step.infuse_amount
            if temp is not None and amount is not None:
                if temp > sparge_temp:
                    sparge_water += amount
                else:
                    mash_water += amount

        return mash_water if mash_water > 0 else None, sparge_water if sparge_water > 0 else None

    def get_malts(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_malt in beerxml.fermentables:
            amount = beerxml_malt.amount
            if amount is not None:
                amount *= 1000  # convert to grams
            yield RecipeMalt(kind_raw=beerxml_malt.name, amount=amount)

    def get_hops(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_hop in beerxml.hops:
            use = self.get_hop_use(beerxml_hop)
            amount = beerxml_hop.amount
            if amount is not None:
                amount *= 1000  # convert to grams
            yield RecipeHop(kind_raw=beerxml_hop.name, alpha=beerxml_hop.alpha, use=use, amount=amount, time=beerxml_hop.time)

    def get_yeasts(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_yeast in beerxml.yeasts:
            yield RecipeYeast(kind_raw=beerxml_yeast.name)

    def get_hop_use(self, beerxml_hop: Hop):
        use_raw = beerxml_hop.use
        if use_raw is not None and use_raw in self.USE_MAP:
            return self.USE_MAP[use_raw]

        time = beerxml_hop.time
        if time is not None:
            if time < 5:
                return RecipeHop.AROMA
            if time > 24*60:
                return RecipeHop.DRY_HOP

        return RecipeHop.BOIL
