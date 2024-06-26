import re
from typing import Optional

from django import template
from django.conf import settings
from django.template import Node, loader, TemplateDoesNotExist
from django.urls import reverse
from django.utils.functional import keep_lazy_text
from django.utils.html import escape
from django.utils.safestring import mark_safe

from recipe_db.formulas import celsius_to_fahrenheit
from recipe_db.models import Style, Hop, Fermentable, Yeast, Tag
from web_app.charts.fermentable import FermentableChartFactory
from web_app.charts.hop import HopChartFactory
from web_app.charts.style import StyleChartFactory
from web_app.charts.trend import TrendChartFactory, TrendPeriod
from web_app.charts.yeast import YeastChartFactory
from web_app.views.utils import object_url, get_hop_description, get_yeast_description, get_fermentable_description, \
    get_style_description, get_flavor_description

register = template.Library()

MAX_PRIORITY = 1.0
MIN_PRIORITY = 0.1
DEFAULT_PRIORITY = 0.3


@register.filter("float2percent")
def float2percent(value):
    return value * 100


@register.filter("startswith")
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter("url")
def url(item: object):
    return object_url(item)


@register.filter("hop")
def hop(id: str):
    return Hop.objects.get(pk=id)


@register.filter("fermentable")
def fermentable(id: str):
    return Fermentable.objects.get(pk=id)


@register.filter("style")
def style(id: str):
    return Style.objects.get(pk=id)


@register.filter("chart_js")
def chart_js(item: object, chart_type):
    return chart_url(item, chart_type, "json")


@register.filter("chart_image", is_safe=True)
def chart_image(item: object, chart_type):
    url = chart_url(item, chart_type, "svg")
    alt_text = escape(chart_image_alt(item, chart_type))
    return '<img src="%s" alt="%s" class="chart-image"/>' % (url, alt_text)


@register.filter("chart_image_url", is_safe=True)
def chart_image_url(item: object, chart_type):
    return chart_url(item, chart_type, "svg")


@register.filter("chart_image_alt")
def chart_image_alt(item: object, chart_type):
    if isinstance(item, TrendPeriod):
        return TrendChartFactory.get_chart(chart_type, item).get_image_alt()

    if isinstance(item, Style):
        return StyleChartFactory.get_chart(item, chart_type).get_image_alt()

    if isinstance(item, Hop):
        return HopChartFactory.get_chart(item, chart_type).get_image_alt()

    if isinstance(item, Fermentable):
        return FermentableChartFactory.get_chart(item, chart_type).get_image_alt()

    if isinstance(item, Yeast):
        return YeastChartFactory.get_chart(item, chart_type).get_image_alt()

    return None


def chart_url(item: object, chart_type: str, format: str):
    if isinstance(item, Style):
        if item.is_category:
            return reverse(
                "style_category_chart",
                kwargs={
                    "category_slug": item.category.slug,
                    "chart_type": chart_type.replace("_", "-"),
                    "format": format,
                },
            )
        else:
            return reverse(
                "style_chart",
                kwargs={
                    "category_slug": item.category.slug,
                    "slug": item.slug,
                    "chart_type": chart_type.replace("_", "-"),
                    "format": format,
                },
            )

    if isinstance(item, Hop):
        return reverse(
            "hop_chart",
            kwargs={
                "category_id": item.use,
                "slug": item.id,
                "chart_type": chart_type.replace("_", "-"),
                "format": format,
            },
        )

    if isinstance(item, Fermentable):
        return reverse(
            "fermentable_chart",
            kwargs={
                "category_id": item.category,
                "slug": item.id,
                "chart_type": chart_type.replace("_", "-"),
                "format": format,
            },
        )

    if isinstance(item, Yeast):
        return reverse(
            "yeast_chart",
            kwargs={
                "type_id": item.type,
                "slug": item.id,
                "chart_type": chart_type.replace("_", "-"),
                "format": format,
            },
        )

    return None


@register.filter("recipes")
def recipes(item: object):
    return recipes_url(item)


def recipes_url(item: object):
    if isinstance(item, Style):
        if item.is_category:
            return reverse(
                "style_category_recipes",
                kwargs={
                    "category_slug": item.category.slug,
                },
            )
        else:
            return reverse(
                "style_recipes",
                kwargs={
                    "category_slug": item.category.slug,
                    "slug": item.slug,
                },
            )

    if isinstance(item, Hop):
        return reverse(
            "hop_recipes",
            kwargs={
                "category_id": item.use,
                "slug": item.id,
            },
        )

    if isinstance(item, Fermentable):
        return reverse(
            "fermentable_recipes",
            kwargs={
                "category_id": item.category,
                "slug": item.id,
            },
        )

    if isinstance(item, Yeast):
        return reverse(
            "yeast_recipes",
            kwargs={
                "type_id": item.type,
                "slug": item.id,
            },
        )

    return None


@register.filter("priority")
def priority(item: object):
    if isinstance(item, Style):
        return get_priority(item.recipes_percentile)

    if isinstance(item, Hop):
        return get_priority(item.recipes_percentile)

    if isinstance(item, Fermentable):
        return get_priority(item.recipes_percentile)

    if isinstance(item, Yeast):
        return get_priority(item.recipes_percentile)

    return DEFAULT_PRIORITY


def get_priority(percentile: Optional[float]) -> float:
    if percentile is not None:
        return round(MIN_PRIORITY + (MAX_PRIORITY - MIN_PRIORITY) * percentile, 1)

    return DEFAULT_PRIORITY


@register.filter("description")
def get_item_description(item: object):
    if isinstance(item, Hop):
        description_template = get_hop_description(item.id)
    elif isinstance(item, Yeast):
        description_template = get_yeast_description(item.id)
    elif isinstance(item, Fermentable):
        description_template = get_fermentable_description(item.id)
    elif isinstance(item, Style):
        description_template = get_style_description(item.id)
    elif isinstance(item, Tag):
        description_template = get_flavor_description(item.id)
        print(item.id)
    else:
        return ""

    if description_template is not None:
        try:
            return loader.get_template(description_template).render({})
        except TemplateDoesNotExist:
            return ""

    return ""


@register.filter("fahrenheit")
def fahrenheit(value):
    if value is None:
        return None
    f = celsius_to_fahrenheit(value)
    return round(f * 2) / 2  # Round to .5


@register.tag
def htmllinebreaks(parser, token):
    nodelist = parser.parse(("endhtmllinebreaks",))
    parser.delete_first_token()
    return HtmlLineBreaksNode(nodelist)


class HtmlLineBreaksNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return newlines_between_tags(self.nodelist.render(context).strip())


@keep_lazy_text
def newlines_between_tags(value):
    """Return the given HTML with spaces between tags removed."""
    return re.sub(r">\s+<", ">\n<", str(value))


@register.inclusion_tag("web_analytics/tracker.html")
def web_analytics():
    return {
        "root_url": settings.__getattr__("WEB_ANALYTICS_ROOT_URL"),
        "site_id": settings.__getattr__("WEB_ANALYTICS_SITE_ID"),
        "script_name": settings.__getattr__("WEB_ANALYTICS_SCRIPT_NAME"),
        "tracker_name": settings.__getattr__("WEB_ANALYTICS_TRACKER_NAME"),
    }


@register.filter()
def highlight(text, value):
    if text is not None:
        text = str(text)
        src_str = re.compile(value, re.IGNORECASE)
        str_replaced = src_str.sub("<span style=\"background:yellow\">\g<0></span>", text)
    else:
        str_replaced = ''

    return mark_safe(str_replaced)
