from django.http import HttpResponse, Http404

from web_app.plot import Plot

FORMAT_PNG = 'png'
FORMAT_SVG = 'svg'
FORMAT_JSON = 'json'
FORMATS = [FORMAT_PNG, FORMAT_SVG, FORMAT_JSON]


def render_plot(plot: Plot, data_format: str):
    if data_format == FORMAT_PNG:
        return HttpResponse(plot.render_png(), content_type='image/png')
    elif data_format == FORMAT_SVG:
        return HttpResponse(plot.render_svg(), content_type='image/svg+xml')
    elif data_format == FORMAT_JSON:
        return HttpResponse(plot.render_json(), content_type='application/json')
    else:
        raise Http404('Unknown plotting format %s.' % data_format)
