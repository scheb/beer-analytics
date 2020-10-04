import csv
from os import path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe_db.models import Style, Hop, Fermentable, Yeast


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

    for row in csv_file:
        if len(row) == 1:
            continue  # Skip empty lines

        hop_id = Hop.create_id(row[0])
        row = map(cast_values, row)
        data = dict(zip(header, row))

        try:
            hop = Hop.objects.get(pk=hop_id)
        except Hop.DoesNotExist:
            hop = Hop()
            pass

        for field in data:
            setattr(hop, field, data[field])
        hop.save()


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
        yeast_id = Yeast.create_id(data['name'], data['brand'], data['product_id'])

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
