from typing import Optional, Iterable

from django.http import HttpResponse, Http404, HttpRequest, JsonResponse
from django.shortcuts import render
from django.template import TemplateDoesNotExist, loader
from django.urls import reverse

from recipe_db.models import Style, Hop, Fermentable, Yeast, Recipe, Tag, SourceInfo
from web_app.charts.utils import Chart

FORMAT_PNG = "png"
FORMAT_SVG = "svg"
FORMAT_JSON = "json"
FORMATS = [FORMAT_PNG, FORMAT_SVG, FORMAT_JSON]


def render_chart(chart: Chart, data_format: str) -> HttpResponse:
    if data_format == FORMAT_PNG:
        return HttpResponse(chart.render_png(), content_type="image/png")
    elif data_format == FORMAT_SVG:
        return HttpResponse(chart.render_svg(), content_type="image/svg+xml")
    elif data_format == FORMAT_JSON:
        return HttpResponse(chart.render_json(), content_type="application/json")
    else:
        raise Http404("Unknown plotting format %s." % data_format)


def render_recipes_list(request: HttpRequest, recipes: Iterable[Recipe], section_name: str) -> HttpResponse:
    sources = {}
    for source in SourceInfo.objects.all():
        sources[source.source_id] = source

    recipes_list = []
    for recipe in recipes:
        url = "#"
        source = None
        if recipe.source in sources:
            source = sources[recipe.source]
            if source.recipe_url is not None:
                url = source.recipe_url.format(recipe.source_id)

        recipes_list.append({
            "name": recipe.name if not None else "Unnamed recipe",
            "author": recipe.author,
            "source": source,
            "url": url,
        })

    context = {
        "recipes": recipes_list,
        "section_name": section_name,
    }
    return render(request, "random_recipes.html", context)


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


try:
    import content
except ImportError:
    def get_style_description() -> Optional[str]:
        return None
    def get_hop_description() -> Optional[str]:
        return None
    def fetch_hop_type_description() -> Optional[str]:
        return None
    def fetch_flavor_description() -> Optional[str]:
        return None
    def fetch_flavor_category_description() -> Optional[str]:
        return None
    def fetch_fermentable_description() -> Optional[str]:
        return None
    def fetch_fermentable_type_description() -> Optional[str]:
        return None
    def fetch_yeast_description() -> Optional[str]:
        return None
    def fetch_yeast_type_description() -> Optional[str]:
        return None
else:
    from content.loader import (fetch_style_description, fetch_hop_description, fetch_hop_type_description,
                                fetch_flavor_description, fetch_flavor_category_description, fetch_fermentable_description,
                                fetch_fermentable_type_description, fetch_yeast_description, fetch_yeast_type_description)

    def get_style_description(style_id: str) -> Optional[str]:
        return fetch_style_description(style_id)

    def get_hop_description(hop_id: str) -> Optional[str]:
        return fetch_hop_description(hop_id)

    def get_hop_type_description(hop_type_id: str) -> Optional[str]:
        return fetch_hop_type_description(hop_type_id)

    def get_flavor_description(flavor_id: str) -> Optional[str]:
        return fetch_flavor_description(flavor_id)

    def get_flavor_category_description(flavor_category_id: str) -> Optional[str]:
        return fetch_flavor_category_description(flavor_category_id)

    def get_fermentable_description(fermentable_id: str) -> Optional[str]:
        return fetch_fermentable_description(fermentable_id)

    def get_fermentable_type_description(fermentable_type_id: str) -> Optional[str]:
        return fetch_fermentable_type_description(fermentable_type_id)

    def get_yeast_description(yeast_id: str) -> Optional[str]:
        return fetch_yeast_description(yeast_id)

    def get_yeast_type_description(yeast_type_id: str) -> Optional[str]:
        return fetch_yeast_type_description(yeast_type_id)


def no_data_response() -> HttpResponse:
    return JsonResponse({"no_data": True})
