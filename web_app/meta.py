import abc
import html
import re
from functools import lru_cache
from typing import List, Iterable, Optional, Tuple

from django.urls import reverse
from meta.views import Meta

from recipe_db.models import Hop, Yeast, Fermentable, Style, Tag
from web_app.views.utils import object_url

OPEN_GRAPH_IMAGE_WIDTH = 1200
OPEN_GRAPH_IMAGE_HEIGHT = 630
DETAIL_PAGE_TITLE = "{} ‹ {} | Beer Analytics"
NORMAL_TITLE = "{} | Beer Analytics"
META_DEFAULT_DESCRIPTION = (
    "Data analysis of brewing recipes for beer enthusiasts, who want to learn how certain "
    "beer types are composed and how ingredients are used."
)


class PageMeta:
    @abc.abstractmethod
    def get_meta(self) -> Meta:
        raise NotImplementedError

    @classmethod
    def create(
        cls,
        title: str,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        url: Optional[str] = None,
    ):
        return Meta(
            title=NORMAL_TITLE.format(title),
            description=description or META_DEFAULT_DESCRIPTION,
            keywords=[] if keywords is None else keywords,
            url=url,
        )


class HomeMeta(PageMeta):
    def get_meta(self) -> Meta:
        meta = self.create("", url=reverse("home"))
        meta.title = "Beer Analytics: Discover, Analyze & Optimize Brewing Recipes"
        return meta


class StyleOverviewMeta(PageMeta):
    def get_meta(self) -> Meta:
        return Meta(
            title=NORMAL_TITLE.format("List of Beer Styles"),
            description="Discover the diverse world of beer styles with our in-depth analysis. Uncover flavor profiles, brewing techniques, and trends to elevate your beer knowledge and appreciation.",
            keywords=["styles"],
            url=reverse("style_overview"),
        )


class StyleMeta(PageMeta):
    def __init__(self, style: Style) -> None:
        self.style = style

    def get_title(self):
        return NORMAL_TITLE.format("%s Beer Style - Recipes, Popularity, Yeasts & Hops" % self.style.name)

    def get_description(self) -> str:
        return "Discover the secrets of brewing {} style beers with our in-depth data analysis! Explore typical hops, fermentables, and yeasts used to craft the perfect beer.".format(self.style.name)

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=[self.style.name.lower(), "style"],
            url=object_url(self.style),
        )


class HopOverviewMeta(PageMeta):
    def __init__(self, category: Optional[Tuple[str, str]] = None) -> None:
        self.category_id = None
        self.category_name = ""
        if category is not None:
            (self.category_id, self.category_name) = category
            self.category_name += " "  # Add extra space for title/description

    def get_title(self):
        return NORMAL_TITLE.format("List of %sHops" % self.category_name)

    def get_description(self):
        return "Discover the ultimate guide to {}hops analysis. Uncover key insights into hop varieties, flavors, and profiles to enhance your brewing experience.".format(self.category_name.lower())

    def get_keywords(self):
        keywords = ["hops"]
        if self.category_id is not None:
            keywords.append(self.category_name.strip().lower())
        return keywords

    def get_url(self):
        if self.category_id is not None:
            return reverse("hop_category", kwargs={"category_id": self.category_id})
        return reverse("hop_overview")

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=self.get_keywords(),
            url=self.get_url(),
        )


class HopMeta(PageMeta):
    def __init__(self, hop: Hop) -> None:
        self.hop = hop

    def get_title(self):
        return NORMAL_TITLE.format(self.hop.name + " Hops – Pairings, Flavor, Beer Styles", self.hop.category_name + " Hops")

    def get_description(self) -> str:
        return "Discover the secrets of {} hops pairings, flavors, and popular beer styles through our in-depth data analysis. Uncover perfect hop combinations for a distinct taste and brew your best beer yet.".format(self.hop.name)

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
        origin = self.hop.origin_tuples
        if len(origin) > 0:
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
                round(self.hop.recipes_amount_percent_mean * 100)
            )

        return text

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=html2text(self.get_description()),
            keywords=[self.hop.name.lower(), "hop", "pairings", "dry-hopping", "bittering", "aroma"],
            url=object_url(self.hop),
        )


