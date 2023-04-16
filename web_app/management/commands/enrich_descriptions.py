import os
import re
from typing import List

from django.core.management.base import BaseCommand

from recipe_db.models import Style, Hop
from web_app.views.utils import object_url


class Command(BaseCommand):
    help = "Enrich descriptions with links to other entities"

    def add_arguments(self, parser):
        parser.add_argument("directory", help="Directory path")

    def handle(self, *args, **options):
        directory = "web_app/templates/" + options["directory"]

        style_replacements: List[dict] = []
        for style in Style.objects.all():
            url = object_url(style)
            for style_name in [style.name] + style.alt_names_list:
                style_replacements.append(dict(id=style.id, name=style_name+"s", url=url, length=len(style_name)+1))  # s at the end
                style_replacements.append(dict(id=style.id, name=style_name, url=url, length=len(style_name)))
        style_replacements.sort(key=lambda x: x['length'], reverse=True)  # Longest names first

        hop_replacements: List[dict] = []
        for hop in Hop.objects.all():
            url = object_url(hop)
            for hop_name in [hop.name] + hop.alt_names_list:
                hop_replacements.append(dict(id=hop.id, name=hop_name, url=url, length=len(hop_name)))
        hop_replacements.sort(key=lambda x: x['length'], reverse=True)  # Longest names first

        for file in os.listdir(directory):
            filename = os.fsdecode(file)

            if filename.endswith(".html"):
                filepath = os.path.join(directory, filename)
                filename_no_extension = os.path.splitext(filename)[0]
                self.stdout.write(filepath)

                with open(filepath, "r") as f:
                    content = f.read()

                for hop in hop_replacements:
                    if hop['id'] == filename_no_extension:
                        continue
                    if hop['url'] in content:
                        continue
                    content = re.sub(r'(?<!>|-|/)\b(' + hop['name'] + r')\b(?!<|-|/)', r'<a href="' + hop['url'] + r'">\1</a>', content, 1)  # Replace first occurrence

                for style in style_replacements:
                    if style['id'] == filename_no_extension:
                        continue
                    if style['url'] in content:
                        continue
                    content = re.sub(r'(?<!>|-|/)\b(' + style['name'] + r')\b(?!<|-|/)', r'<a href="' + style['url'] + r'">\1</a>', content, 1, re.IGNORECASE)  # Replace first occurrence

                with open(filepath, "w") as f:
                    f.write(content)

        self.stdout.write("Done")
