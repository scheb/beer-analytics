from django.http import HttpResponse, HttpRequest, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from recipe_db.analytics.hop import HopFlavorAnalysis
from recipe_db.models import Hop, Tag
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.meta import HopFlavorOverviewMeta, HopFlavorMeta
from web_app.views.utils import get_flavor_description, get_flavor_category_description


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def overview(request: HttpRequest) -> HttpResponse:
    meta = HopFlavorOverviewMeta().get_meta()
    context = {"meta": meta, "categories": get_hop_flavor_categories()}
    return render(request, "hop_flavor/overview.html", context)


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
            description_template = get_flavor_category_description(category_id)

            category["id"] = category_id
            category["description"] = description_template
            categories.append(category)

    return categories


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def detail(request: HttpRequest, flavor_id: str) -> HttpResponse:
    tag_obj = get_object_or_404(Tag, pk=flavor_id.lower())

    if flavor_id != tag_obj.id:
        return redirect("hop_flavor_detail", flavor_id=tag_obj.id, permanent=True)

    hops_query = Hop.objects.filter(aroma_tags=tag_obj, recipes_count__gt=0)
    num_hops = hops_query.count()
    if num_hops <= 0:
        raise Http404("Flavor doesn't have any data.")

    hops = hops_query.order_by("name")
    most_popular = hops_query.order_by("-search_popularity")[:2]
    meta = HopFlavorMeta(tag_obj).get_meta()
    associated_aroma_tags = HopFlavorAnalysis().get_associated_flavors(tag_obj)
    long_description_template = get_flavor_description(tag_obj.id)

    context = {
        "tag_name": tag_obj.name,
        "tag_category": tag_obj.category,
        "num_hops": num_hops,
        "hops": hops,
        "hops_count": hops.count(),
        "most_popular": most_popular,
        "meta": meta,
        "associated_aroma_tags": associated_aroma_tags,
        "long_description": long_description_template,
    }
    return render(request, "hop_flavor/detail.html", context)


def catch_all(request: HttpRequest, flavor_id: str, subpath: str) -> HttpResponse:
    tag_obj = get_object_or_404(Tag, pk=flavor_id.lower())
    return redirect_to_hop_flavor(tag_obj)


def redirect_to_hop_flavor(tag_obj: Tag) -> HttpResponseRedirect:
    return redirect("hop_flavor_detail", flavor_id=tag_obj.id, permanent=True)
