import itertools
from typing import List, Optional, Tuple

from recipe_db.models import Style, Yeast


# Holds all filter criteria (SQL WHERE statement) and parameters
class Filter:
    def __init__(self, filters: List[Tuple[str, list]]) -> None:
        self.filters = filters

    def has_filter(self):
        return len(self.filters) > 0

    @property
    def where(self) -> str:
        if len(self.filters) == 0:
            return " AND TRUE"
        return " AND "+(" AND ".join(map(lambda f: f[0], self.filters)))

    @property
    def parameters(self) -> list:
        return list(itertools.chain.from_iterable(map(lambda f: f[1], self.filters)))

    def combine(self):
        return [self.where, self.parameters]


class StyleCriteriaMixin:
    @property
    def styles(self) -> List[Style]:
        return self._styles

    @styles.setter
    def styles(self, styles: List[Style]) -> None:
        self._styles = styles

    def get_style_filter(self) -> Tuple[str, list]:
        style_ids = list(map(lambda s: s.id, self.styles))
        return in_filter('ras.style_id', style_ids)


class YeastCriteriaMixin:
    @property
    def yeasts(self) -> List[Yeast]:
        return self._yeasts

    @yeasts.setter
    def yeasts(self, yeasts: List[Yeast]) -> None:
        self._yeasts = yeasts

    def get_yeast_filter(self):
        yeast_ids = list(map(lambda y: y.id, self._yeasts))
        return in_filter('ry.kind_id', yeast_ids)


# The scope defines which recipes should be analyzed. The set of these recipes equals 100%.
class RecipeScope(StyleCriteriaMixin):
    def __init__(self) -> None:
        self._styles = []

        self.creation_date_min = None
        self.creation_date_max = None

        self.abv_min: Optional[float] = None
        self.abv_max: Optional[float] = None

        self.ibu_min: Optional[float] = None
        self.ibu_max: Optional[float] = None

        self.srm_min: Optional[float] = None
        self.srm_max: Optional[float] = None

        self.og_min: Optional[float] = None
        self.og_max: Optional[float] = None

        self.fg_min: Optional[float] = None
        self.fg_max: Optional[float] = None

        self.yeast_scope: Optional[YeastScope] = None

    def get_filter(self) -> Filter:
        filters = []

        if len(self.styles) > 0:
            style_filter = self.get_style_filter()
            filters.append((
                'r.uid IN (SELECT DISTINCT ras.recipe_id FROM recipe_db_recipe_associated_styles AS ras WHERE {})'.format(style_filter[0]),
                style_filter[1]
            ))

        if self.creation_date_min is not None or self.creation_date_max is not None:
            filters.append(min_max_filter('r.created', self.creation_date_min, self.creation_date_max))

        if self.abv_min is not None or self.abv_max is not None:
            filters.append(min_max_filter('r.abv', self.abv_min, self.abv_max))

        if self.ibu_min is not None or self.ibu_max is not None:
            filters.append(min_max_filter('r.ibu', self.ibu_min, self.ibu_max))

        if self.srm_min is not None or self.srm_max is not None:
            filters.append(min_max_filter('r.srm', self.srm_min, self.srm_max))

        if self.og_min is not None or self.og_max is not None:
            filters.append(min_max_filter('r.og', self.og_min, self.og_max))

        if self.fg_min is not None or self.fg_max is not None:
            filters.append(min_max_filter('r.fg', self.fg_min, self.fg_max))

        if self.yeast_scope is not None:
            yeast_filter = self.yeast_scope.get_filter()
            if yeast_filter.has_filter():
                (query_string, parameters) = yeast_filter.combine()
                query_string = 'r.uid IN (SELECT DISTINCT ry.recipe_id FROM recipe_db_recipeyeast AS ry WHERE TRUE{})'.format(query_string)
                filters.append((query_string, parameters))

        return Filter(filters)


class YeastScope(YeastCriteriaMixin):
    def __init__(self) -> None:
        self._yeasts = []

    def get_filter(self) -> Filter:
        filters = []

        if len(self.yeasts) > 0:
            filters.append(self.get_yeast_filter())

        return Filter(filters)


class StyleProjection(StyleCriteriaMixin):
    def __init__(self) -> None:
        self._styles = []

    def get_filter(self) -> Filter:
        filters = []

        if len(self.styles) > 0:
            filters.append(self.get_style_filter())

        return Filter(filters)


class YeastProjection(YeastCriteriaMixin):
    def __init__(self) -> None:
        self._yeasts = []

    def get_filter(self) -> Filter:
        filters = []

        if len(self.yeasts) > 0:
            filters.append(self.get_yeast_filter())

        return Filter(filters)


def min_max_filter(field: str, min_value, max_value) -> Tuple[str, list]:
    if min_value is not None and max_value is not None:
        return "{} BETWEEN %s AND %s".format(field), [min_value, max_value]
    if min_value is not None:
        return "{} >= %s".format(field), [min_value]
    if max_value is not None:
        return "{} <= %s".format(field), [max_value]
    raise ValueError("Neither min nor max value given")


def in_filter(field: str, values) -> Tuple[str, list]:
    return "{} IN ({})".format(field, ','.join('%s' for _ in values)), values
