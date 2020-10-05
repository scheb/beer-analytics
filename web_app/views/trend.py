from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render

from web_app.charts.trend import TrendChartFactory
from web_app.charts.utils import NoDataException
from web_app.views.utils import render_chart


def overview(request: HttpRequest) -> HttpResponse:
    return render(request, 'trend/overview.html', )


def chart(request: HttpRequest, chart_type: str, format: str) -> HttpResponse:
    if TrendChartFactory.is_supported_chart(chart_type):
        try:
            chart = TrendChartFactory.plot_chart(chart_type)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, format)
