from os import path

from django.test import TestCase

from recipe_db.etl.format import beersmith, beerxml
from recipe_db.etl.format.parser import ParserResult
from recipe_db.models import RecipeHop, RecipeFermentable, RecipeYeast


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
        self.assertEqual(1.058, round(recipe.og, 3))
        self.assertEqual(1.016, round(recipe.fg, 3))
        self.assertEqual(24.2, round(recipe.ibu, 1))  # Calculated
        self.assertEqual(21.2, round(recipe.srm, 1))  # Calculated
        self.assertEqual(18.04, round(recipe.mash_water, 2))
        self.assertEqual(10.10, round(recipe.sparge_water, 2))
        self.assertEqual(21.29, round(recipe.cast_out_wort, 2))
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
        self.assertEquals(RecipeHop.AROMA, hops[1].type)
        self.assertEquals(RecipeHop.PELLET, hops[1].form)
        self.assertEquals(RecipeHop.BOIL, hops[1].use)
        self.assertEquals(20, hops[1].time)
        self.assertEquals(4.8, hops[1].alpha)
        self.assertEquals(5.25, hops[0].beta)

        self.assertEquals('Hallertau', hops[2].kind_raw)
        self.assertEquals(RecipeHop.DRY_HOP, hops[2].use)
        self.assertEquals(3*24*60, hops[2].time)

        # Yeasts
        self.assertEquals(1, len(yeasts))
        self.assertEquals('Harvest', yeasts[0].kind_raw)
        self.assertEquals("Imperial Yeast", yeasts[0].lab)
        self.assertEquals("L17", yeasts[0].product_id)
        self.assertEquals(RecipeYeast.LIQUID, yeasts[0].form)
        self.assertEquals(RecipeYeast.LAGER, yeasts[0].type)
        self.assertEquals(70.0, yeasts[0].min_attenuation)
        self.assertEquals(74.0, yeasts[0].max_attenuation)


class BeerXMLParserTests(TestCase):

    def test_parse_recipe(self):
        parser = beerxml.BeerXMLParser()
        file = path.join(path.dirname(__file__), "fixtures/beerxml.xml")
        result = ParserResult()
        parser.parse(result, file)

        recipe = result.recipe
        hops = result.hops
        fermentables = result.fermentables
        yeasts = result.yeasts

        self.assertEqual('Coffee Stout', recipe.name)
        self.assertEqual('https://github.com/jwjulien', recipe.author)
        self.assertEqual('Dry Stout', recipe.style_raw)
        self.assertEqual(70.0, recipe.extract_efficiency)
        self.assertEqual(1.049, round(recipe.og, 3))
        self.assertEqual(1.015, round(recipe.fg, 3))
        self.assertEqual(35, round(recipe.ibu, 1))
        self.assertEqual(37, round(recipe.srm, 1))
        self.assertEqual(5.76, round(recipe.abv, 2))
        self.assertEqual(12.42, round(recipe.mash_water, 2))
        self.assertEqual(18.30, round(recipe.sparge_water, 2))
        self.assertEqual(20.82, round(recipe.cast_out_wort, 2))
        self.assertEqual(60, recipe.boiling_time)

        # Fermentables
        self.assertEquals(4, len(fermentables))

        self.assertEquals('Simpsons - Maris Otter', fermentables[0].kind_raw)
        self.assertEquals(4876.12, round(fermentables[0].amount, 2))
        self.assertEquals(RecipeFermentable.GRAIN, fermentables[0].form)
        self.assertEquals('UK', fermentables[0].origin_raw)
        self.assertEquals(3, round(fermentables[0].color_lovibond, 1))
        self.assertEquals(81.0, round(fermentables[0]._yield, 2))

        self.assertEquals('Simpsons - Crystal Dark', fermentables[1].kind_raw)
        self.assertEquals('Simpsons - Chocolate Malt', fermentables[2].kind_raw)
        self.assertEquals('Simpsons - Black Malt', fermentables[3].kind_raw)

        # Hops
        self.assertEquals(2, len(hops))

        self.assertEquals('US Fuggles', hops[0].kind_raw)
        self.assertEquals(28.35, round(hops[0].amount, 2))
        self.assertEquals(RecipeHop.DUAL_PURPOSE, hops[0].type)
        self.assertEquals(RecipeHop.PELLET, hops[0].form)
        self.assertEquals(RecipeHop.BOIL, hops[0].use)
        self.assertEquals(60, hops[0].time)
        self.assertEquals(4.5, hops[0].alpha)
        self.assertEquals(2.5, hops[0].beta)

        self.assertEquals('UK Fuggles', hops[1].kind_raw)
        self.assertEquals(12.00, round(hops[1].amount, 2))
        self.assertEquals(4.8, hops[1].alpha)
        self.assertEquals(RecipeHop.AROMA, hops[1].type)
        self.assertEquals(RecipeHop.PELLET, hops[1].form)
        self.assertEquals(RecipeHop.AROMA, hops[1].use)
        self.assertEquals(5, hops[1].time)

        # Yeasts
        self.assertEquals(1, len(yeasts))
        self.assertEquals('Wyeast - London ESB Ale', yeasts[0].kind_raw)
        self.assertEquals('Wyeast Labs', yeasts[0].lab)
        self.assertEquals('1968', yeasts[0].product_id)
        self.assertEquals(RecipeYeast.LIQUID, yeasts[0].form)
        self.assertEquals(RecipeYeast.ALE, yeasts[0].type)
        self.assertEquals(125, yeasts[0].amount)
        self.assertEquals(False, yeasts[0].amount_is_weight)
        self.assertEquals(69.0, yeasts[0].min_attenuation)
        self.assertEquals(69.0, yeasts[0].min_attenuation)
