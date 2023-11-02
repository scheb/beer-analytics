from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.fermentable import UnmappedFermentablesAnalysis
from recipe_db.analytics.hop import UnmappedHopsAnalysis
from recipe_db.analytics.yeast import UnmappedYeastsAnalysis
from recipe_db.models import Hop, Tag, Yeast, Fermentable, IgnoredHop
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.admin import AdminChartFactory
from web_app.charts.utils import NoDataException
from web_app.views.utils import render_chart, template_exists


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def overview(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/overview.html", {})


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


def hops(request: HttpRequest) -> HttpResponse:
    if "ignore" in request.GET:
        ignored = IgnoredHop()
        ignored.name = str(request.GET["ignore"]).lower()
        ignored.save()
        return redirect(reverse("admin_hops"))

    unmapped_hops = UnmappedHopsAnalysis().get_unmapped()
    context = {
        "unmapped_hops": unmapped_hops,
    }

    return render(request, "admin/hops.html", context)


def yeasts(request: HttpRequest) -> HttpResponse:
    unmapped_yeasts = UnmappedYeastsAnalysis().get_unmapped()
    context = {
        "unmapped_yeasts": unmapped_yeasts,
    }

    return render(request, "admin/yeasts.html", context)


def fermentables(request: HttpRequest) -> HttpResponse:
    unmapped_fermentables = UnmappedFermentablesAnalysis().get_unmapped()
    context = {
        "unmapped_fermentables": unmapped_fermentables,
    }

    return render(request, "admin/fermentables.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def descriptions(request: HttpRequest) -> HttpResponse:
    hop_descriptions = []
    flavor_descriptions = []
    yeast_descriptions = []
    fermentable_descriptions = []

    for hop in Hop.objects.all().order_by('-recipes_count'):
        if not template_exists("hop/descriptions/hops/%s.html" % hop.id):
            hop_descriptions.append({
                'hop': hop,
                'recipes_count': hop.recipes_count,
            })

    for flavor in Tag.objects.all().order_by('name'):
        if not template_exists("hop/descriptions/flavors/%s.html" % flavor.id):
            flavor_descriptions.append({
                'name': flavor.name,
                'hops_count': flavor.accessible_hops_count,
            })

    for yeast in Yeast.objects.all().order_by('-recipes_count'):
        if not template_exists("yeast/descriptions/yeasts/%s.html" % yeast.id):
            yeast_descriptions.append({
                'yeast': yeast,
                'recipes_count': yeast.recipes_count,
            })

    for fermentable in Fermentable.objects.all().order_by('-recipes_count'):
        if not template_exists("fermentable/descriptions/fermentables/%s.html" % fermentable.id):
            fermentable_descriptions.append({
                'fermentable': fermentable,
                'recipes_count': fermentable.recipes_count,
            })

    context = {
        'hops': hop_descriptions,
        'flavors': sorted(flavor_descriptions, key=lambda f: f['hops_count'], reverse=True),
        'yeasts': yeast_descriptions,
        'fermentables': fermentable_descriptions,
    }

    return render(request, "admin/descriptions.html", context)
