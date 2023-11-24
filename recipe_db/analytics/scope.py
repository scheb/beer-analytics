from __future__ import annotations

import abc
import itertools
from typing import List, Optional

from recipe_db.models import Style, Yeast, Hop, Fermentable

class FilterInterface:
    @abc.abstractmethod
    def has_filter(self):
        pass

    @property
    @abc.abstractmethod
    def where_statement(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def where_parameters(self) -> list:
        pass

    @property
    @abc.abstractmethod
    def join_statement(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def join_parameters(self) -> list:
        pass

class AbstractFilter(FilterInterface):
    def __init__(self) -> None:
        self._where_statement = ''
        self._where_parameters = []
        self._join_statement = ''
        self._join_parameters = []

    def has_filter(self):
        return self._where_statement != '' or self._join_statement != ''

    @property
    def where_statement(self) -> str:
        return self._where_statement

    @property
    def where_parameters(self) -> list:
        return self._where_parameters

    @property
    def join_statement(self) -> str:
        return self._join_statement

    @property
    def join_parameters(self) -> list:
        return self._join_parameters


class NoFilterCriteria(AbstractFilter):
    pass


class WhereFilterCriteria(AbstractFilter):
    def __init__(self, where_statement: str, where_parameters: list) -> None:
        super().__init__()
        self._where_statement = where_statement
        self._where_parameters = where_parameters

    def has_filter(self):
        return True

    @classmethod
    def min_max_filter(cls, field: str, min_value, max_value) -> WhereFilterCriteria:
        if min_value is not None and max_value is not None:
            return WhereFilterCriteria("{} BETWEEN %s AND %s".format(field), [min_value, max_value])
        if min_value is not None:
            return WhereFilterCriteria("{} >= %s".format(field), [min_value])
        if max_value is not None:
            return WhereFilterCriteria("{} <= %s".format(field), [max_value])
        raise ValueError("Neither min nor max value given")

    @classmethod
    def in_filter(cls, field: str, values) -> WhereFilterCriteria:
        return WhereFilterCriteria("{} IN ({})".format(field, ",".join("%s" for _ in values)), values)


class JoinFilterCriteria(AbstractFilter):
    def __init__(self, join_statement: str, join_parameters: list) -> None:
        super().__init__()
        self._join_statement = join_statement
        self._join_parameters = join_parameters

    def has_filter(self):
        return True


# Holds all filter criteria (SQL JOIN and WHERE statements) and their respective parameters
class CombinedFilter(FilterInterface):
    def __init__(self) -> None:
        self.filters: List[FilterInterface] = []

    def append(self, filter: FilterInterface):
        if filter.has_filter():  # Do not add empty filters
            self.filters.append(filter)

    def has_filter(self):
        return len(self.filters) > 0

    @property
    def where_statement(self) -> str:
        if len(self.filters) == 0:
            return ""  # No filters at all

        statements = list(map(lambda f: f.where_statement, filter(lambda f: f.where_statement != '', self.filters)))
        if len(statements) == 0:
            return ""  # No where filters

        # Combine all where statements
        return " AND " + (" AND ".join(statements))

    @property
    def where_parameters(self) -> list:
        # Collect all where parameters
        return list(itertools.chain.from_iterable(map(lambda f: f.where_parameters, self.filters)))

    @property
    def join_statement(self) -> str:
        if len(self.filters) == 0:
            return ""  # No filters at all

        statements = list(map(lambda f: f.join_statement, filter(lambda f: f.join_statement != '', self.filters)))
        if len(statements) == 0:
            return ""  # No join filters

        # Combine all join statements
        return "JOIN " + ("\nJOIN ".join(statements))

    @property
    def join_parameters(self) -> list:
        # Collect all join parameters
        return list(itertools.chain.from_iterable(map(lambda f: f.join_parameters, self.filters)))


class StyleCriteriaMixin:
    @property
    def styles(self) -> List[Style]:
        return self._styles

    @styles.setter
    def styles(self, styles: List[Style]) -> None:
        self._styles = styles

    def get_style_ids(self) -> List[str]:
        ids = set()
        for style in self._styles:
            # Categories cannot be filtered directly, instead use the contained styles
            if style.is_category:
                sub_styles = list(style.style_set.all())
                ids.update(list(map(lambda s: s.id, sub_styles)))
            else:
                ids.add(style.id)
        return list(ids)

    def get_style_filter(self) -> WhereFilterCriteria:
        return WhereFilterCriteria.in_filter("ras.style_id", self.get_style_ids())


class HopCriteriaMixin:
    @property
    def hops(self) -> List[Hop]:
        return self._hops

    @hops.setter
    def hops(self, hops: List[Hop]) -> None:
        self._hops = hops

    def get_hop_filter(self) -> WhereFilterCriteria:
        hop_ids = list(map(lambda y: y.id, self._hops))
        return WhereFilterCriteria.in_filter("rh.kind_id", hop_ids)


class FermentableCriteriaMixin:
    @property
    def fermentables(self) -> List[Fermentable]:
        return self._fermentables

    @fermentables.setter
    def fermentables(self, fermentables: List[Fermentable]) -> None:
        self._fermentables = fermentables

    def get_fermentable_filter(self) -> WhereFilterCriteria:
        fermentable_ids = list(map(lambda y: y.id, self._fermentables))
        return WhereFilterCriteria.in_filter("rf.kind_id", fermentable_ids)


class YeastCriteriaMixin:
    @property
    def yeasts(self) -> List[Yeast]:
        return self._yeasts

    @yeasts.setter
    def yeasts(self, yeasts: List[Yeast]) -> None:
        self._yeasts = yeasts

    def get_yeast_filter(self) -> WhereFilterCriteria:
        yeast_ids = list(map(lambda y: y.id, self._yeasts))
        return WhereFilterCriteria.in_filter("ry.kind_id", yeast_ids)


################### ANALYSIS SCOPES
################### The scope defines which recipes should be analyzed. The set of these recipes equals 100%.

# Analyze recipes
class RecipeScope:
    class StyleCriteria:
        def __init__(self):
            self.styles: List[Style] = []

        def get_filter(self) -> FilterInterface:
            if len(self.styles) <= 0:
                return NoFilterCriteria()

            style_ids = list(map(lambda y: y.id, self.styles))
            if len(style_ids) > 1:
                # This approach avoids duplicating recipes through the join
                style_filter = WhereFilterCriteria.in_filter("style_id", style_ids)
                return JoinFilterCriteria(
                    "(SELECT DISTINCT recipe_id FROM recipe_db_recipe_associated_styles WHERE %s) AS ras ON ras.recipe_id = r.uid" % style_filter.where_statement,
                    style_filter.where_parameters
                )
            else:
                style_filter = WhereFilterCriteria.in_filter("rah.style_id", style_ids)
                return JoinFilterCriteria(
                    "recipe_db_recipe_associated_styles AS rah ON rah.recipe_id = r.uid AND %s" % style_filter.where_statement,
                    style_filter.where_parameters
                )


    class HopCriteria:
        def __init__(self):
            self.hops: List[Hop] = []

        def get_filter(self) -> FilterInterface:
            if len(self.hops) <= 0:
                return NoFilterCriteria()

            if len(self.hops) > 1:
                raise Exception("Filtering recipes by multiple hops is currently not supported")

            hop_ids = list(map(lambda y: y.id, self.hops))
            hop_filter = WhereFilterCriteria.in_filter("rah.hop_id", hop_ids)
            return JoinFilterCriteria(
                "recipe_db_recipe_associated_hops AS rah ON rah.recipe_id = r.uid AND %s" % hop_filter.where_statement,
                hop_filter.where_parameters
            )

    class FermentableCriteria:
        def __init__(self):
            self.fermentables: List[Fermentable] = []

        def get_filter(self) -> FilterInterface:
            if len(self.fermentables) <= 0:
                return NoFilterCriteria()

            if len(self.fermentables) > 1:
                raise Exception("Filtering recipes by multiple fermentables is currently not supported")

            fermentable_ids = list(map(lambda y: y.id, self.fermentables))
            fermentable_filter = WhereFilterCriteria.in_filter("raf.fermentable_id", fermentable_ids)
            return JoinFilterCriteria(
                "recipe_db_recipe_associated_fermentables AS raf ON raf.recipe_id = r.uid AND %s" % fermentable_filter.where_statement,
                fermentable_filter.where_parameters
            )

    class YeastCriteria:
        def __init__(self):
            self.yeasts: List[Yeast] = []

        def get_filter(self) -> FilterInterface:
            if len(self.yeasts) <= 0:
                return NoFilterCriteria()

            if len(self.yeasts) > 1:
                raise Exception("Filtering recipes by multiple yeasts is currently not supported")

            yeast_ids = list(map(lambda y: y.id, self.yeasts))
            yeast_filter = WhereFilterCriteria.in_filter("raf.yeast_id", yeast_ids)
            return JoinFilterCriteria(
                "recipe_db_recipe_associated_yeasts AS ray ON ray.recipe_id = r.uid AND %s" % yeast_filter.where_statement,
                yeast_filter.where_parameters
            )

    def __init__(self) -> None:
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

        # Criteria based on related entities
        self.style_criteria = RecipeScope.StyleCriteria()
        self.hop_criteria = RecipeScope.HopCriteria()
        self.fermentable_criteria = RecipeScope.FermentableCriteria()
        self.yeast_criteria = RecipeScope.YeastCriteria()


    def get_filter(self) -> FilterInterface:
        filters = CombinedFilter()

        if self.creation_date_min is not None or self.creation_date_max is not None:
            filters.append(WhereFilterCriteria.min_max_filter("r.created", self.creation_date_min, self.creation_date_max))

        if self.abv_min is not None or self.abv_max is not None:
            filters.append(WhereFilterCriteria.min_max_filter("r.abv", self.abv_min, self.abv_max))

        if self.ibu_min is not None or self.ibu_max is not None:
            filters.append(WhereFilterCriteria.min_max_filter("r.ibu", self.ibu_min, self.ibu_max))

        if self.srm_min is not None or self.srm_max is not None:
            filters.append(WhereFilterCriteria.min_max_filter("r.srm", self.srm_min, self.srm_max))

        if self.og_min is not None or self.og_max is not None:
            filters.append(WhereFilterCriteria.min_max_filter("r.og", self.og_min, self.og_max))

        if self.fg_min is not None or self.fg_max is not None:
            filters.append(WhereFilterCriteria.min_max_filter("r.fg", self.fg_min, self.fg_max))

        # Add filters on related entities
        if self.style_criteria is not None:
            filters.append(self.style_criteria.get_filter())
        if self.fermentable_criteria is not None:
            filters.append(self.fermentable_criteria.get_filter())
        if self.hop_criteria is not None:
            filters.append(self.hop_criteria.get_filter())
        if self.yeast_criteria is not None:
            filters.append(self.yeast_criteria.get_filter())

        return filters


# Analyze hops only
class HopScope(HopCriteriaMixin):
    def __init__(self) -> None:
        self._hops = []

    def get_filter(self) -> CombinedFilter:
        filters = CombinedFilter()

        if len(self.hops) > 0:
            filters.append(self.get_hop_filter())

        return filters


# Analyze fermentables only
class FermentableScope(FermentableCriteriaMixin):
    def __init__(self) -> None:
        self._fermentables = []

    def get_filter(self) -> CombinedFilter:
        filters = CombinedFilter()

        if len(self.fermentables) > 0:
            filters.append(self.get_fermentable_filter())

        return filters


# Analyze yeasts only
class YeastScope(YeastCriteriaMixin):
    def __init__(self) -> None:
        self._yeasts = []

    def get_filter(self) -> CombinedFilter:
        filters = CombinedFilter()

        if len(self.yeasts) > 0:
            filters.append(self.get_yeast_filter())

        return filters


################### SELECTION FILTERS
################### Limit the analysis to specific items

# Narrow down the analysis to specific styles
class StyleSelection(StyleCriteriaMixin):
    def __init__(self) -> None:
        self._styles = []

    def get_filter(self) -> CombinedFilter:
        filters = CombinedFilter()

        if len(self.styles) > 0:
            filters.append(self.get_style_filter())

        return filters


# Narrow down the analysis to specific hops
class HopSelection(HopCriteriaMixin):
    def __init__(self) -> None:
        self._hops = []
        self.uses = []

    def get_filter(self) -> CombinedFilter:
        filters = CombinedFilter()

        if len(self.hops) > 0:
            filters.append(self.get_hop_filter())

        if len(self.uses) > 0:
            filters.append(WhereFilterCriteria.in_filter("rh.use", self.uses))

        return filters


# Narrow down the analysis to specific fermentables
class FermentableSelection(FermentableCriteriaMixin):
    def __init__(self) -> None:
        self._fermentables = []
        self.categories = []
        self.types = []

    def get_filter(self) -> CombinedFilter:
        filters = CombinedFilter()

        if len(self.fermentables) > 0:
            filters.append(self.get_fermentable_filter())

        if len(self.categories) > 0:
            in_filter = WhereFilterCriteria.in_filter("f.category", self.categories)
            where_statement = "rf.kind_id IN (SELECT f.id FROM recipe_db_fermentable AS f WHERE {})".format(in_filter.where_statement)
            filters.append(WhereFilterCriteria(where_statement, in_filter.where_parameters))

        if len(self.types) > 0:
            in_filter = WhereFilterCriteria.in_filter("f.type", self.types)
            where_statement = "rf.kind_id IN (SELECT f.id FROM recipe_db_fermentable AS f WHERE {})".format(in_filter.where_statement)
            filters.append(WhereFilterCriteria(where_statement, in_filter.where_parameters))

        return filters


# Narrow down the analysis to specific yeasts
class YeastSelection(YeastCriteriaMixin):
    def __init__(self) -> None:
        self._yeasts = []
        self.types = []

    def get_filter(self) -> CombinedFilter:
        filters = CombinedFilter()

        if len(self.yeasts) > 0:
            filters.append(self.get_yeast_filter())

        if len(self.types) > 0:
            in_filter = WhereFilterCriteria.in_filter("y.type", self.types)
            where_statement = "ry.kind_id IN (SELECT y.id FROM recipe_db_yeast AS y WHERE {})".format(in_filter.where_statement)
            filters.append(WhereFilterCriteria(where_statement, in_filter.where_parameters))

        return filters
