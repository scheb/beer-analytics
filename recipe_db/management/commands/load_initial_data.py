import csv
from os import path
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe_db.models import Style, Hop, Fermentable, Yeast, Tag


def make_style_id(value):
    if isinstance(value, int):
        return "%02d" % value
    return value


class Command(BaseCommand):
    help = "Load initial date into the database"

    def handle(self, *args, **options):
        self.stdout.write("Load styles")
        self.load_styles()
        self.stdout.write("Load flavors")
        self.load_flavors()
        self.stdout.write("Load hops")
        self.load_hops()
        self.stdout.write("Load fermentables")
        self.load_fermentables()
        self.stdout.write("Load yeasts")
        self.load_yeasts()
        self.stdout.write("Done")


    def load_styles(self):
        csv_file = load_csv("styles.csv")
        header = next(csv_file)

        styles = {}
        for row in csv_file:
            if len(row) == 1:
                continue  # Skip empty lines

            row = map(cast_values, row)
            data = dict(zip(header, row))

            style_id = make_style_id(data["id"])
            parent_style_id = make_style_id(data["parent_style_id"])
            parent_style = None

            if data["og_min"] is not None:
                data["og_min"] /= 1000
            if data["og_max"] is not None:
                data["og_max"] /= 1000
            if data["fg_min"] is not None:
                data["fg_min"] /= 1000
            if data["fg_max"] is not None:
                data["fg_max"] /= 1000

            if parent_style_id is not None:
                if parent_style_id in styles:
                    parent_style = styles[parent_style_id]
                else:
                    raise Exception("Could not find parent style {}".format(parent_style_id))

            try:
                style = Style.objects.get(pk=style_id)
            except Style.DoesNotExist:
                style = Style()
                pass

            for field in data:
                setattr(style, field, data[field])
            style.id = style_id
            style.parent_style = parent_style
            style.save()
            styles[style.id] = style


    def load_hops(self):
        csv_file = load_csv("hops.csv")
        header = next(csv_file)

        hops_by_name = {}

        data_rows = []
        for row in csv_file:
            if len(row) == 1:
                continue  # Skip empty lines
            row = map(cast_values, row)
            data = dict(zip(header, row))
            data_rows.append(data)

        # Add/update hops
        for data in data_rows:
            hop_id = Hop.create_id(data["name"])
            try:
                hop = Hop.objects.get(pk=hop_id)
                hop.substitutes.clear()
                hop.aroma_tags.clear()
            except Hop.DoesNotExist:
                hop = Hop()
                pass

            for field in data:
                if field not in ["aromas", "substitutes"]:
                    setattr(hop, field, data[field])

            hop.save()
            hops_by_name[hop.name] = hop

        # Update tags & substitutes
        for data in data_rows:
            hop = hops_by_name[data["name"]]
            for tag_name in split_list(data["aromas"]):
                tag = get_tag(normalize_flavor_name(tag_name))
                if tag is None:
                    self.stdout.write("Tag %s does not exists" % tag_name)
                    continue
                hop.aroma_tags.add(tag)

            substitutes = split_list(data["substitutes"])
            for substitute_name in substitutes:
                if substitute_name in hops_by_name:
                    substitute = hops_by_name[substitute_name]
                    hop.substitutes.add(substitute)
                else:
                    print("Substitute hop {} not found".format(substitute_name))


    def load_fermentables(self):
        csv_file = load_csv("fermentables.csv")
        header = next(csv_file)

        for row in csv_file:
            if len(row) == 1:
                continue  # Skip empty lines

            fermentable_id = Fermentable.create_id(row[0])
            row = map(cast_values, row)
            data = dict(zip(header, row))

            try:
                fermentable = Fermentable.objects.get(pk=fermentable_id)
            except Fermentable.DoesNotExist:
                fermentable = Fermentable()
                pass

            for field in data:
                setattr(fermentable, field, data[field])
            fermentable.save()


    def load_yeasts(self):
        csv_file = load_csv("yeasts.csv")
        header = next(csv_file)

        for row in csv_file:
            if len(row) == 1:
                continue  # Skip empty lines

            row = map(cast_values, row)
            data = dict(zip(header, row))
            yeast_id = Yeast.create_id(data["name"], data["lab"], data["brand"], data["product_id"])

            try:
                yeast = Yeast.objects.get(pk=yeast_id)
            except Yeast.DoesNotExist:
                yeast = Yeast()
                pass

            yeast.id = yeast_id
            for field in data:
                setattr(yeast, field, data[field])
            yeast.save()



    def load_flavors(self):
        csv_file = load_csv("flavors.csv")
        header = next(csv_file)

        for row in csv_file:
            if len(row) == 1:
                continue  # Skip empty lines

            row = map(cast_values, row)
            data = dict(zip(header, row))
            tag_id = Tag.create_id(data["name"])

            try:
                tag = Tag.objects.get(pk=tag_id)
            except Tag.DoesNotExist:
                tag = Tag()
                pass

            tag.id = tag_id
            for field in data:
                setattr(tag, field, data[field])
            tag.save()


def get_tag(tag_name: str) -> Optional[Tag]:
    try:
        return Tag.objects.get(pk=Tag.create_id(tag_name))
    except Tag.DoesNotExist:
        return None


def split_list(data) -> list:
    if data is None:
        return []
    items = data.split(",")
    items = list(map(lambda s: s.strip(), items))
    return items


def cast_values(value):
    if isinstance(value, str):
        value = value.strip()

    if value == "":
        return None

    if value == "true":
        return True
    if value == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def load_csv(file_name: str):
    file_path = path.join(settings.__getattr__("BASE_DIR"), "recipe_db", "data", file_name)
    return csv.reader(open(file_path, encoding="utf-8"), delimiter=";")


# Normalize flavors, because it's hard to do it right XD
def normalize_flavor_name(value: str):
    value = value.lower()

    if value == "fruit":
        return "Fruity"

    if value == "spice":
        return "Spicy"

    if value == "tropical":
        return "Tropical Fruits"

    if value == "tropical fruit":
        return "Tropical Fruits"

    if value == "grass":
        return "Grassy"

    if value == "green grass":
        return "Grassy"

    if value == "spice":
        return "Spicy"

    if value == "stonefruit":
        return "Stone Fruit"

    if value == "passion fruit":
        return "Passion Fruit"

    if value == "whitewine":
        return "White Wine"

    if value == "resin":
        return "Resinous"

    if value == "liquorice":
        return "Licorice"

    if value == "berry":
        return "Berries"

    if value == "zest":
        return "Zesty"

    if value == "flowery":
        return "floral"

    return value
