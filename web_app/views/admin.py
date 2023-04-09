from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render

from recipe_db.analytics.fermentable import UnmappedFermentablesAnalysis
from recipe_db.analytics.hop import UnmappedHopsAnalysis
from recipe_db.analytics.yeast import UnmappedYeastsAnalysis
from web_app.charts.admin import AdminChartFactory
from web_app.charts.utils import NoDataException
from web_app.views.utils import render_chart


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


def chart(chart_type: str, format: str) -> HttpResponse:
    if AdminChartFactory.is_supported_chart(chart_type):
        try:
            chart = AdminChartFactory.plot_chart(chart_type)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404("Unknown chart type %s." % chart_type)

    return render_chart(chart, format)