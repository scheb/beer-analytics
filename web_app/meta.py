import abc
import html
import re
from functools import lru_cache
from typing import List, Iterable, Optional

from meta.views import Meta

from recipe_db.models import Hop, Yeast, Fermentable, Style

OPEN_GRAPH_IMAGE_WIDTH = 1200
OPEN_GRAPH_IMAGE_HEIGHT = 630
DETAIL_PAGE_TITLE = "{} ‹ {} | Beer-Analytics"
NORMAL_TITLE = "{} | Beer-Analytics"
META_DEFAULT_DESCRIPTION = 'Beer Analytics is a database of brewing recipes dedicated to beer enthusiasts, who want ' \
   'to learn how certain beer styles are composed and how ingredients are used.'


class PageMeta:
    @abc.abstractmethod
    def get_meta(self) -> Meta:
        raise NotImplementedError

    @classmethod
    def create(cls, title: str, description: Optional[str] = None, keywords: Optional[List[str]] = None):
        return Meta(
            title=NORMAL_TITLE.format(title),
            description=description or META_DEFAULT_DESCRIPTION,
            keywords=[] if keywords is None else keywords,
        )


class StyleOverviewMeta(PageMeta):
    def get_meta(self) -> Meta:
        return Meta(
            title=NORMAL_TITLE.format('Beer Styles'),
            description='Overview of all beer styles which can be analyzed on Beer Analytics.',
            keywords=['styles'],
        )


class StyleMeta(PageMeta):
    def __init__(self, style: Style) -> None:
        self.style = style

    def get_title(self):
        return DETAIL_PAGE_TITLE.format(self.style.name, 'Beer Styles')

    def get_description(self) -> str:
        return "Data analysis how the {} beer style is brewed. ".format(self.style.name)

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=[self.style.name.lower(), 'style'],
        )


class HopOverviewMeta(PageMeta):
    def __init__(self, category_name: Optional[str] = None) -> None:
        self.category_name = category_name+" " if category_name is not None else ''

    def get_title(self):
        return NORMAL_TITLE.format(self.category_name+"Hops Overview")

    def get_description(self):
        if self.category_name is not None:
            return 'Overview of {}hops which can be analyzed on Beer Analytics.'.format(
                self.category_name.lower()
            )

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=['hops'],
        )


class HopMeta(PageMeta):
    def __init__(self, hop: Hop) -> None:
        self.hop = hop

    def get_title(self):
        return DETAIL_PAGE_TITLE.format(self.hop.name, self.hop.category_name+" Hops")

    def get_description(self) -> str:
        return "Data analysis how {} hops are used in beer brewing recipes. ".format(self.hop.name)\
               + html2text(self.get_description_html(short=True))

    @lru_cache(maxsize=None)
    def get_description_html(self, short: bool = False) -> str:
        # Name + type
        name = em(escape(self.hop.name))
        category_name = strong(escape(self.hop.category_name.lower()))
        text = "{} is {} {} hop".format(
            name,
            article(category_name),
            category_name,
        )

        # Origin
        if self.hop.origin_tuples is not None:
            countries_verb = " grown in " if len(self.hop.origin_tuples) > 1 else "from"
            countries = comma_and(map(lambda c: country(c), self.hop.origin_tuples))
            text += " {} {}".format(
                countries_verb,
                countries,
            )

        # Alpha
        if self.hop.alpha_level is not None:
            alpha_amount = escape(self.hop.alpha_level)
            text += " with <strong>{} alpha acid</strong> around {}%".format(
                alpha_amount,
                round(self.hop.recipes_alpha_mean),
            )

        text += "."
        if short:
            return text

        # Common styles
        # TODO

        # Common range
        if self.hop.recipes_amount_percent_mean is not None:
            text += " When used in a recipe, it typically accounts for <strong>{}% of the hops</strong>.".format(
                round(self.hop.recipes_amount_percent_mean)
            )

        return text

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=html2text(self.get_description()),
            keywords=[self.hop.name.lower(), 'hop', 'dry-hopping', 'bittering', 'aroma'],
        )


class FermentableOverviewMeta(PageMeta):
    def __init__(self, category_name: Optional[str] = None) -> None:
        self.category_name = category_name+" " if category_name is not None else ''

    def get_title(self):
        return NORMAL_TITLE.format(self.category_name+"Fermentables Overview")

    def get_description(self):
        if self.category_name is not None:
            return 'Overview of {}fermentables which can be analyzed on Beer Analytics.'.format(
                self.category_name.lower()
            )

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=['malts', 'fermentables'],
        )


