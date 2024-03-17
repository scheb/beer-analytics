from urllib.parse import urlencode

from django.http import HttpResponse, HttpRequest, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.hop import HopFlavorAnalysis
from recipe_db.analytics.spotlight.hop import HopAnalysis
from recipe_db.models import Hop, Tag
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.hop import HopChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import HopMeta, HopOverviewMeta, HopFlavorOverviewMeta, HopFlavorMeta
from web_app.views.hop_flavor import redirect_to_hop_flavor
from web_app.views.utils import render_chart, FORMAT_PNG, render_recipes_list, no_data_response, \
    get_hop_type_description, get_flavor_description, get_hop_description, get_flavor_category_description


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def overview(request: HttpRequest) -> HttpResponse:
    most_popular = Hop.objects.order_by("-search_popularity")[:5]
    hops = Hop.objects.filter(recipes_count__gt=0).order_by("name")

    meta = HopOverviewMeta().get_meta()
    context = {
        "hops": hops,
        "most_popular": most_popular,
        "meta": meta,
        "num_hops": hops.count()
    }

    return render(request, "hop/overview.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def category(request: HttpRequest, category_id: str) -> HttpResponse:
    categories = Hop.get_categories()
    if category_id in categories:
        return render_category(request, category_id)

    # Is it a hop?
    try:
        hop = Hop.objects.get(pk=category_id)
        return redirect_to_hop(hop)
    except Hop.DoesNotExist:
        pass

    # Is it a flavor?
    try:
        tag_obj = Tag.objects.get(pk=category_id)
        return redirect_to_hop_flavor(tag_obj)
    except Tag.DoesNotExist:
        pass

    raise Http404("Unknown hop category %s." % category)


def render_category(request: HttpRequest, category_id: str) -> HttpResponse:
    categories = Hop.get_categories()
    hops_query = Hop.objects.filter(use=category_id, recipes_count__gt=0)

    hops = hops_query.order_by("name")
    most_popular = hops_query.order_by("-search_popularity")[:5]
    category_name = categories[category_id]
    long_description_template = get_hop_type_description(category_id)

    meta = HopOverviewMeta((category_id, category_name)).get_meta()
    context = {
        "category_name": category_name,
        "hops": hops,
        "most_popular": most_popular,
        "long_description": long_description_template,
        "meta": meta
    }

    return render(request, "hop/category.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def detail(request: HttpRequest, slug: str, category_id: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=slug.lower())

    if category_id != hop.category or slug != hop.id:
        return redirect_to_hop(hop)

    meta_provider = HopMeta(hop)
    meta = meta_provider.get_meta()
    if hop.recipes_count is not None and hop.recipes_count > 100:
        meta.image = reverse(
            "hop_chart",
            kwargs=dict(
                category_id=hop.category,
                slug=hop.id,
                chart_type="og",
                format=FORMAT_PNG,
            ),
        )

    long_description_template = get_hop_description(hop.id)
    context = {
        "hop": hop,
        "description": meta_provider.get_description_html(),
        "long_description": long_description_template,
        "meta": meta
    }

    return render(request, "hop/detail.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def chart_data(request: HttpRequest, slug: str, category_id: str, chart_type: str) -> HttpResponse:
    return chart(request, slug, category_id, chart_type, "json")


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="images")
def chart_image(request: HttpRequest, slug: str, category_id: str, chart_type: str, format: str) -> HttpResponse:
    return chart(request, slug, category_id, chart_type, format)


def chart(request: HttpRequest, slug: str, category_id: str, chart_type: str, format: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=slug.lower())

    if hop.recipes_count is None or hop.recipes_count <= 0:
        raise Http404("Hop doesn't have any data.")

    if category_id != hop.category or slug != hop.id:
        return redirect("hop_chart", category_id=hop.category, slug=hop.id, chart_type=chart_type, format=format, permanent=True)

    if HopChartFactory.is_supported_chart(chart_type):
        try:
            chart = HopChartFactory.plot_chart(hop, chart_type)
        except NoDataException:
            return no_data_response()
    else:
        raise Http404("Unknown chart type %s." % chart_type)

    return render_chart(chart, format)


@cache_page(0)
def recipes(request: HttpRequest, slug: str, category_id: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=slug.lower())

    if hop.recipes_count is None or hop.recipes_count <= 0:
        raise Http404("Hop doesn't have any data.")

    if category_id != hop.category or slug != hop.id:
        return redirect("hop_recipes", category_id=hop.category, slug=hop.id, permanent=True)

    recipes_list = HopAnalysis(hop).random_recipes(24)
    context = {
        "recipes_search_url": reverse("search") + "?" + urlencode({'hops': hop.id})
    }
    return render_recipes_list(request, recipes_list, "Hops", context)


def catch_all(request: HttpRequest, slug: str, category_id: str, subpath: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=slug.lower())
    return redirect_to_hop(hop)


def redirect_to_hop(hop: Hop) -> HttpResponseRedirect:
    return redirect("hop_detail", category_id=hop.category, slug=hop.id, permanent=True)
