from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render, redirect

from web_app.charts.trend import TrendChartFactory, TrendPeriod
from web_app.charts.utils import NoDataException
from web_app.views.utils import render_chart


def start(request: HttpRequest) -> HttpResponse:
    return redirect('trend_overview', period='recent')


def overview(request: HttpRequest, period: str) -> HttpResponse:
    try:
        trend_period = TrendPeriod.from_string(period)
    except ValueError:
        raise Http404('Unknown period %s.' % period)

    return render(request, 'trend/overview.html', {'period': trend_period})


def chart(request: HttpRequest, period: str, chart_type: str, format: str) -> HttpResponse:
    try:
        trend_period = TrendPeriod.from_string(period)
    except ValueError:
        raise Http404('Unknown period %s.' % period)

    filter_param = str(request.GET['filter']) if 'filter' in request.GET else None

    if TrendChartFactory.is_supported_chart(chart_type):
        try:
            chart = TrendChartFactory.plot_chart(chart_type, trend_period, filter_param)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, format)
