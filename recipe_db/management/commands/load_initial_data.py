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
    for row in csv_file:
        try:
            style_id = create_human_readable_id(row[0])
            query = Style.objects.filter(pk=style_id)
            if query.count() > 0:
                query.update(
                    name=row[0],
                    category=row[2],
                    sub_category=row[1],
                )
            else:
                Style.objects.create(
                    id=style_id,
                    name=row[0],
                    category=row[2],
                    sub_category=row[1],
                )
        except IndexError:
            pass


def load_hops():
    csv_file = load_csv('hops.csv')
    for row in csv_file:
        try:
            hop_id = create_human_readable_id(row[0])
            query = Hop.objects.filter(pk=hop_id)
            if query.count() > 0:
                query.update(
                    name=row[0],
                    category=row[1],
                )
            else:
                Hop.objects.create(
                    id=hop_id,
                    name=row[0],
                    category=row[1],
                )
        except IndexError:
            pass


def create_human_readable_id(value: str) -> str:
    value = codecs.encode(value, 'translit/long')
    return re.sub('\\s+', '_', re.sub('[^\\w\\s]', '', value)).lower()


def load_csv(file_name: str):
    file_path = path.join(settings.__getattr__('BASE_DIR'), 'recipe_db', 'data', file_name)
    return csv.reader(open(file_path, encoding='utf-8'), delimiter=';')
