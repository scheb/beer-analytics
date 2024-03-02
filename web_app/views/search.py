from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from recipe_db.models import Recipe, Hop, Style
from recipe_db.search.elasticsearch import execute_search
from web_app.meta import SearchMeta
from web_app.views.analyze import get_scope
from web_app.views.utils import conditional_cache_page


def search_cache_condition(request: HttpRequest) -> bool:
    return len(request.GET) == 0


@conditional_cache_page(60*60, condition=search_cache_condition)
def search(request: HttpRequest) -> HttpResponse:
    search_result = None

    scope = get_scope(request)
    if scope.has_filter():
        search_result = execute_search(scope)

    meta = SearchMeta(scope.search_term).get_meta()
    context = {
        "hops": Hop.objects.filter(recipes_count__gt=0).order_by("name"),
        "style_categories": Style.objects.filter(parent_style=None).order_by("name"),
        "search_hop": scope.hop_criteria.hops[0].id if scope.hop_criteria is not None and len(scope.hop_criteria.hops) > 0 else None,
        "search_style": scope.style_criteria.styles[0].id if scope.style_criteria is not None and len(scope.style_criteria.styles) > 0 else None,
        "search_term": scope.search_term or "",
        "num_recipes": Recipe.objects.count(),
        "meta": meta,
        "result": search_result
    }
    return render(request, "search.html", context)
