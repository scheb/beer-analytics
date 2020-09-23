from django import template

from recipe_db.analytics import get_ranked_styles, get_ranked_hops, get_ranked_fermentables
from recipe_db.models import Style, Hop, Fermentable

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


@register.filter('priority')
def priority(item: object):
    if isinstance(item, Style):
        return get_priority(item.id, STYLES_RANKED)

    if isinstance(item, Hop):
        return get_priority(item.id, HOPS_RANKED)
    #
    if isinstance(item, Fermentable):
        return get_priority(item.id, FERMENTABLES_RANKED)

    return DEFAULT_PRIORITY


def get_priority(rank_id: str, rank: dict) -> float:
    if rank_id not in rank:
        return DEFAULT_PRIORITY

    percentile = rank[rank_id]['percentile']
    return round(MIN_PRIORITY + (MAX_PRIORITY - MIN_PRIORITY) * percentile, 1)
