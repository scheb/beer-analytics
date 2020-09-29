from os import path

from django.test import TestCase

from recipe_db.format import beersmith
from recipe_db.format.parser import ParserResult
from recipe_db.models import RecipeHop, RecipeFermentable


class BeerSmithParserTests(TestCase):

    def test_parse_recipe(self):
        parser = beersmith.BeerSmithParser()
        file = path.join(path.dirname(__file__), "fixtures/beersmith.xml")
        result = ParserResult()
        parser.parse(result, file)

        recipe = result.recipe
        hops = result.hops
        fermentables = result.fermentables
        yeasts = result.yeasts

        self.assertEqual('Barrel Dopplebock', recipe.name)
        self.assertEqual('LDB', recipe.author)
        self.assertEqual('Doppelbock', recipe.style_raw)
        self.assertEqual(72, recipe.extract_efficiency)
        self.assertEqual(1.065, round(recipe.og, 3))
        self.assertEqual(1.018, round(recipe.fg, 3))
        self.assertEqual(24.2, round(recipe.ibu, 1))  # Calculated
        self.assertEqual(23.0, round(recipe.srm, 1))  # Calculated
        self.assertEqual(18.04, round(recipe.mash_water, 2))
        self.assertEqual(10.10, round(recipe.sparge_water, 2))
        self.assertEqual(18.93, round(recipe.cast_out_wort, 2))
        self.assertEqual(60, recipe.boiling_time)

        # Fermentables
        self.assertEquals(5, len(fermentables))

        self.assertEquals('Munich II (Weyermann)', fermentables[0].kind_raw)
        self.assertEquals(3855.53, round(fermentables[0].amount, 2))
        self.assertEquals(RecipeFermentable.GRAIN, fermentables[0].form)
        self.assertEquals('Germany', fermentables[0].origin_raw)
        self.assertEquals(8.5, round(fermentables[0].color_lovibond, 1))
        self.assertEquals(82.23, round(fermentables[0]._yield, 2))

        self.assertEquals('Melanoidin (Weyermann)', fermentables[1].kind_raw)
        self.assertEquals('Caraaroma', fermentables[2].kind_raw)
        self.assertEquals('Caramunich III (Weyermann)', fermentables[3].kind_raw)
        self.assertEquals('Pilsner (2 Row) Bel', fermentables[4].kind_raw)

        # Hops
        self.assertEquals(3, len(hops))

        self.assertEquals('Magnum', hops[0].kind_raw)
        self.assertEquals(14.17, round(hops[0].amount, 2))
        self.assertEquals(12, hops[0].alpha)
        self.assertEquals(RecipeHop.BITTERING, hops[0].type)
        self.assertEquals(RecipeHop.PELLET, hops[0].form)
        self.assertEquals(RecipeHop.BOIL, hops[0].use)
        self.assertEquals(60, hops[0].time)

        self.assertEquals('Hallertau', hops[1].kind_raw)
        self.assertEquals(28.35, round(hops[1].amount, 2))
        self.assertEquals(4.8, hops[1].alpha)
        self.assertEquals(RecipeHop.AROMA, hops[1].type)
        self.assertEquals(RecipeHop.PELLET, hops[1].form)
        self.assertEquals(RecipeHop.BOIL, hops[1].use)
        self.assertEquals(20, hops[1].time)

        self.assertEquals('Hallertau', hops[2].kind_raw)
        self.assertEquals(RecipeHop.DRY_HOP, hops[2].use)
        self.assertEquals(3*24*60, hops[2].time)

        # Yeasts
        self.assertEquals(1, len(yeasts))
        self.assertEquals('Harvest', yeasts[0].kind_raw)
