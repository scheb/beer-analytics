from typing import Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from pybeerxml import Parser, Recipe as BeerXMLRecipe

from recipe_db.format.parser import FormatParser, ParserResult, float_or_none
from recipe_db.models import Recipe, RecipeYeast, RecipeMalt, RecipeHop


class MalformedDataError(Exception):
    pass


class BeerXMLParser(FormatParser):
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
        recipe.name = beerxml.name

        # Characteristics
        recipe.style_raw = beerxml.style.name
        recipe.extract_efficiency_percent = beerxml.efficiency
        recipe.extract_plato = self.get_og_plato(beerxml, recipe_node)
        recipe.alc_percent = self.get_abv(beerxml, recipe_node)
        recipe.ebc = self.get_ebc(beerxml)
        recipe.ibu = self.get_ibu(beerxml)

        # Mashing
        (recipe.mash_water, recipe.sparge_water) = self.get_mash_water(beerxml)

        # Boiling
        recipe.cast_out_wort = beerxml.batch_size
        recipe.boiling_time = beerxml.boil_time

        return recipe

    def get_og_plato(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        sg = self.get_og_sg(beerxml, recipe_node)
        return round((-616.868) + (1111.14 * sg) - (630.272 * sg ** 2) + (135.997 * sg ** 3), 2)

    def get_og_sg(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        og = self.get_float_value_or_none(recipe_node, 'og')
        if og is not None:
            return og

        return beerxml.og

    def get_ebc(self, beerxml: BeerXMLRecipe):
        # SRM to EBC, http://www.hillybeer.com/color/
        srm_color = beerxml.color
        return srm_color * 1.97 if srm_color > 0 else None

    def get_ibu(self, beerxml: BeerXMLRecipe):
        ibu = beerxml.ibu
        return ibu if ibu > 0 else None

    def get_abv(self, beerxml: BeerXMLRecipe, recipe_node: Element):
        abv = self.get_float_value_or_none(recipe_node, 'abv')
        if abv is not None:
            return abv

        abv = self.get_float_value_or_none(recipe_node, 'est_abv')
        if abv is not None:
            return abv

        return beerxml.abv

    def get_float_value_or_none(self, node_tree: Element, tag_name: str):
        node = self.find_element(node_tree, tag_name)
        if node is not None:
            return float_or_none(node.text or "")
        return None

    def find_element(self, node: Element, tag_name: str) -> Optional[Element]:
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
                beerxml_malt.amount += 1000  # convert to grams
            yield RecipeMalt(kind_raw=beerxml_malt.name, amount=beerxml_malt.amount)

    def get_hops(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_hop in beerxml.hops:
            amount = beerxml_hop.amount
            if amount is not None:
                beerxml_hop.amount += 1000  # convert to grams
            yield RecipeHop(kind_raw=beerxml_hop.name, alpha=beerxml_hop.alpha, amount=amount, boiling_time=beerxml_hop.time)

    def get_yeasts(self, beerxml: BeerXMLRecipe) -> iter:
        for beerxml_yeast in beerxml.yeasts:
            yield RecipeYeast(kind_raw=beerxml_yeast.name)
