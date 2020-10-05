from __future__ import annotations

import codecs
import datetime
import math
import re
from collections import OrderedDict
from typing import Optional

import numpy as np
# noinspection PyUnresolvedReferences
import translitcodec
from django.core.validators import MaxValueValidator, BaseValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from recipe_db.formulas import ebc_to_srm, srm_to_ebc, plato_to_gravity, gravity_to_plato, abv_to_to_final_plato, \
    alcohol_by_volume, lovibond_to_ebc, ebc_to_lovibond, kg_to_lbs, yield_to_ppg, liters_to_gallons


class GreaterThanValueValidator(BaseValidator):
    message = _('Ensure this value is greater than %(limit_value)s (it is %(show_value)s).')
    code = 'greater_min_value'

    def compare(self, a, b):
        return a <= b


def get_tomorrow_date():
    return datetime.date.today() + datetime.timedelta(days=1)


def create_human_readable_id(value: str) -> str:
    value = codecs.encode(value, 'translit/long')
    return re.sub('[\\s\\/-]+', '-', re.sub('[^\\w\\s\\/-]', '', value)).lower()


# https://www.bjcp.org/docs/2015_Guidelines_Beer.pdf
# -> https://www.bjcp.org/docs/2015_Guidelines.xlsx
# -> https://www.bjcp.org/docs/2015_Styles.xlsx
# https://www.brewersassociation.org/edu/brewers-association-beer-style-guidelines/
# https://www.dummies.com/food-drink/drinks/beer/beer-style-guidelines-hierarchy/
class Style(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    slug = models.SlugField()
    name = models.CharField(max_length=255)
    parent_style = models.ForeignKey("self", on_delete=models.SET_NULL, default=None, blank=True, null=True)
    alt_names = models.CharField(max_length=255, default=None, blank=True, null=True)
    alt_names_extra = models.CharField(max_length=255, default=None, blank=True, null=True)

    # Metrics
    abv_min = models.FloatField(default=None, blank=True, null=True)
    abv_max = models.FloatField(default=None, blank=True, null=True)
    ibu_min = models.FloatField(default=None, blank=True, null=True)
    ibu_max = models.FloatField(default=None, blank=True, null=True)
    ebc_min = models.FloatField(default=None, blank=True, null=True)
    ebc_max = models.FloatField(default=None, blank=True, null=True)
    srm_min = models.FloatField(default=None, blank=True, null=True)
    srm_max = models.FloatField(default=None, blank=True, null=True)
    og_min = models.FloatField(default=None, blank=True, null=True)
    og_max = models.FloatField(default=None, blank=True, null=True)
    original_plato_min = models.FloatField(default=None, blank=True, null=True)
    original_plato_max = models.FloatField(default=None, blank=True, null=True)
    fg_min = models.FloatField(default=None, blank=True, null=True)
    fg_max = models.FloatField(default=None, blank=True, null=True)
    final_plato_min = models.FloatField(default=None, blank=True, null=True)
    final_plato_max = models.FloatField(default=None, blank=True, null=True)

    # Calculated metrics from recipes
    recipes_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_percentile = models.FloatField(default=None, blank=True, null=True)
    recipes_abv_min = models.FloatField(default=None, blank=True, null=True)
    recipes_abv_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_abv_max = models.FloatField(default=None, blank=True, null=True)
    recipes_ibu_min = models.FloatField(default=None, blank=True, null=True)
    recipes_ibu_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_ibu_max = models.FloatField(default=None, blank=True, null=True)
    recipes_ebc_min = models.FloatField(default=None, blank=True, null=True)
    recipes_ebc_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_ebc_max = models.FloatField(default=None, blank=True, null=True)
    recipes_srm_min = models.FloatField(default=None, blank=True, null=True)
    recipes_srm_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_srm_max = models.FloatField(default=None, blank=True, null=True)
    recipes_og_min = models.FloatField(default=None, blank=True, null=True)
    recipes_og_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_og_max = models.FloatField(default=None, blank=True, null=True)
    recipes_original_plato_min = models.FloatField(default=None, blank=True, null=True)
    recipes_original_plato_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_original_plato_max = models.FloatField(default=None, blank=True, null=True)
    recipes_fg_min = models.FloatField(default=None, blank=True, null=True)
    recipes_fg_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_fg_max = models.FloatField(default=None, blank=True, null=True)
    recipes_final_plato_min = models.FloatField(default=None, blank=True, null=True)
    recipes_final_plato_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_final_plato_max = models.FloatField(default=None, blank=True, null=True)

    # Classifications
    strength = models.CharField(max_length=255, default=None, blank=True, null=True)
    color = models.CharField(max_length=255, default=None, blank=True, null=True)
    fermentation = models.CharField(max_length=255, default=None, blank=True, null=True)
    conditioning = models.CharField(max_length=255, default=None, blank=True, null=True)
    region_of_origin = models.CharField(max_length=255, default=None, blank=True, null=True)
    family = models.CharField(max_length=255, default=None, blank=True, null=True)
    specialty_beer = models.BooleanField(default=False)
    era = models.CharField(max_length=255, default=None, blank=True, null=True)
    bitter_balances = models.CharField(max_length=255, default=None, blank=True, null=True)
    sour_hoppy_sweet = models.CharField(max_length=255, default=None, blank=True, null=True)
    spice = models.CharField(max_length=255, default=None, blank=True, null=True)
    smoke_roast = models.CharField(max_length=255, default=None, blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if self.slug == '':
            self.slug = create_human_readable_id(self.name)

        self.derive_missing_values('ebc', 'srm', ebc_to_srm)
        self.derive_missing_values('srm', 'ebc', srm_to_ebc)
        self.derive_missing_values('original_plato', 'og', plato_to_gravity)
        self.derive_missing_values('og', 'original_plato', gravity_to_plato)
        self.derive_missing_values('final_plato', 'fg', plato_to_gravity)
        self.derive_missing_values('fg', 'final_plato', gravity_to_plato)

        super().save(*args, **kwargs)

    def derive_missing_values(self, from_field: str, to_field: str, calc_function: callable) -> None:
        fields = ['{}_min', '{}_max', 'recipes_{}_min', 'recipes_{}_mean', 'recipes_{}_max']
        for pattern in fields:
            to_field_name = pattern.format(to_field)
            if getattr(self, to_field_name) is None:
                from_field_name = pattern.format(from_field)
                from_field_value = getattr(self, from_field_name)
                if from_field_value is not None:
                    setattr(self, to_field_name, calc_function(from_field_value))

    def get_style_including_sub_styles(self) -> iter:
        yield self
        for style in self.style_set.all():
            yield from style.get_style_including_sub_styles()

    def get_id_name_mapping_including_sub_styles(self) -> dict:
        return dict(map(lambda s: (s.id, s.name), self.get_style_including_sub_styles()))

    def get_ids_including_sub_styles(self) -> list:
        return list(map(lambda x: x.id, self.get_style_including_sub_styles()))

    @property
    def parent_styles(self) -> iter:
        s = self
        while s.parent_style is not None:
            yield s.parent_style
            s = s.parent_style

    @property
    def sub_styles(self) -> iter:
        return self.style_set.order_by('id')

    @property
    def has_sub_styles(self) -> bool:
        return self.style_set.count() > 0

    @property
    def is_category(self) -> bool:
        return self.parent_style is None

    @property
    def category(self) -> Style:
        if self.is_category:
            return self
        return list(self.parent_styles).pop()

    @property
    def category_slug(self) -> str:
        return self.category.slug

    @property
    def alt_names_list(self):
        if self.alt_names is not None:
            items = self.alt_names.split(',')
            return list(map(lambda x: x.strip(), items))

    @property
    def has_specified_metrics(self) -> bool:
        fields = ['abv_min', 'abv_max', 'ibu_min', 'ibu_max', 'ebc_min', 'ebc_max', 'srm_min', 'srm_max', 'og_min',
                  'og_max', 'original_plato_min', 'original_plato_max', 'fg_min', 'fg_max', 'final_plato_min',
                  'final_plato_max']
        for field in fields:
            if getattr(self, field) is not None:
                return True
        return False

    @property
    def has_recipes_metrics(self) -> bool:
        fields = ['recipes_abv_min', 'recipes_abv_mean', 'recipes_abv_max', 'recipes_ibu_min', 'recipes_ibu_mean',
                  'recipes_ibu_max', 'recipes_ebc_min', 'recipes_ebc_mean', 'recipes_ebc_max', 'recipes_srm_min',
                  'recipes_srm_mean', 'recipes_srm_max', 'recipes_og_min', 'recipes_og_mean', 'recipes_og_max',
                  'recipes_original_plato_min', 'recipes_original_plato_mean', 'recipes_original_plato_max',
                  'recipes_fg_min', 'recipes_fg_mean', 'recipes_fg_max', 'recipes_final_plato_min',
                  'recipes_final_plato_mean', 'recipes_final_plato_max']
        for field in fields:
            if getattr(self, field) is not None:
                return True
        return False

    @property
    def is_popular(self) -> bool:
        return self.recipes_percentile is not None and self.recipes_percentile > 0.8


class Fermentable(models.Model):
    # Categories
    GRAIN = "grain"
    SUGAR = "sugar"
    FRUIT = "fruit"
    EXTRACT = "extract"

    # Types
    BASE = "base"
    CARA_CRYSTAL = "cara_crystal"
    TOASTED = "toasted"
    ROASTED = "roasted"
    OTHER_MALT = "other_malt"
    ADJUNCT = "adjunct"
    UNMALTED_ADJUNCT = "unmalted_adjunct"

    CATEGORY_CHOICES = (
        (GRAIN, "Grain"),
        (SUGAR, "Sugar"),
        (FRUIT, "Fruit"),
        (EXTRACT, "Malt Extract"),
    )

    TYPE_CHOICES = (
        (BASE, "Base Malts"),
        (CARA_CRYSTAL, "Caramel/Crystal Malts"),
        (TOASTED, "Toasted"),
        (ROASTED, "Roasted"),
        (OTHER_MALT, "Other Malts"),
        (ADJUNCT, "Adjunct Malts"),
        (UNMALTED_ADJUNCT, "Unmalted Adjuncts"),
    )

    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default=None, blank=True, null=True)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=None, blank=True, null=True)
    alt_names = models.CharField(max_length=255, default=None, blank=True, null=True)
    alt_names_extra = models.CharField(max_length=255, default=None, blank=True, null=True)

    # Calculated metrics from recipes
    recipes_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_percentile = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_min = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_max = models.FloatField(default=None, blank=True, null=True)
    recipes_color_lovibond_min = models.FloatField(default=None, blank=True, null=True)
    recipes_color_lovibond_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_color_lovibond_max = models.FloatField(default=None, blank=True, null=True)
    recipes_color_ebc_min = models.FloatField(default=None, blank=True, null=True)
    recipes_color_ebc_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_color_ebc_max = models.FloatField(default=None, blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if self.id == '':
            self.id = self.create_id(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def create_id(cls, name: str) -> str:
        return create_human_readable_id(name)

    @classmethod
    def get_categories(cls) -> dict:
        return dict(cls.CATEGORY_CHOICES)

    @property
    def category_name(self) -> Optional[str]:
        if self.category is None:
            return None
        return self.get_categories()[self.category]

    @classmethod
    def get_types(cls) -> dict:
        return dict(cls.TYPE_CHOICES)

    @property
    def type_name(self) -> Optional[str]:
        if self.type is None:
            return None
        return self.get_types()[self.type]

    @property
    def alt_names_list(self):
        if self.alt_names is not None:
            items = self.alt_names.split(',')
            return list(map(lambda x: x.strip(), items))

    @property
    def is_popular(self) -> bool:
        return self.recipes_percentile is not None and self.recipes_percentile > 0.9


# http://www.hopslist.com/hops/
class Hop(models.Model):
    AROMA = 'aroma'
    BITTERING = 'bittering'
    DUAL_PURPOSE = 'dual-purpose'

    USE_CHOICES = (
        (AROMA, 'Aroma'),
        (BITTERING, 'Bittering'),
        (DUAL_PURPOSE, 'Dual Purpose'),
    )

    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    use = models.CharField(max_length=16, choices=USE_CHOICES, default=None, blank=True, null=True)
    alt_names = models.CharField(max_length=255, default=None, blank=True, null=True)
    alt_names_extra = models.CharField(max_length=255, default=None, blank=True, null=True)

    # Calculated metrics from recipes
    recipes_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_percentile = models.FloatField(default=None, blank=True, null=True)
    recipes_alpha_min = models.FloatField(default=None, blank=True, null=True)
    recipes_alpha_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_alpha_max = models.FloatField(default=None, blank=True, null=True)
    recipes_beta_min = models.FloatField(default=None, blank=True, null=True)
    recipes_beta_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_beta_max = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_min = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_max = models.FloatField(default=None, blank=True, null=True)
    recipes_use_mash_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_use_first_wort_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_use_boil_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_use_aroma_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_use_dry_hop_count = models.IntegerField(default=None, blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if self.id == '':
            self.id = self.create_id(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def create_id(cls, name: str) -> str:
        return create_human_readable_id(name)

    @classmethod
    def get_categories(cls) -> dict:
        return dict(cls.USE_CHOICES)

    @property
    def category(self) -> str:
        return self.use

    @property
    def category_name(self) -> str:
        return self.get_categories()[self.use]

    @property
    def alt_names_list(self):
        if self.alt_names is not None:
            items = self.alt_names.split(',')
            return list(map(lambda x: x.strip(), items))

    @property
    def use_count(self) -> list:
        uses = [
            RecipeHop.MASH,
            RecipeHop.FIRST_WORT,
            RecipeHop.BOIL,
            RecipeHop.AROMA,
            RecipeHop.DRY_HOP,
        ]

        use_names = RecipeHop.get_uses()
        use_counts = []
        for use in uses:
            value = getattr(self, 'recipes_use_%s_count' % use)
            if value is not None:
                use_counts.append({"use_id": use, "use": use_names[use], "recipes": value})

        return use_counts

    @property
    def is_popular(self) -> bool:
        return self.recipes_percentile is not None and self.recipes_percentile > 0.9


class Yeast(models.Model):
    ALE = "ale"
    LAGER = "lager"
    WHEAT = "wheat"
    BRETT_BACTERIA = "brett-bacteria"
    WINE_CIDER = "wine-cider"

    LIQUID = "liquid"
    DRY = "dry"
    SLANT = "slant"
    CULTURE = "culture"

    LOW = "low"
    MEDIUM_LOW = "medium-low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium-high"
    HIGH = "high"
    VERY_HIGH = "very-high"

    FORM_CHOICES = (
        (LIQUID, "Liquid"),
        (DRY, "Dry"),
        (SLANT, "Slant"),
        (CULTURE, "Culture"),
    )

    TYPE_CHOICES = (
        (ALE, "Ale"),
        (LAGER, "Lager"),
        (WHEAT, "Wheat"),
        (BRETT_BACTERIA, "Brett & Bacteria"),
        (WINE_CIDER, "Wine & Cider"),
    )

    FLOCCULATION_CHOICES = (
        (LOW, "Low"),
        (MEDIUM_LOW, "Medium-Low"),
        (MEDIUM, "Medium"),
        (MEDIUM_HIGH, "Medium-High"),
        (HIGH, "High"),
        (VERY_HIGH, "Very High"),
    )

    TOLERANCE_CHOICES = (
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
        (VERY_HIGH, "Very High"),
    )

    id = models.CharField(max_length=255, primary_key=True)
    product_id = models.CharField(max_length=16, default=None, blank=True, null=True)
    alt_product_id = models.CharField(max_length=255, default=None, blank=True, null=True)
    name = models.CharField(max_length=255)
    alt_names = models.CharField(max_length=255, default=None, blank=True, null=True)
    alt_names_extra = models.CharField(max_length=255, default=None, blank=True, null=True)
    brand = models.CharField(max_length=255, default=None, blank=True, null=True)
    alt_brand = models.CharField(max_length=255, default=None, blank=True, null=True)
    alt_brand_extra = models.CharField(max_length=255, default=None, blank=True, null=True)
    form = models.CharField(max_length=16, choices=FORM_CHOICES, default=None, blank=True, null=True)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=None, blank=True, null=True)
    attenuation = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    min_temperature = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    max_temperature = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    flocculation = models.CharField(max_length=16, choices=FLOCCULATION_CHOICES, default=None, blank=True, null=True)
    tolerance = models.CharField(max_length=16, choices=TOLERANCE_CHOICES, default=None, blank=True, null=True)
    tolerance_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])

    # Calculated metrics from recipes
    recipes_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_percentile = models.FloatField(default=None, blank=True, null=True)

    class Meta:
        unique_together = ('brand', 'product_id')

    def save(self, *args, **kwargs) -> None:
        if self.id == '':
            self.id = self.create_id(self.name, self.brand, self.product_id)
        super().save(*args, **kwargs)

    @classmethod
    def create_id(cls, name: str, brand: str, product_id: Optional[str]) -> str:
        if product_id is not None and str(product_id) not in name:
            combined = "{} {} {}".format(brand, name, product_id)
        else:
            combined = "{} {}".format(brand, name)
        return create_human_readable_id(combined)

    @classmethod
    def get_brands(cls) -> list:
        return list(cls.objects.order_by('brand').values_list('brand', flat=True).distinct())

    @classmethod
    def get_types(cls) -> dict:
        return dict(cls.TYPE_CHOICES)

    @property
    def has_product_id_included(self):
        return self.product_id is not None and self.product_id in self.name

    @property
    def full_name(self):
        full_name = "{} · {}".format(self.brand, self.name)
        if self.product_id is not None and not self.has_product_id_included:
            full_name += " ({})".format(self.product_id)
        return full_name

    @property
    def type_name(self) -> Optional[str]:
        if self.type is None:
            return None
        return self.get_types()[self.type]

    @property
    def form_name(self):
        if self.flocculation is None:
            return None
        return dict(self.FORM_CHOICES)[self.form]

    @property
    def flocculation_name(self):
        if self.flocculation is None:
            return None
        return dict(self.FLOCCULATION_CHOICES)[self.flocculation]

    @property
    def tolerance_name(self):
        if self.tolerance is None:
            return None
        return dict(self.TOLERANCE_CHOICES)[self.tolerance]

    @property
    def is_popular(self) -> bool:
        return self.recipes_percentile is not None and self.recipes_percentile > 0.9


class Recipe(models.Model):
    # Identifiers
    uid = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=255, default=None, blank=True, null=True)
    author = models.CharField(max_length=255, default=None, blank=True, null=True)
    created = models.DateField(default=None, blank=True, null=True, validators=[MinValueValidator(datetime.date(1990, 1, 1)), MaxValueValidator(get_tomorrow_date)])

    # Characteristics
    style = models.ForeignKey(Style, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    style_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    extract_efficiency = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    og = models.FloatField(default=None, blank=True, null=True, validators=[MinValueValidator(0.95), MaxValueValidator(1.5)])
    fg = models.FloatField(default=None, blank=True, null=True, validators=[MinValueValidator(0.95), MaxValueValidator(1.5)])
    original_plato = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    final_plato = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    abv = models.FloatField(default=None, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    ebc = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    srm = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    ibu = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])

    # Mashing
    mash_water = models.IntegerField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    sparge_water = models.IntegerField(default=None, blank=True, null=True, validators=[MinValueValidator(0)])

    # Boiling
    boiling_time = models.IntegerField(default=None, blank=True, null=True, validators=[MinValueValidator(0)])
    cast_out_wort = models.IntegerField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])

    def save(self, *args, **kwargs) -> None:
        self.derive_missing_values('ebc', 'srm', ebc_to_srm)
        self.derive_missing_values('srm', 'ebc', srm_to_ebc)
        self.derive_missing_values('original_plato', 'og', plato_to_gravity)
        self.derive_missing_values('og', 'original_plato', gravity_to_plato)

        # When no final plato/gravity is available, but there's original plato and abv
        if self.fg is None and self.final_plato is None and self.original_plato is not None and self.abv is not None:
            self.final_plato = abv_to_to_final_plato(self.abv, self.original_plato)

        self.derive_missing_values('final_plato', 'fg', plato_to_gravity)
        self.derive_missing_values('fg', 'final_plato', gravity_to_plato)

        # Calculate ABV when missing
        if self.abv is None and self.og is not None and self.fg is not None:
            self.abv = alcohol_by_volume(self.og, self.fg)

        super().save(*args, **kwargs)

    def derive_missing_values(self, from_field_name: str, to_field_name: str, calc_function: callable) -> None:
        if getattr(self, to_field_name) is None:
            from_field_value = getattr(self, from_field_name)
            if from_field_value is not None:
                setattr(self, to_field_name, calc_function(from_field_value))

    def __str__(self):
        return self.uid


