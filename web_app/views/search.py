from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from recipe_db.models import Recipe, Hop, Style
from recipe_db.search.elasticsearch import execute_search
from web_app.meta import SearchMeta
from web_app.views.utils import conditional_cache_page


def search_cache_condition(request: HttpRequest) -> bool:
    print(request.GET)
    print(len(request.GET))
    return len(request.GET) == 0


@conditional_cache_page(60*60, condition=search_cache_condition)
def search(request: HttpRequest) -> HttpResponse:
    search_result = None
    search_term = str(request.GET['term']).strip() if "term" in request.GET and len(str(request.GET['term']).strip()) > 0 else None
    search_hops = str(request.GET['hops']) if "hops" in request.GET and len(str(request.GET['hops']).strip()) > 0 else None
    search_styles = str(request.GET['styles']) if "styles" in request.GET and len(str(request.GET['styles']).strip()) > 0 else None

    if search_term is not None or search_hops is not None or search_styles is not None:
        search_result = execute_search(search_term, search_hops, search_styles)

    meta = SearchMeta(search_term).get_meta()
    context = {
        "hops": Hop.objects.filter(recipes_count__gt=0).order_by("name"),
        "style_categories": Style.objects.filter(parent_style=None).order_by("name"),
        "search_hop": search_hops,
        "search_style": search_styles,
        "search_term": search_term or "",
        "num_recipes": Recipe.objects.count(),
        "meta": meta,
        "result": search_result
    }
    return render(request, "search.html", context)
