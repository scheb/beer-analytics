import itertools
from typing import List, Optional, Set, Tuple

from recipe_db.models import Style


def min_max_filter(field: str, min_value, max_value) -> Tuple[str, list]:
    if min_value is not None and max_value is not None:
        return "{} BETWEEN %s AND %s".format(field), [min_value, max_value]
    if min_value is not None:
        return "{} >= %s".format(field), [min_value]
    if max_value is not None:
        return "{} <= %s".format(field), [max_value]
    raise ValueError("Neither min nor max value given")


def in_filter(field: str, values):
    return "{} IN ({})".format(field, ','.join('%s' for _ in values)), values


class ScopeFilter:
    def __init__(self, filters: List[Tuple[str, list]]) -> None:
        self.filters = filters

    @property
    def where(self) -> str:
        if len(self.filters) == 0:
            return " AND TRUE"
        return " AND "+(" AND ".join(map(lambda f: f[0], self.filters)))

    @property
    def parameters(self) -> list:
        return list(itertools.chain.from_iterable(map(lambda f: f[1], self.filters)))


class RecipeScope:
    def __init__(self) -> None:
        self._style_ids: Set[str] = set()
        self.include_sub_styles: bool = True

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

    @property
    def style_ids(self):
        return self._style_ids

    @style_ids.setter
    def style_ids(self, value):
        if isinstance(value, set):
            self._style_ids = value
            return
        if isinstance(value, list):
            self._style_ids = set(value)
            return
        raise ValueError("style_ids value has to be set or list, {} given".format(type(value)))

    def get_style_ids(self) -> List[str]:
        style_ids_incl_sub_styles = set()
        style_ids = self.style_ids
        if self.include_sub_styles:
            for style_id in style_ids:
                style = Style.objects.get(pk=style_id)
                style_ids_incl_sub_styles.update(style.get_ids_including_sub_styles())
        return list(style_ids_incl_sub_styles)

    def get_filter(self) -> ScopeFilter:
        filters = []

        style_ids = self.get_style_ids()
        if len(style_ids) > 0:
            filters.append(in_filter('r.style_id', style_ids))

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

        return ScopeFilter(filters)
