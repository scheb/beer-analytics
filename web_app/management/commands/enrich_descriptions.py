import os
import re

from django.core.management.base import BaseCommand
from django.db.models.functions import Length
from django.urls import reverse

from recipe_db.models import Style, Hop


class Command(BaseCommand):
    help = "Enrich descriptions with links to other entities"

    def handle(self, *args, **options):
        styles = Style.objects.all().order_by(Length('name').desc())
        hops = Hop.objects.all().order_by(Length('name').desc())

        directory = "web_app/templates/hop/descriptions"
        for file in os.listdir(directory):
            filename = os.fsdecode(file)

            if filename.endswith(".html"):
                filepath = os.path.join(directory, filename)
                filename_no_extension = os.path.splitext(filename)[0]
                self.stdout.write(filepath)

                with open(filepath, "r") as f:
                    content = f.read()

                for hop in hops:
                    if hop.id == filename_no_extension:
                        continue
                    url = reverse("hop_detail", kwargs=dict(category_id=hop.category, slug=hop.id))
                    content = re.sub(r'(?<!>)(' + hop.name + r')(?!<)', r'<a href="' + url + r'">\1</a>', content, 1)  # Replace first occurrence

                with open(filepath, "w") as f:
                    f.write(content)

        self.stdout.write("Done")