class HopFlavorOverviewMeta(PageMeta):
    def __init__(self) -> None:
        pass

    def get_title(self):
        return NORMAL_TITLE.format("Hop Flavors and Aromas")

    def get_description(self):
        return "Unlock the secrets of hop flavors with our ultimate guide. From classic to exotic varieties, explore flavor profiles and enhance your brewing game."

    def get_keywords(self):
        return ["hops", "flavors", "aromas"]

    def get_url(self):
        return reverse("hop_flavor_overview")

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=self.get_keywords(),
            url=self.get_url(),
        )


class HopFlavorMeta(PageMeta):
    def __init__(self, tag: Tag) -> None:
        self.tag = tag

    def get_title(self):
        return NORMAL_TITLE.format(self.tag.name + " Flavor Hops")

    def get_description(self) -> str:
        return "Unlock the secrets of the {} hop flavor with our ultimate guide. Explore available varieties, flavor profiles and enhance your brewing game.".format(self.tag.name)

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=html2text(self.get_description()),
            keywords=[self.tag.name.lower(), "hops", "flavors", "aromas"],
            url=object_url(self.tag),
        )


class FermentableOverviewMeta(PageMeta):
    def __init__(self, category: Optional[Tuple[str, str]] = None) -> None:
        self.category_id = None
        self.category_name = ""
        if category is not None:
            (self.category_id, self.category_name) = category
            self.category_name += " "  # Add extra space for title/description

    def get_title(self):
        return NORMAL_TITLE.format("List of %sFermentables" % self.category_name)

    def get_description(self):
        return "Discover an in-depth overview of {}fermentables used in beer brewing. Unveil insights, trends, and analysis to craft the perfect brew!".format(self.category_name.lower())

    def get_url(self):
        if self.category_id is not None:
            return reverse("fermentable_category", kwargs={"category_id": self.category_id})
        return reverse("fermentable_overview")

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=["malts", "fermentables"],
            url=self.get_url(),
        )


class FermentableMeta(PageMeta):
    def __init__(self, fermentable: Fermentable) -> None:
        self.fermentable = fermentable

    def get_title(self) -> str:
        return NORMAL_TITLE.format("%s – Beer Styles, Amount, Color" % self.fermentable.name)

    def get_description(self) -> str:
        return "Unlock the secrets of {} in beer brewing: Explore data analysis on common beer styles, amounts and color variations.".format(
            self.fermentable.name
        )

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
            text += " with <strong>{} color</strong>".format(escape(color_name))

        text += "."
        if short:
            return text

        # Common range
        if self.fermentable.recipes_amount_percent_mean is not None:
            text += (
                " When used in a recipe, it typically accounts for <strong>{}% of the fermentables</strong>.".format(
                    round(self.fermentable.recipes_amount_percent_mean * 100)
                )
            )

        return text

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=html2text(self.get_description()),
            keywords=[self.fermentable.name.lower(), "fermentable", "malt", "mashing"],
            url=object_url(self.fermentable),
        )


class YeastOverviewMeta(PageMeta):
    def __init__(self, y_type: Optional[Tuple[str, str, bool]] = None) -> None:
        self.type_id = None
        self.type_name = ""
        self.is_yeast = True
        if y_type is not None:
            (self.type_id, self.type_name, self.is_yeast) = y_type
            if self.is_yeast:
                self.type_name += " Yeast"
            self.type_name += " "  # Add extra space for title/description


    def get_title(self):
        if self.type_name is not None:
            return NORMAL_TITLE.format("List of %s for Beer Brewing" % self.type_name)

        return NORMAL_TITLE.format("List of Yeasts and Bacteria for Beer Brewing")

    def get_description(self):
        return "Discover the best {} used in brewing with our comprehensive guide! Compare flavor profiles, fermentation characteristics and performance data to elevate your brewing experience.".format(self.type_name.lower())

    def get_url(self):
        if self.type_id is not None:
            return reverse("yeast_type", kwargs={"type_id": self.type_id})
        return reverse("yeast_overview")

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=self.get_description(),
            keywords=["yeasts"],
            url=self.get_url(),
        )


