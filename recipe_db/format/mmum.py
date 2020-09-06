from datetime import datetime
from json import JSONDecodeError
from math import ceil

from recipe_db.format.parser import JsonParser, clean_kind, FormatParser, ParserResult, MalformedDataError
from recipe_db.models import Recipe, RecipeYeast, RecipeFermentable, RecipeHop


class MmumParser(FormatParser):
    def parse(self, result: ParserResult, file_path: str) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
                json_data = JsonParser(data)
        except JSONDecodeError:
            raise MalformedDataError("Cannot decode JSON")

        self.parse_recipe(result.recipe, json_data)
        result.fermentables.extend(self.get_fermentables(json_data))
        result.hops.extend(self.get_hops(json_data))
        result.yeasts.extend(self.get_yeasts(json_data))

    def parse_recipe(self, recipe: Recipe, json_data: JsonParser):
        recipe.name = json_data.string_or_none('Name')
        date_created = json_data.string_or_none('Datum')
        if date_created is not None:
            recipe.created = datetime.strptime(date_created, '%d.%m.%Y')

        # Characteristics
        recipe.style_raw = json_data.string_or_none('Sorte')
        recipe.extract_efficiency_percent = json_data.float_or_none('Sudhausausbeute')
        recipe.extract_plato = json_data.float_or_none('Stammwuerze')
        recipe.alc_percent = json_data.float_or_none('Alkohol')
        recipe.ebc = json_data.int_or_none('Farbe')
        recipe.ibu = json_data.int_or_none('Bittere')

        # Mashing
        recipe.mash_water = json_data.float_or_none('Infusion_Hauptguss')
        recipe.sparge_water = json_data.float_or_none('Nachguss')

        # Boiling
        recipe.cast_out_wort = json_data.int_or_none('Ausschlagswuerze')
        recipe.boiling_time = json_data.int_or_none('Kochzeit_Wuerze')

        return recipe

    def get_fermentables(self, json_data: JsonParser) -> iter:
        i = 1
        while (kind := json_data.string_or_none("Malz%d" % i)) is not None:
            kind = clean_kind(kind)

            amount = json_data.float_or_none("Malz%d_Menge" % i)
            if amount is not None:
                unit = json_data.string_or_none("Malz%d_Einheit" % i)
                if unit is not None and unit == 'kg':
                    amount *= 1000

            yield RecipeFermentable(kind_raw=kind, amount=amount)
            i += 1

    def get_hops(self, json_data: JsonParser) -> iter:
        for hop in self.parse_hops(json_data, 'Hopfen_VWH'):
            hop.use = RecipeHop.FIRST_WORT
            yield hop
        yield from self.parse_hops(json_data, 'Hopfen')
        for hop in self.parse_hops(json_data, 'Stopfhopfen'):
            hop.use = RecipeHop.DRY_HOP
            yield hop

    def parse_hops(self, json_data: JsonParser, prefix: str):
        i = 1
        while (kind := json_data.string_or_none("{}_{}_Sorte".format(prefix, i))) is not None:
            kind = clean_kind(kind)

            use = RecipeHop.BOIL
            alpha = json_data.float_or_none("{}_{}_alpha".format(prefix, i))
            amount = json_data.float_or_none("{}_{}_Menge".format(prefix, i))
            time = json_data.string_or_none("{}_{}_Kochzeit".format(prefix, i))
            if time is not None:
                if time == 'Whirlpool':
                    use = RecipeHop.AROMA
                    time = 0
                else:
                    time = json_data.float_or_none("{}_{}_Kochzeit".format(prefix, i))
                    if time is not None:
                        time = ceil(time)
                        if time < 5:  # Assume aroma use when less than 5mins boiled
                            use = RecipeHop.AROMA

            yield RecipeHop(kind_raw=kind, alpha=alpha, use=use, amount=amount, time=time)
            i += 1

    def get_yeasts(self, json_data: JsonParser) -> iter:
        yeast_kind = json_data.string_or_none('Hefe')
        if yeast_kind is not None:
            yield RecipeYeast(kind_raw=yeast_kind)
