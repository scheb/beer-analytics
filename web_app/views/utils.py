import json
from typing import Optional, Iterable

from django.conf import settings
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist, loader
from django.urls import reverse

from recipe_db.models import Style, Hop, Fermentable, Yeast, Recipe, Tag
from web_app.charts.utils import Chart

FORMAT_PNG = "png"
FORMAT_SVG = "svg"
FORMAT_JSON = "json"
FORMATS = [FORMAT_PNG, FORMAT_SVG, FORMAT_JSON]
SOURCE_URL_PATTERNS = settings.__getattr__("SOURCE_URL_PATTERNS")


def render_chart(chart: Chart, data_format: str) -> HttpResponse:
    if data_format == FORMAT_PNG:
        return HttpResponse(chart.render_png(), content_type="image/png")
    elif data_format == FORMAT_SVG:
        return HttpResponse(chart.render_svg(), content_type="image/svg+xml")
    elif data_format == FORMAT_JSON:
        return HttpResponse(chart.render_json(), content_type="application/json")
    else:
        raise Http404("Unknown plotting format %s." % data_format)


def render_recipes_list(recipes: Iterable[Recipe]) -> HttpResponse:
    json_data = []
    for recipe in recipes:
        url = get_recipe_url(recipe.uid)
        if url is not None:
            json_data.append(
                {
                    "name": recipe.name,
                    "author": recipe.author,
                    "url": url,
                }
            )

    return HttpResponse(json.dumps(json_data), content_type="application/json")


def get_recipe_url(uid: str) -> Optional[str]:
    (source, source_id) = uid.split(":")
    if source in SOURCE_URL_PATTERNS:
        return SOURCE_URL_PATTERNS[source] % source_id
    return None


def object_url(item: object):
    if isinstance(item, Style):
        if item.is_category:
            return reverse("style_category", kwargs={"category_slug": item.slug})
        else:
            return reverse("style_detail", kwargs={"category_slug": item.category.slug, "slug": item.slug})

    if isinstance(item, Hop):
        return reverse("hop_detail", kwargs={"category_id": item.use, "slug": item.id})

    if isinstance(item, Fermentable):
        return reverse("fermentable_detail", kwargs={"category_id": item.category, "slug": item.id})

    if isinstance(item, Yeast):
        return reverse("yeast_detail", kwargs={"type_id": item.type, "slug": item.id})

    if isinstance(item, Tag):
        return reverse("hop_flavor_detail", kwargs={"flavor_id": item.id})

    return None


def template_exists(template: str) -> bool:
    try:
        loader.get_template(template)
        return True
    except TemplateDoesNotExist:
        return False
