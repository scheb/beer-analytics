import itertools
from typing import List, Optional, Tuple

from recipe_db.models import Style, Yeast, Hop, Fermentable


# Holds all filter criteria (SQL WHERE statement) and parameters
class Filter:
    def __init__(self, filters: List[Tuple[str, list]]) -> None:
        self.filters = filters

    def has_filter(self):
        return len(self.filters) > 0

    @property
    def where(self) -> str:
        if len(self.filters) == 0:
            return " AND 1"
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

    def get_style_ids(self) -> List[str]:
        return list(map(lambda s: s.id if isinstance(s, Style) else s, self.styles))

    def get_style_filter(self) -> Tuple[str, list]:
        return in_filter('ras.style_id', self.get_style_ids())


class HopCriteriaMixin:
    @property
    def hops(self) -> List[Hop]:
        return self._hops

    @hops.setter
    def hops(self, hops: List[Hop]) -> None:
        self._hops = hops

    def get_hop_filter(self):
        hop_ids = list(map(lambda y: y.id, self._hops))
        return in_filter('rh.kind_id', hop_ids)


class FermentableCriteriaMixin:
    @property
    def fermentables(self) -> List[Fermentable]:
        return self._fermentables

    @fermentables.setter
    def fermentables(self, fermentables: List[Fermentable]) -> None:
        self._fermentables = fermentables

    def get_fermentable_filter(self):
        fermentable_ids = list(map(lambda y: y.id, self._fermentables))
        return in_filter('rf.kind_id', fermentable_ids)


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

        self.hop_scope: Optional[HopScope] = None
        self.fermentable_scope: Optional[FermentableScope] = None
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

        if self.hop_scope is not None:
            hop_filter = self.hop_scope.get_filter()
            if hop_filter.has_filter():
                (query_string, parameters) = hop_filter.combine()
                query_string = 'r.uid IN (SELECT DISTINCT rh.recipe_id FROM recipe_db_recipehop AS rh WHERE 1{})'.format(query_string)
                filters.append((query_string, parameters))

        if self.fermentable_scope is not None:
            fermentable_filter = self.fermentable_scope.get_filter()
            if fermentable_filter.has_filter():
                (query_string, parameters) = fermentable_filter.combine()
                query_string = 'r.uid IN (SELECT DISTINCT rf.recipe_id FROM recipe_db_recipefermentable AS rf WHERE 1{})'.format(query_string)
                filters.append((query_string, parameters))

        if self.yeast_scope is not None:
            yeast_filter = self.yeast_scope.get_filter()
            if yeast_filter.has_filter():
                (query_string, parameters) = yeast_filter.combine()
                query_string = 'r.uid IN (SELECT DISTINCT ry.recipe_id FROM recipe_db_recipeyeast AS ry WHERE 1{})'.format(query_string)
                filters.append((query_string, parameters))

        return Filter(filters)


class HopScope(HopCriteriaMixin):
    def __init__(self) -> None:
        self._hops = []

    def get_filter(self) -> Filter:
        filters = []

        if len(self.hops) > 0:
            filters.append(self.get_hop_filter())

        return Filter(filters)


class FermentableScope(FermentableCriteriaMixin):
    def __init__(self) -> None:
        self._fermentables = []

    def get_filter(self) -> Filter:
        filters = []

        if len(self.fermentables) > 0:
            filters.append(self.get_fermentable_filter())

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


class HopProjection(HopCriteriaMixin):
    def __init__(self) -> None:
        self._hops = []
        self.uses = []

    def get_filter(self) -> Filter:
        filters = []

        if len(self.hops) > 0:
            filters.append(self.get_hop_filter())

        if len(self.uses) > 0:
            filters.append(in_filter('rh.use', self.uses))

        return Filter(filters)


class FermentableProjection(FermentableCriteriaMixin):
    def __init__(self) -> None:
        self._fermentables = []
        self.categories = []
        self.types = []

    def get_filter(self) -> Filter:
        filters = []

        if len(self.fermentables) > 0:
            filters.append(self.get_fermentable_filter())

        if len(self.categories) > 0:
            (query_string, parameters) = in_filter('f.category', self.categories)
            query_string = 'rf.kind_id IN (SELECT f.id FROM recipe_db_fermentable AS f WHERE {})'.format(query_string)
            filters.append((query_string, parameters))

        if len(self.types) > 0:
            (query_string, parameters) = in_filter('f.type', self.types)
            query_string = 'rf.kind_id IN (SELECT f.id FROM recipe_db_fermentable AS f WHERE {})'.format(query_string)
            filters.append((query_string, parameters))

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
