from django.http import HttpResponse, Http404

from web_app.charts.utils import Chart

FORMAT_PNG = 'png'
FORMAT_SVG = 'svg'
FORMAT_JSON = 'json'
FORMATS = [FORMAT_PNG, FORMAT_SVG, FORMAT_JSON]


def render_chart(chart: Chart, data_format: str):
    if data_format == FORMAT_PNG:
        return HttpResponse(chart.render_png(), content_type='image/png')
    elif data_format == FORMAT_SVG:
        return HttpResponse(chart.render_svg(), content_type='image/svg+xml')
    elif data_format == FORMAT_JSON:
        return HttpResponse(chart.render_json(), content_type='application/json')
    else:
        raise Http404('Unknown plotting format %s.' % data_format)