class FermentableMeta(PageMeta):
    def __init__(self, fermentable: Fermentable) -> None:
        self.fermentable = fermentable

    def get_title(self) -> str:
        return DETAIL_PAGE_TITLE.format(self.fermentable.name, self.fermentable.category_name+" Fermentables")

    def get_description(self) -> str:
        return "Data analysis how {} fermentables are used in beer brewing recipes. ".format(self.fermentable.name)\
               + html2text(self.get_description_html(short=True))

    def get_description_html(self, short: bool = False) -> str:
        # Name + type
        name = em(escape(self.fermentable.name))
        if self.fermentable.type is not None and self.fermentable.type != Fermentable.OTHER_MALT:
            type_name = strong(escape(self.fermentable.type_name.lower()))
        else:
            type_name = strong(escape(self.fermentable.category_name.lower()))
        text = "{} is {} {}".format(
            name,
            article(type_name),
            type_name,
        )
        if self.fermentable.color_level is not None:
            color_name = self.fermentable.color_level
            text += " with {} <strong>{} color</strong>".format(
                article(color_name),
                escape(color_name)
            )
        text += "."
        if short:
            return text

        # Common range
        if self.fermentable.recipes_amount_percent_mean is not None:
            text += " When used in a recipe, it typically accounts for <strong>{}% of the fermentables</strong>.".format(
                round(self.fermentable.recipes_amount_percent_mean)
            )

        return text

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=html2text(self.get_description()),
            keywords=[self.fermentable.name.lower(), 'fermentable', 'malt', 'mashing'],
        )


class YeastOverviewMeta(PageMeta):
    def __init__(self, type_name: Optional[str] = None) -> None:
        self.type_name = type_name + " " if type_name is not None else ''

    def get_title(self):
        return NORMAL_TITLE.format(self.type_name + "Yeasts Overview")

    def get_description(self):
        if self.type_name is not None:
            return 'Overview of {}yeasts which can be analyzed on Beer Analytics.'.format(
                self.type_name.lower()
            )

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=['yeasts'],
        )


class YeastMeta(PageMeta):
    def __init__(self, yeast: Yeast) -> None:
        self.yeast = yeast

    def get_yeast_full_name(self):
        yeast_name = self.yeast.full_name
        if self.yeast.has_extra_product_id:
            yeast_name += ' ({})'.format(self.yeast.product_id)
        return yeast_name

    def get_title(self) -> str:
        yeast_name = self.get_yeast_full_name()
        return DETAIL_PAGE_TITLE.format(yeast_name, self.yeast.type_name+" Yeasts")

    def get_description(self) -> str:
        return 'Data analysis how "{}" {} {} yeast is used in beer brewing recipes. '.format(
            self.get_yeast_full_name(),
            self.yeast.form_name.lower(),
            self.yeast.type_name.lower(),
        )

    def get_description_html(self) -> str:
        # Name + type
        name_incl_id = self.yeast.product_name
        if self.yeast.has_extra_product_id:
            name_incl_id += " ({})".format(self.yeast.product_id)
        product_name = em(escape(name_incl_id))
        lab_name = em(escape(self.yeast.lab))
        form_name = escape(self.yeast.form_name.lower())
        type_name = escape(self.yeast.type_name.lower())
        text = "{} is a <strong>{} {} yeast</strong> produced by {}".format(
            product_name,
            form_name,
            type_name,
            lab_name
        )
        text += "."

        # Fermentation properties
        fermentation = []
        if self.yeast.attenuation is not None:
            fermentation.append(" ferments with <strong>{} attenuation</strong>".format(
                escape(self.yeast.attenuation_level.lower()))
            )
        if self.yeast.flocculation is not None:
            flocculation_text = " <strong>{} flocculation</strong>".format(
                escape(self.yeast.flocculation_name.lower())
            )
            if not len(fermentation):
                flocculation_text = " ferments with" + flocculation_text
            fermentation.append(flocculation_text)
        if self.yeast.tolerance_name is not None:
            fermentation.append(" has a <strong>{} alcohol tolerance</strong>".format(
                self.yeast.tolerance_name.lower())
            )

        text += " It " + (comma_and(fermentation)) + "."
        return text

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=html2text(self.get_description()),
            keywords=[self.yeast.name.lower(), 'yeast', 'fermentation'],
        )


def em(value: str) -> str:
    return '<em>%s</em>' % value


def strong(value: str) -> str:
    return '<strong>%s</strong>' % value


def country(country_tuple: tuple) -> str:
    (code, name) = country_tuple
    return '<strong class="country-{}">{}</strong>'.format(code.lower(), escape(name))


def escape(value: str) -> str:
    return html.escape(value)


def html2text(value: str) -> str:
    return html.unescape(re.sub('<[^<]+?>', '', value))


def article(value: str) -> str:
    if value[0] in ['a', 'e', 'i', 'o', 'u']:
        return 'an'
    else:
        return 'a'


def comma_and(values: Iterable[str]) -> str:
    values = list(values)
    if len(values) <= 2:
        return " and ".join(values)
    else:
        return "{} and {}".format(", ".join(values[:-1]),  values[-1])
