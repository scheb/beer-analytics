import csv
import re
import translitcodec
import codecs
from os import path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe_db.models import Style, Hop


class Command(BaseCommand):
    help = "Load initial date into the database"

    def handle(self, *args, **options):
        self.stdout.write('Load styles')
        load_styles()
        self.stdout.write('Load hops')
        load_hops()
        self.stdout.write('Done')


def load_styles():
    csv_file = load_csv('styles.csv')
    header = next(csv_file)

    for row in csv_file:
        if len(row) == 1:
            continue  # Skip empty lines

        row = map(cast_values, row)
        data = dict(zip(header, row))

        try:
            style = Style.objects.get(pk=data['id'])
        except Style.DoesNotExist:
            style = Style()
            pass

        for field in data:
            setattr(style, field, data[field])
        style.save()


def cast_values(value):
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


def load_hops():
    csv_file = load_csv('hops.csv')
    header = next(csv_file)

    for row in csv_file:
        if len(row) == 1:
            continue  # Skip empty lines

        hop_id = create_human_readable_id(row[0])
        row = map(cast_values, row)
        data = dict(zip(header, row))

        try:
            hop = Hop.objects.get(pk=hop_id)
        except Hop.DoesNotExist:
            hop = Hop()
            pass

        hop.id = hop_id
        for field in data:
            setattr(hop, field, data[field])
        hop.save()


def create_human_readable_id(value: str) -> str:
    value = codecs.encode(value, 'translit/long')
    return re.sub('\\s+', '_', re.sub('[^\\w\\s]', '', value)).lower()


def load_csv(file_name: str):
    file_path = path.join(settings.__getattr__('BASE_DIR'), 'recipe_db', 'data', file_name)
    return csv.reader(open(file_path, encoding='utf-8'), delimiter=';')
