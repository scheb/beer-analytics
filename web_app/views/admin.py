from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from recipe_db.analytics.fermentable import UnmappedFermentablesAnalysis
from recipe_db.analytics.hop import UnmappedHopsAnalysis
from recipe_db.analytics.yeast import UnmappedYeastsAnalysis
from recipe_db.models import Hop, Tag, Yeast
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.admin import AdminChartFactory
from web_app.charts.utils import NoDataException
from web_app.views.utils import render_chart, template_exists


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def start(request: HttpRequest) -> HttpResponse:
    unmapped_hops = UnmappedHopsAnalysis().get_unmapped()
    unmapped_yeasts = UnmappedYeastsAnalysis().get_unmapped()
    unmapped_fermentables = UnmappedFermentablesAnalysis().get_unmapped()

    context = {
        "unmapped_hops": unmapped_hops,
        "unmapped_yeasts": unmapped_yeasts,
        "unmapped_fermentables": unmapped_fermentables,
    }

    return render(request, "admin/overview.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def chart(request: HttpRequest, chart_type: str, format: str) -> HttpResponse:
    if AdminChartFactory.is_supported_chart(chart_type):
        try:
            chart = AdminChartFactory.plot_chart(chart_type)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404("Unknown chart type %s." % chart_type)

    return render_chart(chart, format)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def descriptions(request: HttpRequest) -> HttpResponse:
    hop_descriptions = []
    flavor_descriptions = []
    yeast_descriptions = []

    for hop in Hop.objects.all().filter(recipes_count__gt=0).order_by('-recipes_count'):
        hop_descriptions.append({
            'name': hop.name,
            'recipes_count': hop.recipes_count,
            'has_description': template_exists("hop/descriptions/hops/%s.html" % hop.id),
        })

    for flavor in Tag.objects.all().order_by('name'):
        flavor_descriptions.append({
            'name': flavor.name,
            'hops_count': flavor.accessible_hops_count,
            'has_description': template_exists("hop/descriptions/flavors/%s.html" % flavor.id),
        })

    for yeast in Yeast.objects.all().order_by('-recipes_count'):
        yeast_descriptions.append({
            'name': yeast.product_name,
            'recipes_count': yeast.recipes_count,
            'has_description': template_exists("yeast/descriptions/%s.html" % yeast.id),
        })

    context = {
        'hops': hop_descriptions,
        'flavors': sorted(flavor_descriptions, key=lambda f: f['hops_count'], reverse=True),
        'yeasts': yeast_descriptions,
    }

    return render(request, "admin/descriptions.html", context)