class YeastMeta(PageMeta):
    def __init__(self, yeast: Yeast) -> None:
        self.yeast = yeast

    def get_yeast_full_name(self):
        yeast_name = self.yeast.full_name
        if self.yeast.has_extra_product_id:
            yeast_name += " ({})".format(self.yeast.product_id)
        return yeast_name

    def get_title(self) -> str:
        yeast_name = self.get_yeast_full_name()
        return NORMAL_TITLE.format("%s Beer Yeast – Styles, Fermentation" % yeast_name)

    def get_description(self) -> str:
        return 'Unlock the secrets of {} in brewing recipes: Explore data analysis on fermentable amounts, color variations and common beer styles'.format(
            self.get_yeast_full_name(),
            (self.yeast.form_name or "").lower(),
            (self.yeast.type_name or "").lower(),
        )

    def get_description_html(self, short: bool = False) -> str:
        # Name + type
        name_incl_id = self.yeast.product_name
        if self.yeast.has_extra_product_id:
            name_incl_id += " ({})".format(self.yeast.product_id)
        product_name = em(escape(name_incl_id))
        lab_name = em(escape(self.yeast.lab))
        form_name = escape((self.yeast.form_name or "").lower())
        type_name = escape((self.yeast.type_name or "").lower())
        text = "{} is a <strong>{} {} yeast</strong> produced by {}".format(
            product_name, form_name, type_name, lab_name
        )

        text += "."
        if short:
            return text

        # Fermentation properties
        fermentation = []
        if self.yeast.attenuation is not None:
            fermentation.append(
                " ferments with <strong>{} attenuation</strong>".format(escape(self.yeast.attenuation_level.lower()))
            )
        if self.yeast.flocculation is not None:
            flocculation_text = " <strong>{} flocculation</strong>".format(escape(self.yeast.flocculation_name.lower()))
            if not len(fermentation):
                flocculation_text = " ferments with" + flocculation_text
            fermentation.append(flocculation_text)
        if self.yeast.tolerance_name is not None:
            fermentation.append(
                " has a <strong>{} alcohol tolerance</strong>".format(self.yeast.tolerance_name.lower())
            )
        if len(fermentation) > 0:
            text += " It " + (comma_and(fermentation)) + "."

        return text

    def get_meta(self) -> Meta:
        return Meta(
            title=self.get_title(),
            description=html2text(self.get_description()),
            keywords=[self.yeast.name.lower(), "yeast", "fermentation"],
            url=object_url(self.yeast),
        )


def em(value: str) -> str:
    return "<em>%s</em>" % value


def strong(value: str) -> str:
    return "<strong>%s</strong>" % value


def country(country_tuple: tuple) -> str:
    (code, name) = country_tuple
    return '<strong class="country-{}">{}</strong>'.format(code.lower(), escape(name))


def escape(value: str) -> str:
    return html.escape(value)


def html2text(value: str) -> str:
    return html.unescape(re.sub("<[^<]+?>", "", value))


def article(value: str) -> str:
    if value[0] in ["a", "e", "i", "o", "u"]:
        return "an"
    else:
        return "a"


def comma_and(values: Iterable[str]) -> str:
    values = list(values)
    if len(values) <= 2:
        return " and ".join(values)
    else:
        return "{} and {}".format(", ".join(values[:-1]), values[-1])
