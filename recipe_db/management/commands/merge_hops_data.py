import csv
import json
from os import path

from django.core.management.base import BaseCommand

from recipe_db.management.commands.load_initial_data import load_csv, cast_values, split_list, normalize_flavor_name


def merge_aromas(aromas_csl: str, new_aromas: list):
    new_aromas = map(str.title, map(normalize_flavor_name, new_aromas))

    if "Tropical Mango" in new_aromas:
        new_aromas.remove("Tropical Mango")
        new_aromas.append("Tropical Fruits")
        new_aromas.append("Mango")

    if "Sweet Aromatic" in new_aromas:
        new_aromas.remove("Sweet Aromatic")
        new_aromas.append("Sweet")
        new_aromas.append("Aromatic")

    if "Citrusy And Floral" in new_aromas:
        new_aromas.remove("Citrusy And Floral")
        new_aromas.append("Citrus")
        new_aromas.append("Floral")

    aromas = set(split_list(aromas_csl))
    merged = sorted(aromas.union(set(new_aromas)))
    return ", ".join(merged)


class Command(BaseCommand):
    help = "Merge hops data into my own data"

    def handle(self, *args, **options):
        out_file = load_csv("hops.csv")
        header = next(out_file)

        hops_by_name = {}
        for row in out_file:
            if len(row) == 1:
                continue  # Skip empty lines
            row = map(cast_values, row)
            data = dict(zip(header, row))
            hops_by_name[data['name']] = data

        with open(path.join(path.dirname(__file__), "../../data/combined.json"), "r", encoding="utf-8") as f:
            hops_data = json.loads(f.read())
            for hop in hops_data:
                aromas = hop['notes']
                hop_name = hop['name']
                if hop_name in hops_by_name:
                    hops_by_name[hop_name]['aromas'] = merge_aromas(hops_by_name[hop_name]['aromas'], aromas)

        with open(path.join(path.dirname(__file__), "../../data/hops_merged.csv"), "w", encoding="utf-8") as out_file:
            fieldnames = header
            writer = csv.DictWriter(out_file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for hop_name in hops_by_name:
                writer.writerow(hops_by_name[hop_name])

