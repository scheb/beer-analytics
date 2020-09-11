from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from recipe_db.analytics import get_style_popularity
from recipe_db.models import Style
from web_app.charts import LinesChart, Plot


def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


def imprint(request: HttpRequest) -> HttpResponse:
    return render(request, 'imprint.html')


def privacy_policy(request: HttpRequest) -> HttpResponse:
    return render(request, 'privacy_policy.html')


def style_overview(request: HttpRequest) -> HttpResponse:
    categories = Style.objects.filter(parent_style=None).order_by('id')
    return render(request, 'styles/overview.html', {'categories': categories})


def style_category_detail(request: HttpRequest, *args, **kwargs):
    category_slug = kwargs['category_slug']
    style = get_object_or_404(Style, slug=category_slug)

    if not style.is_category:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return render_style(request, style)


def style_detail(request: HttpRequest, *args, **kwargs):
    slug = kwargs['slug']
    category_slug = kwargs['category_slug']
    style = get_object_or_404(Style, slug=slug)

    if style.is_category:
        return redirect('style_category_detail', category_slug=style.category.slug)
    if category_slug != style.category.slug:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return render_style(request, style)


def render_style(request: HttpRequest, style: Style) -> HttpResponse:
    return render(request, 'styles/detail.html', {
        "style": style
    })


def style_chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, pk=id)

    id_to_name = style.get_id_name_mapping_including_sub_styles()
    df = get_style_popularity(style)
    plot = LinesChart().plot(df, 'month', 'recipes', 'style', 'Month/Year', '% Recipes', category_names=id_to_name)

    if format == 'png':
        return HttpResponse(plot.render_png(), content_type='image/png')
    elif format == 'svg':
        return HttpResponse(plot.render_svg(), content_type='image/svg+xml')
    else:
        return HttpResponse(plot.render_json(), content_type='application/json')
