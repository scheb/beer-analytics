from datetime import datetime

from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page

from recipe_db.models import Hop
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.trend import TrendChartFactory, TrendPeriod
from web_app.charts.utils import NoDataException
from web_app.meta import TrendMeta, PopularHopsMeta
from web_app.views.utils import render_chart


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def start(request: HttpRequest) -> HttpResponse:
    return redirect("trend_overview", period="recent")


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def overview(request: HttpRequest, period: str) -> HttpResponse:
    try:
        trend_period = TrendPeriod.from_string(period)
    except ValueError:
        raise Http404("Unknown period %s." % period)

    meta = TrendMeta(period).get_meta()
    context = {
        "meta": meta,
        "period": trend_period,
    }

    return render(request, "trend/overview.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def chart_data(request: HttpRequest, period: str, chart_type: str) -> HttpResponse:
    return chart(request, period, chart_type, "json")


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="images")
def chart_image(request: HttpRequest, period: str, chart_type: str, format: str) -> HttpResponse:
    return chart(request, period, chart_type, format)


def chart(request: HttpRequest, period: str, chart_type: str, format: str) -> HttpResponse:
    try:
        trend_period = TrendPeriod.from_string(period)
    except ValueError:
        raise Http404("Unknown period %s." % period)

    filter_param = str(request.GET["filter"]) if "filter" in request.GET else None

    if TrendChartFactory.is_supported_chart(chart_type):
        try:
            chart = TrendChartFactory.plot_chart(chart_type, trend_period, filter_param)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404("Unknown chart type %s." % chart_type)

    return render_chart(chart, format)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def popular_hops(request: HttpRequest) -> HttpResponse:
    meta = PopularHopsMeta().get_meta()
    context = {
        "meta": meta,
        "month": datetime.now().strftime("%B %Y"),
        "most_searched_hops": Hop.objects.filter(search_popularity__gt=0).order_by('-search_popularity')[:10],
        "most_used_hops": Hop.objects.filter(recipes_count__gt=0).order_by('-recipes_count')[:10],
    }

    return render(request, "trend/popular-hops.html", context)
