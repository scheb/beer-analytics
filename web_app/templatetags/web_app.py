from django import template
from django.urls import reverse
from django.utils.html import escape

from recipe_db.analytics import get_ranked_styles, get_ranked_hops, get_ranked_fermentables
from recipe_db.models import Style, Hop, Fermentable
from web_app.charts.fermentable import FermentableChartFactory
from web_app.charts.hop import HopChartFactory
from web_app.charts.style import StyleChartFactory

register = template.Library()

MAX_PRIORITY = 1.0
MIN_PRIORITY = 0.1
DEFAULT_PRIORITY = 0.3
STYLES_RANKED = get_ranked_styles()
HOPS_RANKED = get_ranked_hops()
FERMENTABLES_RANKED = get_ranked_fermentables()


@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter('url')
def url(item: object):
    if isinstance(item, Style):
        if item.is_category:
            return reverse('style_category', kwargs={'category_slug': item.slug})
        else:
            return reverse('style_detail', kwargs={'category_slug': item.category.slug, 'slug': item.slug})

    if isinstance(item, Hop):
        return reverse('hop_detail', kwargs={'category': item.use, 'slug': item.id})

    if isinstance(item, Fermentable):
        return reverse('fermentable_detail', kwargs={'category': item.category, 'slug': item.id})

    return None


@register.filter('chart_js')
def chart_js(item: object, chart_type):
    return chart_url(item, chart_type, 'json')


@register.filter('chart_image', is_safe=True)
def chart_image(item: object, chart_type):
    url = chart_url(item, chart_type, 'svg')
    alt_text = escape(chart_image_alt(item, chart_type))
    return '<img src="%s" alt="%s" class="chart-image"/>' % (url, alt_text)


def chart_image_alt(item: object, chart_type):
    if isinstance(item, Style):
        return StyleChartFactory.get_chart(item, chart_type).get_image_alt()

    if isinstance(item, Hop):
        return HopChartFactory.get_chart(item, chart_type).get_image_alt()

    if isinstance(item, Fermentable):
        return FermentableChartFactory.get_chart(item, chart_type).get_image_alt()

    return None


def chart_url(item: object, chart_type: str, format: str):
    if isinstance(item, Style):
        if item.is_category:
            return reverse('style_category_chart', kwargs={
                'category_slug': item.category.slug,
                'chart_type': chart_type,
                'format': format
            })
        else:
            return reverse('style_chart', kwargs={
                'category_slug': item.category.slug,
                'slug': item.slug,
                'chart_type': chart_type,
                'format': format
            })

    if isinstance(item, Hop):
        return reverse('hop_chart', kwargs={
            'category': item.use,
            'slug': item.id,
            'chart_type': chart_type,
            'format': format
        })

    if isinstance(item, Fermentable):
        return reverse('fermentable_chart', kwargs={
            'category': item.category,
            'slug': item.id,
            'chart_type': chart_type,
            'format': format
        })

    return None


@register.filter('priority')
def priority(item: object):
    if isinstance(item, Style):
        return get_priority(item.id, STYLES_RANKED)

    if isinstance(item, Hop):
        return get_priority(item.id, HOPS_RANKED)

    if isinstance(item, Fermentable):
        return get_priority(item.id, FERMENTABLES_RANKED)

    return DEFAULT_PRIORITY


def get_priority(rank_id: str, rank: dict) -> float:
    if rank_id not in rank:
        return DEFAULT_PRIORITY

    percentile = rank[rank_id]['percentile']
    return round(MIN_PRIORITY + (MAX_PRIORITY - MIN_PRIORITY) * percentile, 1)
