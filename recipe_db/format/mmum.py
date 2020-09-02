import re
from datetime import datetime
from json import JSONDecodeError
from math import ceil

from recipe_db.format.parser import JsonParser, clean_kind, FormatParser, ParserResult
from recipe_db.models import Recipe, RecipeYeast, RecipeMalt, RecipeHop


class MalformedDataError(Exception):
    pass


class MmumParser(FormatParser):
    def parse_recipe(self, file_path: str) -> ParserResult:
        try:
            data = open(file_path, 'r', encoding='utf-8').read()
            json_data = JsonParser(data)
        except JSONDecodeError:
            raise MalformedDataError("Cannot decode JSON")

        return ParserResult(
            self.get_recipe(json_data),
            list(self.get_malts(json_data)),
            list(self.get_hops(json_data)),
            list(self.get_yeasts(json_data)),
        )

    def get_recipe(self, json_data: JsonParser):
        recipe = Recipe()

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

    def get_malts(self, json_data: JsonParser) -> iter:
        i = 1
        while (kind := json_data.string_or_none("Malz%d" % i)) is not None:
            kind = clean_kind(kind)

            amount = json_data.float_or_none("Malz%d_Menge" % i)
            if amount is not None:
                unit = json_data.string_or_none("Malz%d_Einheit" % i)
                if unit is not None and unit == 'kg':
                    amount *= 1000

            yield RecipeMalt(kind_raw=kind, amount=amount)
            i += 1

    def get_hops(self, json_data: JsonParser) -> iter:
        i = 1
        while (kind := json_data.string_or_none("Hopfen_%d_Sorte" % i)) is not None:
            kind = clean_kind(kind)

            # Clean data
            kind = kind.replace("®", "")
            kind = re.sub("\\s+", " ", kind)
            kind = kind.strip()

            alpha = json_data.float_or_none("Hopfen_%d_alpha" % i)
            amount = json_data.float_or_none("Hopfen_%d_Menge" % i)
            boiling_time = json_data.string_or_none("Hopfen_%d_Kochzeit" % i)
            if boiling_time is not None:
                if boiling_time == 'Whirlpool':
                    boiling_time = 0
                else:
                    boiling_time = json_data.float_or_none("Hopfen_%d_Kochzeit" % i)
                    if boiling_time is not None:
                        boiling_time = ceil(boiling_time)

            yield RecipeHop(kind_raw=kind, alpha=alpha, amount=amount, boiling_time=boiling_time)
            i += 1

    def get_yeasts(self, json_data: JsonParser) -> iter:
        yeast_kind = json_data.string_or_none('Hefe')
        if yeast_kind is not None:
            yield RecipeYeast(kind_raw=yeast_kind)
