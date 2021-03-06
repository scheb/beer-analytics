import csv
from os import path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe_db.models import Style, Hop, Fermentable, Yeast, Tag


def make_style_id(value):
    if isinstance(value, int):
        return '%02d' % value
    return value


class Command(BaseCommand):
    help = "Load initial date into the database"

    def handle(self, *args, **options):
        self.stdout.write('Load styles')
        load_styles()
        self.stdout.write('Load hops')
        load_hops()
        self.stdout.write('Load fermentables')
        load_fermentables()
        self.stdout.write('Load yeasts')
        load_yeasts()
        self.stdout.write('Done')


def load_styles():
    csv_file = load_csv('styles.csv')
    header = next(csv_file)

    styles = {}
    for row in csv_file:
        if len(row) == 1:
            continue  # Skip empty lines

        row = map(cast_values, row)
        data = dict(zip(header, row))

        style_id = make_style_id(data['id'])
        parent_style_id = make_style_id(data['parent_style_id'])
        parent_style = None

        if data['og_min'] is not None:
            data['og_min'] /= 1000
        if data['og_max'] is not None:
            data['og_max'] /= 1000
        if data['fg_min'] is not None:
            data['fg_min'] /= 1000
        if data['fg_max'] is not None:
            data['fg_max'] /= 1000

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


def load_hops():
    csv_file = load_csv('hops.csv')
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
        hop_id = Hop.create_id(data['name'])
        try:
            hop = Hop.objects.get(pk=hop_id)
            hop.substitutes.remove()
            hop.aroma_tags.remove()
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
        hop = hops_by_name[data['name']]
        for tag_name in split_list(data['aromas']):
            tag = get_or_create_tag(tag_name)
            hop.aroma_tags.add(tag)

        substitutes = split_list(data['substitutes'])
        for substitute_name in substitutes:
            if substitute_name in hops_by_name:
                substitute = hops_by_name[substitute_name]
                hop.substitutes.add(substitute)
            else:
                print("Substitute hop {} not found".format(substitute_name))


def get_or_create_tag(tag_name: str) -> Tag:
    try:
        return Tag.objects.get(pk=Tag.create_id(tag_name))
    except Tag.DoesNotExist:
        tag = Tag(name=tag_name)
        tag.save()
        return tag


def split_list(data) -> list:
    if data is None:
        return []
    items = data.split(",")
    items = list(map(lambda s: s.strip(), items))
    return items


def load_fermentables():
    csv_file = load_csv('fermentables.csv')
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


def load_yeasts():
    csv_file = load_csv('yeasts.csv')
    header = next(csv_file)

    for row in csv_file:
        if len(row) == 1:
            continue  # Skip empty lines

        row = map(cast_values, row)
        data = dict(zip(header, row))
        yeast_id = Yeast.create_id(data['name'], data['lab'], data['brand'], data['product_id'])

        try:
            yeast = Yeast.objects.get(pk=yeast_id)
        except Yeast.DoesNotExist:
            yeast = Yeast()
            pass

        yeast.id = yeast_id
        for field in data:
            setattr(yeast, field, data[field])
        yeast.save()


def cast_values(value):
    if isinstance(value, str):
        value = value.strip()

    if value == '':
        return None

    if value == 'true':
        return True
    if value == 'false':
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
    file_path = path.join(settings.__getattr__('BASE_DIR'), 'recipe_db', 'data', file_name)
    return csv.reader(open(file_path, encoding='utf-8'), delimiter=';')