class RecipeFermentable(models.Model):
    BOIL = 'boil'
    MASH = 'mash'
    STEEP = 'steep'

    GRAIN = 'grain'
    SUGAR = 'sugar'
    EXTRACT = 'extract'
    DRY_EXTRACT = 'dry-extract'
    ADJUNCT = 'adjunct'

    FORM_CHOICES = (
        (GRAIN, "Grain"),
        (SUGAR, "Sugar"),
        (EXTRACT, "Extract"),
        (DRY_EXTRACT, "Dry Extract"),
        (ADJUNCT, "Adjunct"),
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.ForeignKey(Fermentable, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    origin_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    form = models.CharField(max_length=16, choices=FORM_CHOICES, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    color_lovibond = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    color_ebc = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    _yield = models.FloatField(default=None, blank=True, null=True, db_column='yield', validators=[GreaterThanValueValidator(0)])
    notes = models.TextField(default=None, blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        self.derive_missing_values('color_lovibond', 'color_ebc', lovibond_to_ebc)
        self.derive_missing_values('color_ebc', 'color_lovibond', ebc_to_lovibond)

        super().save(*args, **kwargs)

    def derive_missing_values(self, from_field_name: str, to_field_name: str, calc_function: callable) -> None:
        if getattr(self, to_field_name) is None:
            from_field_value = getattr(self, from_field_name)
            if from_field_value is not None:
                setattr(self, to_field_name, calc_function(from_field_value))

    # When is this item added in the brewing process? Boil, steep, or mash?
    @property
    def addition(self):
        if self.kind_raw is None:
            return self.MASH

        regexes = [
            # Forced values take precedence, then search known names and default to mashing
            (re.compile("/mash/i"), self.MASH),
            (re.compile("/steep/i"), self.STEEP),
            (re.compile("/boil/i"), self.BOIL),
            (re.compile("/boil/i"), self.BOIL),
            (re.compile("/biscuit|black|cara|chocolate|crystal|munich|roast|special|toast|victory|vienna/i"), self.STEEP),
            (re.compile("/candi|candy|dme|dry|extract|honey|lme|liquid|sugar|syrup|turbinado/i"), self.BOIL),
        ]

        kind_raw_lower = self.kind_raw.lower()
        for regex, addition in regexes:
            if re.search(regex, kind_raw_lower):
                return addition

        return self.MASH

    # Efficiency based on addition
    @property
    def extract_efficiency(self):
        if self.addition == self.STEEP:
            return 0.5
        elif self.addition == self.MASH:
            return 0.75
        return 1.0

    # Get the gravity units for a specific liquid volume with 100% efficiency
    def gu(self, cast_out_wort: float):
        if self._yield is None or self.amount is None:
            return None

        ppg = yield_to_ppg(self._yield)
        amount_lbs = kg_to_lbs(self.amount / 1000)
        gallons = liters_to_gallons(cast_out_wort)
        return ppg * amount_lbs / gallons


class RecipeHop(models.Model):
    MASH = 'mash'
    FIRST_WORT = 'first_wort'
    BOIL = 'boil'
    AROMA = 'aroma'
    DRY_HOP = 'dry_hop'

    BITTERING = 'bittering'
    DUAL_PURPOSE = 'dual-purpose'

    PELLET = 'pellet'
    PLUG = 'plug'
    LEAF = 'leaf'
    EXTRACT = 'extract'

    USE_CHOICES = (
        (MASH, 'Mash'),
        (FIRST_WORT, 'First Wort'),
        (BOIL, 'Boil'),
        (AROMA, 'Aroma'),
        (DRY_HOP, 'Dry Hop'),
    )

    TYPE_CHOICES = (
        (AROMA, 'Aroma'),
        (BITTERING, 'Bittering'),
        (DUAL_PURPOSE, 'Dual-Purpose'),
    )

    FORM_CHOICES = (
        (PELLET, 'Pellet'),
        (PLUG, 'Plug'),
        (LEAF, 'Leaf'),
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.ForeignKey(Hop, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    form = models.CharField(max_length=16, choices=FORM_CHOICES, default=None, blank=True, null=True)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=None, blank=True, null=True)
    use = models.CharField(max_length=16, choices=USE_CHOICES, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    time = models.IntegerField(default=None, blank=True, null=True, validators=[MinValueValidator(0)])

    alpha = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    beta = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    hsi = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    humulene = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    caryophyllene = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    cohumulone = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    myrcene = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    substitutes = models.CharField(max_length=255, default=None, blank=True, null=True)
    used_for = models.CharField(max_length=255, default=None, blank=True, null=True)
    aroma = models.CharField(max_length=255, default=None, blank=True, null=True)
    notes = models.TextField(default=None, blank=True, null=True)

    @classmethod
    def get_uses(cls) -> dict:
        return OrderedDict(cls.USE_CHOICES)

    # https://realbeer.com/hops/research.html
    def ibu_tinseth(self, og_wort: float, batch_size: float) -> float:
        if self.use == self.DRY_HOP:
            return 0.0  # Dry hop doesn't affect IBU
        if self.alpha is None or self.amount is None or self.time is None:
            return 0.0

        return 1.65 * math.pow(0.000125, og_wort - 1.0) * ((1 - math.pow(math.e, -0.04 * self.time)) / 4.15) * (
                (self.alpha / 100.0 * self.amount * 1000) / batch_size) * self.utilization_factor()

    def utilization_factor(self) -> float:
        """Account for better utilization from pellets vs. whole"""
        return 1.15 if self.form == self.PELLET else 1.0


class RecipeYeast(models.Model):
    ALE = "ale"
    LAGER = "lager"
    WHEAT = "wheat"
    WINE = "wine"
    CHAMPAGNE = "champagne"

    LIQUID = "liquid"
    DRY = "dry"
    SLANT = "slant"
    CULTURE = "culture"

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very-high"

    FORM_CHOICES = (
        (LIQUID, "Liquid"),
        (DRY, "Dry"),
        (SLANT, "Slant"),
        (CULTURE, "Culture"),
    )

    TYPE_CHOICES = (
        (ALE, "Ale"),
        (LAGER, "Lager"),
        (WHEAT, "Wheat"),
        (WINE, "Wine"),
        (CHAMPAGNE, "Champagne"),
    )

    FLOCCULATION_CHOICES = (
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
        (VERY_HIGH, "Very High"),
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.ForeignKey(Yeast, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    lab = models.CharField(max_length=255, default=None, blank=True, null=True)
    product_id = models.CharField(max_length=32, default=None, blank=True, null=True)
    form = models.CharField(max_length=16, choices=FORM_CHOICES, default=None, blank=True, null=True)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    amount_is_weight: models.BooleanField(default=None, blank=True, null=True)
    min_attenuation = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    max_attenuation = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    min_temperature = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    max_temperature = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    flocculation = models.CharField(max_length=16, choices=FLOCCULATION_CHOICES, default=None, blank=True, null=True)
    best_for = models.CharField(max_length=255, default=None, blank=True, null=True)
    notes = models.TextField(default=None, blank=True, null=True)

    @property
    def attenuation(self) -> Optional[float]:
        attenuations = []
        if self.min_attenuation is not None:
            attenuations.append(self.min_attenuation)
        if self.max_attenuation is not None:
            attenuations.append(self.max_attenuation)

        if len(attenuations) > 0:
            return np.mean(attenuations)

        return None
