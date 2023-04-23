from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader, TemplateDoesNotExist
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.hop import HopFlavorAnalysis
from recipe_db.analytics.spotlight.hop import HopAnalysis
from recipe_db.models import Hop, Tag
from web_app.charts.hop import HopChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import HopMeta, HopOverviewMeta, HopFlavorOverviewMeta, HopFlavorMeta
from web_app.views.utils import render_chart, FORMAT_PNG, render_recipes_list, template_exists


def overview(request: HttpRequest) -> HttpResponse:
    hop_categories = {}
    categories = Hop.get_categories()
    for category in categories:
        most_popular = Hop.objects.filter(use=category).order_by("-recipes_count")[:5]
        hop_categories[category] = {
            "id": category,
            "name": categories[category],
            "hops": [],
            "most_popular": most_popular,
        }

    hops = Hop.objects.filter(recipes_count__gt=0).order_by("name")
    for hop in hops:
        hop_categories[hop.use]["hops"].append(hop)

    meta = HopOverviewMeta().get_meta()
    context = {"categories": hop_categories.values(), "meta": meta, "num_hops": hops.count()}

    return render(request, "hop/overview.html", context)


def category_or_tag(request: HttpRequest, category_id: str) -> HttpResponse:
    categories = Hop.get_categories()
    if category_id in categories:
        return category(request, category_id)

    try:
        tag_obj = Tag.objects.get(pk=category_id)
        return redirect("hop_flavor_detail", flavor_id=tag_obj.id, permanent=True)
    except Tag.DoesNotExist:
        pass

    raise Http404("Unknown hop category %s." % category)


def category(request: HttpRequest, category_id: str) -> HttpResponse:
    categories = Hop.get_categories()
    hops_query = Hop.objects.filter(use=category_id, recipes_count__gt=0)

    hops = hops_query.order_by("name")
    most_popular = hops_query.order_by("-recipes_count")[:5]
    category_name = categories[category_id]

    meta = HopOverviewMeta((category_id, category_name)).get_meta()
    context = {"category_name": category_name, "hops": hops, "most_popular": most_popular, "meta": meta}

    return render(request, "hop/category.html", context)


def flavor_overview(request: HttpRequest) -> HttpResponse:
    meta = HopFlavorOverviewMeta().get_meta()
    context = {"meta": meta, "categories": get_hop_flavor_categories()}
    return render(request, "hop/flavor_overview.html", context)


def get_hop_flavor_categories():
    available_categories = {
        'fruity': {"name": "Fruity", "tags": []},
        'citrus': {"name": "Citrus", "tags": []},
        'tropical': {"name": "Tropical", "tags": []},
        'floral': {"name": "Floral", "tags": []},
        'earthy-woody': {"name": "Earthy & Woody", "tags": []},
        'herbal': {"name": "Herbal", "tags": []},
        'spicy': {"name": "Spicy", "tags": []},
        'cream-caramel': {"name": "Creamy & Caramel", "tags": []},
        'vegetal': {"name": "Vegetal", "tags": []},
        'other': {"name": "General Descriptors", "tags": []},
    }
    tags = Tag.objects.order_by("name")
    for tag in tags:
        if tag.accessible_hops_count >= 1:
            assigned_category = (tag.category if tag.category in available_categories else "other")
            available_categories[assigned_category]["tags"].append(tag)
    categories = []
    for category_id, category in available_categories.items():
        if len(category["tags"]) > 0:

            description_template = "hop/descriptions/flavor-category/%s.html" % category_id
            if not template_exists(description_template):
                description_template = None

            category["id"] = category_id
            category["description"] = description_template
            categories.append(category)

    return categories


def flavor_detail(request: HttpRequest, flavor_id: str) -> HttpResponse:
    tag_obj = get_object_or_404(Tag, pk=flavor_id.lower())

    if flavor_id != tag_obj.id:
        return redirect("hop_flavor_detail", flavor_id=tag_obj.id, permanent=True)

    hops_query = Hop.objects.filter(aroma_tags=tag_obj, recipes_count__gt=0)
    num_hops = hops_query.count()
    if num_hops <= 0:
        raise Http404("Flavor doesn't have any data.")

    hops = hops_query.order_by("name")
    meta = HopFlavorMeta(tag_obj).get_meta()
    associated_aroma_tags = HopFlavorAnalysis().get_associated_flavors(tag_obj)

    long_description_template = "hop/descriptions/flavors/%s.html" % tag_obj.id
    try:
        loader.get_template(long_description_template)
    except TemplateDoesNotExist:
        long_description_template = None

    context = {
        "tag_name": tag_obj.name,
        "num_hops": num_hops,
        "hops": hops,
        "meta": meta,
        "associated_aroma_tags": associated_aroma_tags,
        "long_description": long_description_template,
    }
    return render(request, "hop/flavor.html", context)


def detail(request: HttpRequest, slug: str, category_id: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=slug.lower())

    if hop.recipes_count is None or hop.recipes_count <= 0:
        raise Http404("Hop doesn't have any data.")

    if category_id != hop.category or slug != hop.id:
        return redirect("hop_detail", category_id=hop.category, slug=hop.id, permanent=True)

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

    long_description_template = "hop/descriptions/hops/%s.html" % hop.id
    try:
        loader.get_template(long_description_template)
    except TemplateDoesNotExist:
        long_description_template = None

    context = {"hop": hop, "description": meta_provider.get_description_html(), "long_description": long_description_template, "meta": meta}

    return render(request, "hop/detail.html", context)


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
            return HttpResponse(status=204)
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
    return render_recipes_list(recipes_list)
