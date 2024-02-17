from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from recipe_db.models import Recipe
from recipe_db.search.elasticsearch import search_by_term
from web_app.meta import SearchMeta


@cache_page(0)
def search(request: HttpRequest) -> HttpResponse:
    search_term = ""
    search_result = None
    if "term" in request.GET:
        search_term = str(request.GET['term'])
        search_result = search_by_term(search_term)

    meta = SearchMeta(search_term).get_meta()
    context = {
        "recipes": Recipe.objects.count(),
        "meta": meta,
        "search_term": search_term,
        "result": search_result
    }
    return render(request, "search.html", context)
