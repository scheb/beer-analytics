from urllib.parse import urlencode

from django.http import HttpResponse, HttpRequest, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.spotlight.style import StyleAnalysis
from recipe_db.models import Style
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.style import StyleChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import StyleOverviewMeta, StyleMeta
from web_app.views.utils import render_chart, FORMAT_PNG, render_recipes_list, no_data_response, \
    get_style_description


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def overview(request: HttpRequest) -> HttpResponse:
    categories = Style.objects.filter(parent_style=None).order_by("-recipes_count")
    most_popular = Style.objects.exclude(parent_style=None).order_by("-search_popularity")[:5]

    meta = StyleOverviewMeta().get_meta()
    context = {"categories": categories, "most_popular": most_popular, "meta": meta}

    return render(request, "style/overview.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def category(request: HttpRequest, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug)

    if not style.is_category:
        return redirect_to_style(style)

    return display_style(request, style)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def detail(request: HttpRequest, slug: str, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug.lower())

    if style.is_category:
        return redirect_to_style(style)
    elif category_slug != style.category.slug or slug != style.slug:
        return redirect_to_style(style)

    return display_style(request, style)


def display_style(request: HttpRequest, style: Style) -> HttpResponse:
    meta = StyleMeta(style).get_meta()
    if style.recipes_count is not None and style.recipes_count > 100:
        meta.image = reverse(
            "style_chart",
            kwargs=dict(
                category_slug=style.category.slug,
                slug=style.slug,
                chart_type="og",
                format=FORMAT_PNG,
            ),
        )

    long_description_template = get_style_description(style.id)
    context = {"style": style, "meta": meta, "long_description": long_description_template}
    return render(request, "style/detail.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def category_chart_data(request: HttpRequest, category_slug: str, chart_type: str) -> HttpResponse:
    return category_chart(request, category_slug, chart_type, "json")


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="images")
def category_chart_image(request: HttpRequest, category_slug: str, chart_type: str, format: str) -> HttpResponse:
    return category_chart(request, category_slug, chart_type, format)


def category_chart(request: HttpRequest, category_slug: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug.lower())

    if not style.is_category:
        return redirect(
            "style_chart", category_slug=style.category.slug, slug=style.slug, chart_type=chart_type, format=format, permanent=True
        )

    return display_chart(request, style, chart_type, format)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def chart_data(request: HttpRequest, slug: str, category_slug: str, chart_type: str) -> HttpResponse:
    return chart(request, slug, category_slug, chart_type, "json")


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="images")
def chart_image(request: HttpRequest, slug: str, category_slug: str, chart_type: str, format: str) -> HttpResponse:
    return chart(request, slug, category_slug, chart_type, format)


def chart(request: HttpRequest, slug: str, category_slug: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug.lower())

    if style.is_category:
        return redirect("style_category_chart", category_slug=style.category.slug, chart_type=chart_type, format=format, permanent=True)
    if category_slug != style.category.slug or slug != style.slug:
        return redirect(
            "style_chart", category_slug=style.category.slug, slug=style.slug, chart_type=chart_type, format=format, permanent=True
        )

    return display_chart(request, style, chart_type, format)


@cache_page(0)
def category_recipes(request: HttpRequest, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug.lower())

    if not style.is_category:
        return redirect("style_category_recipes", category_slug=style.category.slug, permanent=True)

    recipes_list = StyleAnalysis(style).random_recipes(24)
    return render_recipes_list(request, recipes_list, "Styles")


@cache_page(0)
def recipes(request: HttpRequest, slug: str, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug.lower())

    if style.is_category:
        return redirect("style_category_recipes", category_slug=style.category.slug, permanent=True)
    if category_slug != style.category.slug:
        return redirect("style_recipes", category_slug=style.category.slug, slug=style.slug, permanent=True)

    context = {
        "recipes_search_url": reverse("search") + "?" + urlencode({'styles': style.id})
    }
    recipes_list = StyleAnalysis(style).random_recipes(24)
    return render_recipes_list(request, recipes_list, "Styles", context)


def display_chart(request: HttpRequest, style: Style, chart_type: str, format: str) -> HttpResponse:
    filter_param = str(request.GET["filter"]) if "filter" in request.GET else None

    if StyleChartFactory.is_supported_chart(chart_type):
        try:
            chart = StyleChartFactory.plot_chart(style, chart_type, filter_param)
        except NoDataException:
            return no_data_response()
    else:
        raise Http404("Unknown chart type %s." % chart_type)

    return render_chart(chart, format)


def category_catch_all(request: HttpRequest, category_slug: str, subpath: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug)
    return redirect_to_style(style)


def catch_all(request: HttpRequest, slug: str, category_slug, subpath: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug.lower())
    return redirect_to_style(style)


def redirect_to_style(style: Style) -> HttpResponseRedirect:
    if style.is_category:
        return redirect("style_category", category_slug=style.category.slug, permanent=True)
    else:
        return redirect("style_detail", category_slug=style.category.slug, slug=style.slug, permanent=True)
