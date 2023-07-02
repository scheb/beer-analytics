from typing import Tuple

from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.spotlight.fermentable import FermentableAnalysis
from recipe_db.models import Fermentable
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.fermentable import FermentableChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import FermentableMeta, FermentableOverviewMeta
from web_app.views.utils import render_chart, FORMAT_PNG, render_recipes_list, get_template_if_exists


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def overview(request: HttpRequest) -> HttpResponse:
    fermentables = Fermentable.objects.filter(recipes_count__gt=0).order_by("name")
    fermentable_categories = group_by_category(fermentables)
    for fermentable_category in fermentable_categories:
        if len(fermentable_category["fermentables"]) > 5:
            fermentable_category["most_popular"] = Fermentable.objects.filter(
                category=fermentable_category["id"]
            ).order_by("-recipes_count")[:5]
        (fermentable_category["fermentables"], fermentable_category["types"]) = group_by_type(
            fermentable_category["fermentables"]
        )

    meta = FermentableOverviewMeta().get_meta()
    context = {"categories": fermentable_categories, "num_fermentables": fermentables.count(), "meta": meta}

    return render(request, "fermentable/overview.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def category(request: HttpRequest, category_id: str) -> HttpResponse:
    categories = Fermentable.get_categories()
    if category_id not in categories:
        raise Http404("Unknown fermentable category %s." % category_id)

    category_name = categories[category_id]

    fermentables_query = Fermentable.objects.filter(category=category_id, recipes_count__gt=0)
    (fermentables, types) = group_by_type(fermentables_query.order_by("name"))

    most_popular = []
    if fermentables_query.count() > 5:
        most_popular = fermentables_query.order_by("-recipes_count")[:5]

    meta = FermentableOverviewMeta((category_id, category_name)).get_meta()
    long_description_template = get_template_if_exists("fermentable/descriptions/%s.html" % category_id)
    context = {
        "category_name": category_name,
        "fermentables": fermentables,
        "types": types,
        "most_popular": most_popular,
        "long_description": long_description_template,
        "meta": meta,
    }

    return render(request, "fermentable/category.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def detail(request: HttpRequest, slug: str, category_id: str) -> HttpResponse:
    try:
        fermentable = get_object_or_404(Fermentable, pk=slug.lower())
    except Http404 as err:
        # Gracefully redirect when the "-malt" suffix is missing
        if not slug.endswith("-malt"):
            fermentable = get_object_or_404(Fermentable, pk=slug + "-malt")
        else:
            raise err

    if fermentable.recipes_count is None or fermentable.recipes_count <= 0:
        raise Http404("Fermentable doesn't have any data.")

    if category_id != fermentable.category or slug != fermentable.id:
        return redirect("fermentable_detail", category_id=fermentable.category, slug=fermentable.id, permanent=True)

    meta_provider = FermentableMeta(fermentable)
    meta = meta_provider.get_meta()
    if fermentable.recipes_count is not None and fermentable.recipes_count > 100:
        meta.image = reverse(
            "fermentable_chart",
            kwargs=dict(
                category_id=fermentable.category,
                slug=fermentable.id,
                chart_type="og",
                format=FORMAT_PNG,
            ),
        )

    long_description_template = get_template_if_exists("fermentable/descriptions/fermentables/%s.html" % fermentable.id)
    context = {
        "fermentable": fermentable,
        "description": meta_provider.get_description_html(),
        "long_description": long_description_template,
        "meta": meta
    }

    return render(request, "fermentable/detail.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def chart_data(request: HttpRequest, slug: str, category_id: str, chart_type: str) -> HttpResponse:
    return chart(request, slug, category_id, chart_type, "json")


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="images")
def chart_image(request: HttpRequest, slug: str, category_id: str, chart_type: str, format: str) -> HttpResponse:
    return chart(request, slug, category_id, chart_type, format)


def chart(request: HttpRequest, slug: str, category_id: str, chart_type: str, format: str) -> HttpResponse:
    fermentable = get_object_or_404(Fermentable, pk=slug.lower())

    if fermentable.recipes_count is None or fermentable.recipes_count <= 0:
        raise Http404("Fermentable doesn't have any data.")

    if category_id != fermentable.category or slug != fermentable.id:
        return redirect(
            "fermentable_chart",
            category_id=fermentable.category,
            slug=fermentable.id,
            chart_type=chart_type,
            format=format,
            permanent=True,
        )

    if FermentableChartFactory.is_supported_chart(chart_type):
        try:
            chart = FermentableChartFactory.plot_chart(fermentable, chart_type)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404("Unknown chart type %s." % chart_type)

    return render_chart(chart, format)


@cache_page(0)
def recipes(request: HttpRequest, slug: str, category_id: str) -> HttpResponse:
    fermentable = get_object_or_404(Fermentable, pk=slug.lower())

    if fermentable.recipes_count is None or fermentable.recipes_count <= 0:
        raise Http404("Fermentable doesn't have any data.")

    if category_id != fermentable.category or slug != fermentable.id:
        return redirect("fermentable_recipes", category_id=fermentable.category, slug=fermentable.id, permanent=True)

    recipes_list = FermentableAnalysis(fermentable).random_recipes(24)
    return render_recipes_list(recipes_list)


def group_by_category(fermentables: iter) -> list:
    fermentable_categories = {}
    categories = Fermentable.get_categories()

    # Create category object
    for category in categories:
        fermentable_categories[category] = {
            "id": category,
            "name": categories[category],
            "fermentables": [],
            "most_popular": [],
        }

    # Assign fermentables
    for fermentable in fermentables:
        fermentable_categories[fermentable.category]["fermentables"].append(fermentable)

    # Filter categories with fermentables
    categories_filtered = []
    for fermentable_category in fermentable_categories.values():
        if len(fermentable_category["fermentables"]):
            categories_filtered.append(fermentable_category)

    return categories_filtered


def group_by_type(fermentables: iter) -> Tuple[list, list]:
    untyped_fermentables = []
    types = Fermentable.get_types()
    fermentable_types = {}

    # Create type objects
    for t in types:
        fermentable_types[t] = {
            "id": t,
            "name": types[t],
            "fermentables": [],
        }

    # Assign fermentables (if possible)
    for fermentable in fermentables:
        if fermentable.type is not None:
            fermentable_types[fermentable.type]["fermentables"].append(fermentable)
        else:
            untyped_fermentables.append(fermentable)

    # Filter types with fermentables
    types_filtered = []
    for fermentable_type in fermentable_types.values():
        if len(fermentable_type["fermentables"]):
            types_filtered.append(fermentable_type)

    return untyped_fermentables, types_filtered
