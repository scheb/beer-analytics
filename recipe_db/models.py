from __future__ import annotations

import codecs
import datetime
import re
# noinspection PyUnresolvedReferences
from typing import Optional

from django.core.validators import MaxValueValidator, BaseValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from recipe_db.formulas import ebc_to_srm, srm_to_ebc, plato_to_gravity, gravity_to_plato, abv_to_to_final_plato, \
    alcohol_by_volume


class GreaterThanValueValidator(BaseValidator):
    message = _('Ensure this value is greater than %(limit_value)s (it is %(show_value)s).')
    code = 'greater_min_value'

    def compare(self, a, b):
        return a <= b


def get_tomorrow_date():
    return datetime.date.today() + datetime.timedelta(days=1)


def create_human_readable_id(value: str) -> str:
    value = codecs.encode(value, 'translit/long')
    return re.sub('[\\s-]+', '-', re.sub('[^\\w\\s-]', '', value)).lower()


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
    def url(self):
        if self.is_category:
            return reverse('style_category', kwargs={'category_slug': self.slug})
        else:
            return reverse('style_detail', kwargs={'category_slug': self.category.slug, 'slug': self.slug})

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


class Fermentable(models.Model):
    # Categories
    GRAIN = "grain"
    SUGAR = "sugar"
    FRUIT = "fruit"
    EXTRACT = "extract"

    # Types
    BARLEY = "barley"
    WHEAT = "wheat"
    OTHER_GRAIN = "other_grain"
    CARA_CRYSTAL = "cara_crystal"
    ROASTED = "roasted"
    SPECIAL = "special"
    UNMALTED_ADJUNCT = "unmalted_adjunct"

    CATEGORY_CHOICES = (
        (GRAIN, "Grain"),
        (SUGAR, "Sugar"),
        (FRUIT, "Fruit"),
        (EXTRACT, "Malt Extract"),
    )

    TYPE_CHOICES = (
        (BARLEY, "Barley"),
        (WHEAT, "Wheat"),
        (CARA_CRYSTAL, "Caramel/Crystal Malt"),
        (ROASTED, "Roasted"),
        (SPECIAL, "Special"),
        (OTHER_GRAIN, "Other Grains"),
        (UNMALTED_ADJUNCT, "Unmalted Adjunct"),
    )

    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default=None, blank=True, null=True)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=None, blank=True, null=True)
    alt_names = models.CharField(max_length=255, default=None, blank=True, null=True)
    alt_names_extra = models.CharField(max_length=255, default=None, blank=True, null=True)

    # Calculated metrics from recipes
    recipes_count = models.IntegerField(default=None, blank=True, null=True)
    recipes_amount_percent_min = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_max = models.FloatField(default=None, blank=True, null=True)

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
    def url(self) -> str:
        return reverse('fermentable_detail', kwargs={'category': self.category, 'slug': self.id})


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
    recipes_alpha_min = models.FloatField(default=None, blank=True, null=True)
    recipes_alpha_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_alpha_max = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_min = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_mean = models.FloatField(default=None, blank=True, null=True)
    recipes_amount_percent_max = models.FloatField(default=None, blank=True, null=True)

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
    def url(self) -> str:
        return reverse('hop_detail', kwargs={'category': self.use, 'slug': self.id})


class Yeast(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)

    def save(self, *args, **kwargs) -> None:
        if self.id == '':
            self.id = self.create_id(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def create_id(cls, name: str) -> str:
        return create_human_readable_id(name)


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
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.ForeignKey(Fermentable, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])


class RecipeHop(models.Model):
    MASH = 'mash'
    FIRST_WORT = 'first_wort'
    BOIL = 'boil'
    AROMA = 'aroma'
    DRY_HOP = 'dry_hop'

    USE_CHOICES = (
        (MASH, 'Mash'),
        (FIRST_WORT, 'First Wort'),
        (BOIL, 'Boil'),
        (AROMA, 'Aroma'),
        (DRY_HOP, 'Dry Hop'),
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.ForeignKey(Hop, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    use = models.CharField(max_length=16, default=None, blank=True, null=True, choices=USE_CHOICES)
    alpha = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    time = models.IntegerField(default=None, blank=True, null=True, validators=[MinValueValidator(0)])


class RecipeYeast(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.CharField(max_length=255, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
